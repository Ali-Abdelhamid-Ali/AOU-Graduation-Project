from .VectorDBEnums import VectorDBENUMS
from src.api.controllers.BaseController import BaseController
from src.observability.logger import get_logger


class VectorDBProviderFactory:
    def __init__(self, settings):
        self.settings = settings
        self.base_controller = BaseController()
        self.logger = get_logger("vectordb.factory")
        self.last_error: str | None = None
        self.last_db_path: str | None = None

    def create(self, Provider: str):
        self.last_error = None
        self.last_db_path = None

        if Provider and Provider.upper() == VectorDBENUMS.QDRANT.value:
            db_path = self.base_controller.get_database_path(
                db_name=self.settings.VECTOR_DB_PATH
            )
            self.last_db_path = db_path

            try:
                from .providers.QdrantDBProvider import QdrantDBProvider
            except Exception as exc:
                self.last_error = f"provider import failed: {exc}"
                self.logger.warning(
                    f"Qdrant provider import failed for db_path={db_path}; continuing without vectordb client: {exc}"
                )
                return None
            return QdrantDBProvider(
                db_path=db_path,
                distance_method=self.settings.VECTOR_DB_DISTANCE_METHOD,
            )

        self.last_error = f"unsupported provider: {Provider}"
        return None
    