from .providers import QdrantDBProvider
from .VectorDBEnums import VectorDBENUMS
from src.api.controllers.BaseController import BaseController
class VectorDBProviderFactory:
    def __init__(self, settings):
        self.settings = settings
        self.base_controller = BaseController()
    def create(self, Provider: str):
        if Provider== VectorDBENUMS.QDRANT.value:
            db_path = self.base_controller.get_database_path(db_name=self.settings.VECTOR_DB_PATH)
            return QdrantDBProvider(db_path=db_path, 
            distance_method=self.settings.VECTOR_DB_DISTANCE_METHOD)
        return None 
    