"""Application configuration using pydantic-settings."""
from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from pathlib import Path

# Load .env from backend directory
ENV_PATH = Path(__file__).parent.parent / ".env"

class Settings(BaseSettings):
    """Application settings."""
    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    
    # LLM
    cohere_api_key: str = ""
    
    # App
    app_env: str = "production"
    debug: bool = False
    api_prefix: str = "/api"
    
    class Config:
        env_file = str(ENV_PATH)
        env_file_encoding = "utf-8"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

settings = get_settings()
