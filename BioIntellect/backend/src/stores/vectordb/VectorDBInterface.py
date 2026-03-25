from abc import ABC, abstractmethod
from src.validators.Retrieved_dto import RetrievedItem
class VectorDBInterface(ABC):

    @abstractmethod
    def connect(self):
        pass
    @abstractmethod
    def disconnect(self):
        pass
    @abstractmethod
    def is_collection_exists(self, collection_name: str) -> bool:
        pass
    @abstractmethod
    def list_all_collections(self) -> list:
        pass
    @abstractmethod
    def get_collection_info(self, collection_name: str) -> dict:
        pass
    @abstractmethod
    def delete_collection(self, collection_name: str):
        pass
    @abstractmethod
    def create_collection(self, collection_name: str, embedding_size: int, do_reset: bool = False):
        pass
    @abstractmethod
    def insert_one(self, collection_name: str, text:str, vectors: list, metadatas: list, record_id:str|None=None):
        pass
    @abstractmethod
    def insert_many(self, collection_name: str, text:list , vectors: list, metadatas: list, record_id:list|None=None, batch_size: int = 100):
        pass
    @abstractmethod
    def search_py_vector(self, collection_name: str, vector: list, limit: int = 10) -> list[RetrievedItem]:
        pass