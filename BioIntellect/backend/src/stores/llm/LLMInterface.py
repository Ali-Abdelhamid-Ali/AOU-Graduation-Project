from abc import ABC, abstractmethod


class LLMInterface(ABC):

    @abstractmethod
    def set_generation_model(self, model_id: str) -> str:
        pass

    @abstractmethod
    def set_embedding_model(self, model_id: str, embedding_size:int) -> str:
        pass

    @abstractmethod
    def generate_text(self, prompt: str,chat_history:list=None,max_output_tokens:int = None,
                           temp:float = None) -> str:
        pass

    @abstractmethod
    def embed_text(self, text: str, document_type: str = None) -> list[float]:
        pass

    @abstractmethod
    def construct_prompt(self, query: str, role:str) -> dict:
        pass