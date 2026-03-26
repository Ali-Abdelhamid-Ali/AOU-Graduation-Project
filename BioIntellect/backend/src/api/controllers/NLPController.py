from src.api.controllers.BaseController import BaseController
from src.stores.llm.LLMEnums import DocumentTypeEnums


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
    def get_vector_db_collection_info(self, project_id: str) -> dict:
        collection_name = self.create_collection_name(project_id=project_id)
        if self.vectorDB_client.is_collection_exists(collection_name):
            collection_info = self.vectorDB_client.get_collection_info(collection_name=collection_name)
            return collection_info
        return None

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
    def search_vector_db_collection(self, project_id: str, text: str, limit: int = 10) -> list:
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
        results = self.vectorDB_client.search_py_vector(collection_name=collection_name, vector=vector, limit=limit)
        if not results:
            raise ValueError("No results returned from vector database search")
        return results
    def answer_rag_question(self, project_id: str, question: str, limit: int, chat_history: list = None, language: str = "en") -> tuple:
        retrieved_documents = self.search_vector_db_collection(project_id=project_id, text=question, limit=limit)
        if not retrieved_documents or len(retrieved_documents) == 0:
            raise ValueError("No relevant documents found in vector database for the given question")
        if self.generation_client is None:
            raise ValueError("Generation client is not initialized")

        if chat_history is None:
            chat_history = []

        self.template_parser.set_language(language)

        system_prompt = self.template_parser.get("rag", "system_prompt", vars={})

        document_prompts = "\n".join([
            self.template_parser.get("rag", "document_prompt", vars={
                "doc_no": idx + 1,
                "doc_content": doc.text
            })
            for idx, doc in enumerate(retrieved_documents)
        ])

        footer_prompt = self.template_parser.get("rag", "footer_prompt", vars={})
        question_label = "Question" if language != "ar" else "السؤال"
        answer_label = "Answer" if language != "ar" else "الإجابة"
        full_prompt = f"{document_prompts}\n{footer_prompt}\n{question_label}: {question}\n{answer_label}:"

        clean_history = [
            msg for msg in chat_history
            if isinstance(msg, dict) and str(msg.get("role", "")).capitalize() != "System"
        ][-100:]

        model_history = [{"role": "System", "message": system_prompt}, *clean_history]

        answer = self.generation_client.generate_text(
            prompt=full_prompt,
            chat_history=model_history,
            max_output_tokens=500
        )
        if not answer:
            raise ValueError("Failed to generate answer from generation client")

        chat_history.append(
            self.generation_client.construct_prompt(
                query=question,
                role=self.generation_client.Enums.user.value,
            )
        )
        chat_history.append(
            self.generation_client.construct_prompt(
                query=answer.strip(),

                role=self.generation_client.Enums.assistant.value,
            )
        )

        return answer.strip(), full_prompt.strip(), chat_history
    