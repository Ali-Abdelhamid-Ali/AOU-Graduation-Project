from ..LLMInterface import LLMInterface
from ..LLMEnums import OpenAIEnums
from openai import OpenAI
from src.observability.logger import get_logger


class OpenAIProvider(LLMInterface):

    def __init__(self, api_key: str,base_url:str = None
                ,default_input_max_characters:int = 1000, 
                default_output_max_tokens:int = 1000,
                default_temp:float = 0.1):
        self.api_key = api_key
        self.base_url = base_url
        self.default_input_max_characters = default_input_max_characters
        self.default_output_max_tokens = default_output_max_tokens
        self.default_temp = default_temp
        self.generation_model_id = None
        self.embedding_model_id = None
        self.embedding_size = None
        self.logger = get_logger("provider.OpenAIProvider")
        self.Enums = OpenAIEnums
        self.client = OpenAI(api_key=self.api_key, 
                             base_url=self.base_url)

    def set_generation_model(self, model_id: str ) -> str:
        self.generation_model_id = model_id

        return self.generation_model_id

    def set_embedding_model(self, model_id: str, embedding_size:int) -> str:
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size
        return self.embedding_model_id

    def generate_text(self, prompt: str,chat_history:list=None,max_output_tokens:int=None ,
                           temp:float = None) -> str:
        if not self.client:
            self.logger.error("OpenAI client is not initialized.")
            return None
        if not self.generation_model_id:
            self.logger.error("Generation model is not set.")
            return None
        if chat_history is None:
            chat_history = []

        # Normalize chat history to OpenAI format {role, content}
        normalized: list[dict] = []
        for msg in chat_history:
            if not isinstance(msg, dict) or "role" not in msg:
                continue
            role = str(msg["role"]).lower()
            content = msg.get("content") or msg.get("message") or ""
            if role in ("chatbot",):
                role = "assistant"
            normalized.append({"role": role, "content": str(content)})

        normalized.append(self.construct_prompt(query=prompt, role=OpenAIEnums.user.value))
        response = self.client.chat.completions.create(
            model=self.generation_model_id,
            messages=normalized,
            max_tokens=max_output_tokens or self.default_output_max_tokens,
            temperature=temp if temp is not None else self.default_temp,
            timeout=30.0,
        )


        if not response or not response.choices or len(response.choices) == 0 or not response.choices[0].message or not response.choices[0].message.content:
            self.logger.error("No choices returned from OpenAI.")
            return None
        return response.choices[0].message.content
    def process_text(self, text: str) -> str:

        # This method can be implemented to perform any necessary preprocessing on the input text
        # For example, you could add special tokens, truncate the text, or perform other transformations
        return text[:self.default_input_max_characters].strip()





    def embed_text(self, text: str, document_type: str = None) -> list[float]:
        if not self.client:
            self.logger.error("OpenAI client is not initialized.")
            return None
        if not self.embedding_model_id:
            self.logger.error("Embedding model is not set.")
            return None


        response = self.client.embeddings.create(
            input=text,
            model=self.embedding_model_id,
            timeout=30.0,
        )


        if not response or not response.data or len(response.data) == 0 or not response.data[0].embedding:
            self.logger.error("No embedding data returned from OpenAI.")
            return None
        
        return response.data[0].embedding

    def construct_prompt(self, query: str, role: str) -> dict:
        # This method can be customized based on specific prompt construction needs
        return {
            "role": role,   # e.g. "user", "assistant", "system"
            "content": self.process_text(query),
        }