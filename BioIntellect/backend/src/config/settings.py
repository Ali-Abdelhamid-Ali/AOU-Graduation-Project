from functools import lru_cache
import os
from typing import List, Optional

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ── App ──────────────────────────────────────────────────────────────
    APP_NAME:    str
    APP_VERSION: str

    # ── Cloud LLM providers ──────────────────────────────────────────────
    COHERE_API_KEY:  Optional[str] = None
    OPENAI_API_KEY:  Optional[str] = None
    OPENAI_API_URL:  Optional[str] = None

    # ── Generation / embedding config ────────────────────────────────────
    GENERATION_BACKEND:   str
    GENERATION_MODEL_ID:  Optional[str] = None
    EMBEDDING_BACKEND:    Optional[str] = None
    EMBEDDING_MODEL_ID:   Optional[str] = None
    EMBEDDING_MODEL_SIZE: Optional[int] = None

    INPUT_DEFAULT_MAX_CHARACTERS: Optional[int]   = None
    INPUT_DEFAULT_MAX_TOKENS:     Optional[int]   = None
    INPUT_DEFAULT_TEMPERATURE:    Optional[float] = None

    # ── Local model paths ────────────────────────────────────────────────
    MEDMO_MODEL_PATH:     Optional[str] = None
    MEDMO_OFFLOAD_FOLDER: str           = "./offload"
    PHI_QA_MODEL_PATH:    Optional[str] = None

    # ── File handling ────────────────────────────────────────────────────
    FILE_MAX_SIZE:           int
    FILE_ALLOWED_TYPE:       list
    FILE_DEFAULT_CHUNK_SIZE: int

    # ── Runtime ──────────────────────────────────────────────────────────
    environment: str  = Field(default="development", alias="ENVIRONMENT")
    debug:       bool = Field(default=False,          alias="DEBUG")
    log_level:   str  = Field(default="INFO",         alias="LOG_LEVEL")

    # ── Supabase ─────────────────────────────────────────────────────────
    supabase_url:              str = Field(default="", alias="SUPABASE_URL")
    supabase_anon_key:         str = Field(default="", alias="SUPABASE_ANON_KEY")
    supabase_service_role_key: str = Field(default="", alias="SUPABASE_SERVICE_ROLE_KEY")

    # ── MRI segmentation service ──────────────────────────────────────────
    mri_segmentation_service_url: str = Field(
        default="http://127.0.0.1:7860", alias="MRI_SEGMENTATION_SERVICE_URL"
    )
    mri_segmentation_timeout_seconds: int = Field(
        default=300, alias="MRI_SEGMENTATION_TIMEOUT_SECONDS"
    )

    # ── CORS / trusted hosts ──────────────────────────────────────────────
    cors_origins:  str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")
    trusted_hosts: str = Field(default="localhost,127.0.0.1",   alias="TRUSTED_HOSTS")

    # ── Validators ────────────────────────────────────────────────────────
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

    @model_validator(mode="after")
    def _validate_llm_configuration(self):
        supported_backends = {"cohere", "openai", "medmo", "phi_qa"}

        def _normalize_existing_dir(value: Optional[str], env_name: str) -> str:
            resolved = os.path.abspath(
                os.path.expanduser(os.path.expandvars((value or "").strip()))
            )
            if not resolved or not os.path.isdir(resolved):
                raise ValueError(
                    f"{env_name} must point to an existing directory. Resolved path: '{resolved or value}'."
                )
            return resolved

        generation_backend = (self.GENERATION_BACKEND or "").strip().lower()
        if generation_backend not in supported_backends:
            raise ValueError(
                "GENERATION_BACKEND must be one of: cohere, openai, medmo, phi_qa"
            )
        self.GENERATION_BACKEND = generation_backend

        if self.EMBEDDING_BACKEND:
            embedding_backend = (self.EMBEDDING_BACKEND or "").strip().lower()
        elif self.GENERATION_BACKEND == "medmo":
            raise ValueError(
                "EMBEDDING_BACKEND must be set when GENERATION_BACKEND=medmo because medmo does not support embed_text. "
                "Choose one of: phi_qa, openai, cohere."
            )
        else:
            embedding_backend = self.GENERATION_BACKEND

        if embedding_backend not in supported_backends:
            raise ValueError(
                "EMBEDDING_BACKEND must be one of: cohere, openai, medmo, phi_qa"
            )
        self.EMBEDDING_BACKEND = embedding_backend

        if self.GENERATION_BACKEND == "cohere" and not self.COHERE_API_KEY:
            raise ValueError(
                "COHERE_API_KEY is required when GENERATION_BACKEND=cohere"
            )
        if self.GENERATION_BACKEND == "openai" and not self.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY is required when GENERATION_BACKEND=openai"
            )

        if self.GENERATION_BACKEND == "medmo" and not self.MEDMO_MODEL_PATH:
            raise ValueError(
                "MEDMO_MODEL_PATH is required when GENERATION_BACKEND=medmo.\n"
                "Add this to your .env:\n"
                "MEDMO_MODEL_PATH=D:/AOU-Graduation-Project/BioIntellect/AI/fintune/medmo_8B/MedMO-8B-Next"
            )
        if self.GENERATION_BACKEND == "medmo":
            self.MEDMO_MODEL_PATH = _normalize_existing_dir(
                self.MEDMO_MODEL_PATH,
                "MEDMO_MODEL_PATH",
            )

        if self.GENERATION_BACKEND == "phi_qa" and not self.PHI_QA_MODEL_PATH:
            raise ValueError(
                "PHI_QA_MODEL_PATH is required when GENERATION_BACKEND=phi_qa.\n"
                "Add this to your .env:\n"
                "PHI_QA_MODEL_PATH=D:/AOU-Graduation-Project/BioIntellect/AI/fintune/"
                "fintuned_QA_model/phi_medical_full_merged_16bit_QA"
            )
        if self.GENERATION_BACKEND == "phi_qa":
            self.PHI_QA_MODEL_PATH = _normalize_existing_dir(
                self.PHI_QA_MODEL_PATH,
                "PHI_QA_MODEL_PATH",
            )

        if self.EMBEDDING_BACKEND == "cohere":
            if not self.COHERE_API_KEY:
                raise ValueError(
                    "COHERE_API_KEY is required when EMBEDDING_BACKEND=cohere"
                )
            if not self.EMBEDDING_MODEL_ID:
                raise ValueError(
                    "EMBEDDING_MODEL_ID is required when EMBEDDING_BACKEND=cohere"
                )
            if self.EMBEDDING_MODEL_SIZE is None:
                raise ValueError(
                    "EMBEDDING_MODEL_SIZE is required when EMBEDDING_BACKEND=cohere"
                )

        if self.EMBEDDING_BACKEND == "openai":
            if not self.OPENAI_API_KEY:
                raise ValueError(
                    "OPENAI_API_KEY is required when EMBEDDING_BACKEND=openai"
                )
            if not self.EMBEDDING_MODEL_ID:
                raise ValueError(
                    "EMBEDDING_MODEL_ID is required when EMBEDDING_BACKEND=openai"
                )

        if self.EMBEDDING_BACKEND == "medmo":
            raise ValueError(
                "EMBEDDING_BACKEND=medmo is not supported because MedMOProvider does not implement embed_text. "
                "Use EMBEDDING_BACKEND=phi_qa/openai/cohere."
            )

        if self.EMBEDDING_BACKEND == "phi_qa" and not self.PHI_QA_MODEL_PATH:
            raise ValueError(
                "PHI_QA_MODEL_PATH is required when EMBEDDING_BACKEND=phi_qa"
            )
        if self.EMBEDDING_BACKEND == "phi_qa":
            self.PHI_QA_MODEL_PATH = _normalize_existing_dir(
                self.PHI_QA_MODEL_PATH,
                "PHI_QA_MODEL_PATH",
            )

        return self

    # ── Properties ────────────────────────────────────────────────────────
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