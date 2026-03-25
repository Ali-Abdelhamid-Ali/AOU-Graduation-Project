import cohere

from src.observability.logger import get_logger

from ..LLMEnums import CohereEnums, DocumentTypeEnums
from ..LLMInterface import LLMInterface


class CoHereProvider(LLMInterface):
    def __init__(self, api_key: str
                ,default_input_max_characters:int = 1000,
                default_output_max_tokens:int = 1000,
                default_temp:float = 0.1):
        self.api_key = api_key
        self.default_input_max_characters = default_input_max_characters
        self.default_output_max_tokens = default_output_max_tokens
        self.default_temp = default_temp
        self.generation_model_id = None
        self.embedding_model_id = None
        self.embedding_size = None
        self.logger = get_logger("provider.CohereProvider")
        self.Enums = CohereEnums
        self.client = cohere.Client(api_key=self.api_key)

    def set_generation_model(self, model_id: str ) -> str:
        self.generation_model_id = model_id
        return self.generation_model_id

    def set_embedding_model(self, model_id: str, embedding_size:int) -> str:
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size
        return self.embedding_model_id

    def process_text(self, text: str) -> str:
        return text[:self.default_input_max_characters].strip()

    def generate_text(self, prompt: str, chat_history: list = None, max_output_tokens: int = None,
                    temp: float = None) -> str:
        if not self.client:
            self.logger.error("Cohere client is not initialized.")
            return None
        if not self.generation_model_id:
            self.logger.error("Generation model is not set.")
            return None

        if chat_history is None:
            chat_history = []

        preamble = None
        sanitized_history = []

        for msg in chat_history:
            if not isinstance(msg, dict) or "role" not in msg:
                self.logger.warning(f"Skipping malformed chat_history entry: {msg}")
                continue

            role_str = str(msg["role"]).capitalize()
            if role_str == "Assistant":
                role_str = "Chatbot"

            if role_str == "System":          
                preamble = msg.get("message", "")
            else:
                sanitized_history.append({
                    "role": role_str,
                    "message": msg.get("message", "")
                })

        response = self.client.chat(
            model=self.generation_model_id,
            message=prompt,
            chat_history=sanitized_history,  
            preamble=preamble,                
            max_tokens=max_output_tokens or self.default_output_max_tokens,
            temperature=temp if temp is not None else self.default_temp,
        )

        if not response or not response.text:
            self.logger.error("No response returned from Cohere.")
            return None

        return response.text

    def embed_text(self, text: str | list[str], document_type: str = None):
        if not self.client:
            self.logger.error("Cohere client is not initialized.")
            return None
        if not self.embedding_model_id:
            self.logger.error("Embedding model is not set.")
            return None

        input_type=CohereEnums.document.value if document_type==DocumentTypeEnums.document.value else CohereEnums.query.value
        texts = [self.process_text(item) for item in text] if isinstance(text, list) else [self.process_text(text)]
        response = self.client.embed(
            texts=texts,
            model=self.embedding_model_id,
            input_type=input_type,
            embedding_types=["float"]
        )

        if not response or not response.embeddings or not response.embeddings.float:
            self.logger.error("No embedding returned from Cohere.")
            return None
        if isinstance(text, list):
            return response.embeddings.float
        return response.embeddings.float[0]

    def construct_prompt(self, query: str, role: str) -> dict:
        return {
                "role": role,
                "message": query,
            }
