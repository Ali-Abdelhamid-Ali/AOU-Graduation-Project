"""Typed application settings."""

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized environment settings."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ── App ─────────────────────────────────────────────────────────────
    APP_NAME:    str
    APP_VERSION: str

    # ── Cloud LLM providers ──────────────────────────────────────────────
    COHERE_API_KEY:  str
    OPENAI_API_KEY:  str = None
    OPENAI_API_URL:  str = None

    # ── Generation / embedding config ───────────────────────────────────
    GENERATION_BACKEND:   str
    GENERATION_MODEL_ID:  str = None
    EMBEDDING_BACKEND:    str
    EMBEDDING_MODEL_ID:   str = None
    EMBEDDING_MODEL_SIZE: int = None

    INPUT_DEFAULT_MAX_CHARACTERS: int   = None
    INPUT_DEFAULT_MAX_TOKENS:     int   = None
    INPUT_DEFAULT_TEMPERATURE:    float = None

    # ── Local model paths ────────────────────────────────────────────────
    # MedMO-8B-Next  (Qwen3-VL multimodal)

    PHI_QA_MODEL_PATH:str="D:/AOU-Graduation-Project/BioIntellect/AI/fintune/fintuned_QA_model/phi_medical_full_merged_16bit_QA"
    MEDMO_OFFLOAD_FOLDER:str="D:\AOU-Graduation-Project\BioIntellect\AI\fintune\medmo_8B\offload"

    # Fine-tuned Phi medical QA

    PHI_QA_MODEL_PATH:str="D:/AOU-Graduation-Project/BioIntellect/AI/fintune/fintuned_QA_model/phi_medical_full_merged_16bit_QA"
    # ── File handling ────────────────────────────────────────────────────
    FILE_MAX_SIZE:          int
    FILE_ALLOWED_type:      list
    FILE_DEFAULT_CHUNK_SIZE: int

    # ── Runtime ──────────────────────────────────────────────────────────
    environment: str  = Field(default="development", alias="ENVIRONMENT")
    debug:        bool = Field(default=False,          alias="DEBUG")
    log_level:    str  = Field(default="INFO",         alias="LOG_LEVEL")

    # ── Supabase ─────────────────────────────────────────────────────────
    supabase_url:              str = Field(default="", alias="SUPABASE_URL")
    supabase_anon_key:         str = Field(default="", alias="SUPABASE_ANON_KEY")
    supabase_service_role_key: str = Field(default="", alias="SUPABASE_SERVICE_ROLE_KEY")

    # ── MRI segmentation service ─────────────────────────────────────────
    mri_segmentation_service_url: str = Field(
        default="http://127.0.0.1:7860", alias="MRI_SEGMENTATION_SERVICE_URL"
    )
    mri_segmentation_timeout_seconds: int = Field(
        default=300, alias="MRI_SEGMENTATION_TIMEOUT_SECONDS"
    )

    # ── CORS / trusted hosts ─────────────────────────────────────────────
    cors_origins:  str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")
    trusted_hosts: str = Field(default="localhost,127.0.0.1",   alias="TRUSTED_HOSTS")

    # ── Validators ───────────────────────────────────────────────────────
    @field_validator("debug", mode="before")
    @classmethod
    def _normalize_debug(cls, value):
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        normalized = str(value).strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
        return False

    # ── Properties ───────────────────────────────────────────────────────
    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def trusted_host_list(self) -> List[str]:
        return [h.strip() for h in self.trusted_hosts.split(",") if h.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()


settings = get_settings()