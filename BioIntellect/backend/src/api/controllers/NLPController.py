import inspect
from typing import Any, Optional

from src.api.controllers.BaseController import BaseController
from src.stores.llm.LLMEnums import DocumentTypeEnums
from src.config.settings import get_settings


class NLPController(BaseController):
    def __init__(self,vectorDB_client, generation_client, embedding_client,template_parser=None):
        super().__init__()
        self.vectorDB_client = vectorDB_client
        self.generation_client = generation_client
        self.embedding_client = embedding_client
        self.template_parser = template_parser

    def create_collection_name(self, project_id: str) -> str:
        return f"project_{project_id}".strip()
    def reset_vector_db_collection(self, project_id: str):
        collection_name = self.create_collection_name(project_id=project_id)
        if self.vectorDB_client.is_collection_exists(collection_name):
            return self.vectorDB_client.delete_collection(collection_name)
    def get_vector_db_collection_info(self, project_id: str) -> Any:
        collection_name = self.create_collection_name(project_id=project_id)
        if self.vectorDB_client.is_collection_exists(collection_name):
            collection_info = self.vectorDB_client.get_collection_info(collection_name=collection_name)
            return collection_info
        return {}

    def index_into_vector_db(self, project_id: str, texts:list, vectors:list, metadata: list, record_id: list|None=None, do_reset: bool = False):
        collection_name = self.create_collection_name(project_id=project_id)
        if do_reset:
            self.reset_vector_db_collection(project_id=project_id)
        if not self.vectorDB_client.is_collection_exists(collection_name):
            embedding_size = getattr(self.embedding_client, "embedding_size", None)
            if embedding_size is None and vectors and len(vectors) > 0:
                embedding_size = len(vectors[0])
            if embedding_size is None:
                raise ValueError("Unable to determine embedding size for collection creation")
            _ = self.vectorDB_client.create_collection(collection_name=collection_name, embedding_size=embedding_size, do_reset=do_reset)
        inserted = self.vectorDB_client.insert_many(
            collection_name=collection_name,
            text=texts,
            vectors=vectors,
            metadatas=metadata,
            record_id=record_id,
        )
        if not inserted:
            raise ValueError("Failed to insert vectors into vector database")
        return True
    def search_vector_db_collection(self, project_id: str, text: str, limit: int = 10, filter_file_ids: list[str] | None = None) -> list:
        collection_name = self.create_collection_name(project_id=project_id)
        if not self.vectorDB_client.is_collection_exists(collection_name):
            raise ValueError(f"Vector database collection for project {project_id} does not exist")
        if self.embedding_client is None:
            raise ValueError("Embedding client is not initialized")
        vector = self.embedding_client.embed_text(
            text=text,
            document_type=DocumentTypeEnums.query.value,
        )
        if not vector or len(vector) == 0:
            raise ValueError("Failed to generate embedding for search query")

        active_filter = filter_file_ids if filter_file_ids else None

        # When specific file IDs are requested, use a higher limit so that even
        # low-scoring chunks from those files are surfaced before we fall back.
        search_limit = max(limit * 3, 10) if active_filter else limit

        results = self.vectorDB_client.search_py_vector(
            collection_name=collection_name,
            vector=vector,
            limit=search_limit,
            filter_file_ids=active_filter,
        )

        # If the filtered search returned nothing, fall back to an unfiltered
        # search so the model still gets relevant context from other documents.
        if not results and active_filter:
            results = self.vectorDB_client.search_py_vector(
                collection_name=collection_name,
                vector=vector,
                limit=limit,
                filter_file_ids=None,
            )

        return results or []

    def answer_rag_question(
        self,
        project_id: str,
        question: str,
        limit: int,
        chat_history = None,
        language: str = "en",
        image_path: str | None = None,
        filter_file_ids: list[str] | None = None,
    ) -> tuple:
        try:
            retrieved_documents = self.search_vector_db_collection(
                project_id=project_id,
                text=question,
                limit=limit,
                filter_file_ids=filter_file_ids if filter_file_ids else None,
            )
        except ValueError:
            retrieved_documents = []

        if self.generation_client is None:
            raise ValueError("Generation client is not initialized")

        if chat_history is None:
            chat_history = []

        self.template_parser.set_language(language)
        system_prompt = self.template_parser.get("rag", "system_prompt", vars={})

        # Build per-document prompt blocks WITH source name so the model can
        # cite. We also return a parallel `sources` list for the UI.
        sources: list[dict] = []
        if retrieved_documents:
            doc_blocks: list[str] = []
            for idx, doc in enumerate(retrieved_documents):
                meta = getattr(doc, "metadata", None) or {}
                file_name = (
                    getattr(doc, "file_name", None)
                    or meta.get("file_name")
                    or meta.get("source")
                    or "unknown_source"
                )
                source_file_id = (
                    getattr(doc, "source_file_id", None)
                    or meta.get("source_file_id")
                )
                chunk_index = meta.get("chunk_index")
                page = meta.get("page")
                doc_no = idx + 1
                header_bits = [f"Document {doc_no}", f"source: {file_name}"]
                if chunk_index is not None:
                    header_bits.append(f"chunk: {chunk_index}")
                if page is not None:
                    header_bits.append(f"page: {page}")
                header = " | ".join(header_bits)
                doc_blocks.append(f"## {header}\n{doc.text}")
                sources.append({
                    "doc_no": doc_no,
                    "file_name": file_name,
                    "source_file_id": source_file_id,
                    "chunk_index": chunk_index,
                    "page": page,
                    "score": float(getattr(doc, "score", 0.0) or 0.0),
                    "preview": (doc.text or "")[:240],
                })
            document_prompts = "\n\n".join(doc_blocks)
            citation_instruction = (
                "When you answer, cite the supporting documents inline using the "
                "format [source: <file_name>]. At the end of your answer, add a "
                "'Sources' section listing the distinct file names you relied on."
            )
        else:
            document_prompts = (
                "No indexed documents were found for this project and question. "
                "Answer based on your general medical knowledge, and clearly "
                "indicate uncertainty when applicable. Clearly state that this "
                "answer is based on general knowledge and not from the patient's "
                "uploaded documents."
            )
            citation_instruction = ""

        footer_prompt = self.template_parser.get("rag", "footer_prompt", vars={})
        question_label = "Question" if language != "ar" else "السؤال"
        answer_label = "Answer" if language != "ar" else "الإجابة"
        full_prompt = (
            f"{document_prompts}\n"
            f"{citation_instruction}\n"
            f"{footer_prompt}\n"
            f"{question_label}: {question}\n{answer_label}:"
        )

        settings = get_settings()
        history_limit = settings.CHAT_HISTORY_MAX_MESSAGES
        max_tokens = settings.CHAT_MAX_OUTPUT_TOKENS

        clean_history = [
            msg for msg in chat_history
            if isinstance(msg, dict) and str(msg.get("role", "")).capitalize() != "System"
        ][-history_limit:]
        model_history = [{"role": "System", "message": system_prompt}, *clean_history]

        generate_kwargs = {
            "prompt": full_prompt,
            "chat_history": model_history,
            "max_output_tokens": max_tokens,
        }
        if image_path and "image_path" in inspect.signature(self.generation_client.generate_text).parameters:
            generate_kwargs["image_path"] = image_path

        answer = self.generation_client.generate_text(**generate_kwargs)
        answer = answer.strip() if isinstance(answer, str) else ""
        if not answer:
            answer = (
                "I couldn't generate a model response for this request right now. "
                "Please try another model or check the local model configuration."
            )

        chat_history.append(
            self.generation_client.construct_prompt(
                query=question,
                role=self.generation_client.Enums.user.value,
            )
        )
        chat_history.append(
            self.generation_client.construct_prompt(
                query=answer,
                role=self.generation_client.Enums.assistant.value,
            )
        )

        return answer, full_prompt.strip(), chat_history, sources
