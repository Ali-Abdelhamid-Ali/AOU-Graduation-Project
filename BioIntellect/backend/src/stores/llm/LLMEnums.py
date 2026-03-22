from enum import Enum
class LLMEnumes(Enum):
    # LLM Types
    openai = "openai"
    cohere = "cohere"
    medmo   = "medmo"      
    phi_qa  = "phi_qa"
class OpenAIEnums(Enum):
    system= "system"
    user= "user"
    assistant= "assistant"
class CohereEnums(Enum):
    system= "system"
    user= "user"
    assistant= "assistant"
    document="search_Document"
    query="search_query"
class MedMOEnums(Enum):
    system    = "system"
    user      = "user"
    assistant = "assistant"
class PhiQAEnums(Enum):
    system    = "system"
    user      = "user"
    assistant = "assistant"
class DocumentTypeEnums(Enum):
    document = "document"
    query = "query"