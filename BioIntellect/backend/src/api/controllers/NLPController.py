from src.api.controllers.BaseController import BaseController


class NLPController(BaseController):
    def __init__(self,vectorDB_client, generation_client, embedding_client):
        super().__init__()
        self.vectorDB_client = vectorDB_client
        self.generation_client = generation_client
        self.embedding_client = embedding_client


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