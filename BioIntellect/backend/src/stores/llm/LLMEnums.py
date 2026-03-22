from enum import Enum


class LLEnumes(Enum):
    """
    Enum class for LLM related constants.
    """
    # LLM Types
    openai = "openai"
    cohere = "cohere"
    ollama = "ollama"
class OpenAIEnums(Enum):
    system= "system"
    user= "user"
    assistant= "assistant"