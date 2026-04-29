from abc import ABC, abstractmethod
from typing import Optional


class LLMInterface(ABC):

    @abstractmethod
    def set_generation_model(self, model_id: str) -> str:
        pass

    @abstractmethod
    def set_embedding_model(self, model_id: str, embedding_size:int) -> str:
        pass

    @abstractmethod
    def generate_text(self, prompt: str, chat_history: Optional[list] = None, max_output_tokens: Optional[int] = None,
                           temp: Optional[float] = None) -> Optional[str]:
        pass

    @abstractmethod
    def embed_text(self, text: "str | list[str]", document_type: Optional[str] = None) -> "Optional[list]":
        """Embed text.

        Accepts a single string or a list of strings.
        Returns a single vector (list[float]) for str input, or a list of
        vectors (list[list[float]]) for list input.
        """
        pass

    @abstractmethod
    def construct_prompt(self, query: str, role:str) -> dict:
        pass