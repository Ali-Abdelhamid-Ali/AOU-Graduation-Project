from uuid import uuid4

from qdrant_client import QdrantClient, models
from src.observability.logger import get_logger

from ..VectorDBEnums import DistanceMethodEnums
from ..VectorDBInterface import VectorDBInterface


class QdrantDBProvider(VectorDBInterface):
    def __init__(self, db_path: str, distance_method: str):
        self.db_path = db_path
        self.distance_method = None
        if distance_method == DistanceMethodEnums.COSINE.value:
            self.distance_method = models.Distance.COSINE
        elif distance_method == DistanceMethodEnums.DOT.value:
            self.distance_method = models.Distance.DOT
        self.client=None
        self.logger = get_logger("vectordb.QdrantDB")

    def connect(self):
        self.client = QdrantClient(path=self.db_path)

    def disconnect(self):
        if self.client:
            self.client.close()

    def is_collection_exists(self, collection_name: str) -> bool:
        return self.client.collection_exists(collection_name)
    
    def list_all_collections(self) -> list:
        return self.client.get_collections().collections
    def get_collection_info(self, collection_name: str) -> dict:
        return self.client.get_collection(collection_name=collection_name).dict()
    def delete_collection(self, collection_name: str):
        if self.is_collection_exists(collection_name):
            return self.client.delete_collection(collection_name=collection_name)
    def create_collection(self, collection_name: str, embedding_size: int, do_reset: bool = False):
        if do_reset and self.is_collection_exists(collection_name):
            self.delete_collection(collection_name)
        if not self.is_collection_exists(collection_name):
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=embedding_size, distance=self.distance_method)
            )
            return True 
        return False
    def insert_one(self, collection_name: str, text:str, vectors: list, metadatas: list, record_id:str|None=None):
        if not self.is_collection_exists(collection_name):
            self.logger.error(f"Collection {collection_name} does not exist.")
            return False
        try:
            rid = record_id if record_id is not None else uuid4().hex
            _ = self.client.upsert(
                collection_name=collection_name,
                points=[
                    models.PointStruct(
                        id=rid,
                        vector=vectors,
                        payload={"text": text, "metadata": metadatas},
                    )
                ],
                wait=True,
            )
        except Exception as e:
            self.logger.error(f"Error inserting record: {e}")
            return False
        return True
    
    def insert_many(self, collection_name: str, text:list , vectors: list, metadatas: list, record_id:list|None=None, batch_size: int = 100):
        if metadatas is None:
            metadatas = [None] * len(text)
        if record_id is None:
            record_id = [uuid4().hex for _ in text]
        else:
            record_id = [rid if rid is not None else uuid4().hex for rid in record_id]
        for i in range (0, len(text), batch_size):

            batch_text = text[i:i + batch_size]
            batch_vectors = vectors[i:i + batch_size]
            batch_metadatas = metadatas[i:i + batch_size]
            batch_record_id = record_id[i:i + batch_size]
            batch_records = [models.PointStruct(id=rid, vector=vec, payload={"text": t, "metadata": m})
                       for rid, vec, t, m in zip(batch_record_id, batch_vectors, batch_text, batch_metadatas, strict=False)]
            try:
                self.client.upsert(collection_name, batch_records, wait=True)
            except Exception as e:
                self.logger.error(f"Error inserting batch: {e}")
                return False
        return True
    
    def search_py_vector(self, collection_name: str, vector: list, limit: int = 3) -> list:
        return self.client.search(collection_name=collection_name, query_vector=vector, limit=limit)
    