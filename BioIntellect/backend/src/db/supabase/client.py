from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from supabase import AsyncClient, AsyncClientOptions, create_async_client


_BACKEND_ROOT = Path(__file__).resolve().parents[3]
_ENV_PATH = _BACKEND_ROOT / ".env"
if _ENV_PATH.exists():
    load_dotenv(_ENV_PATH, override=False)


class SupabaseProvider:
    _instance_anon: Optional[AsyncClient] = None
    _instance_admin: Optional[AsyncClient] = None

    @staticmethod
    def _require_env(name: str) -> str:
        from os import getenv

        value = (getenv(name) or "").strip()
        if not value:
            raise ValueError(f"Missing required environment variable: {name}")
        return value

    @classmethod
    async def get_client(cls) -> AsyncClient:
        if cls._instance_anon is None:
            url = cls._require_env("SUPABASE_URL")
            anon_key = cls._require_env("SUPABASE_ANON_KEY")
            cls._instance_anon = await create_async_client(
                url,
                anon_key,
                options=AsyncClientOptions(
                    postgrest_client_timeout=60,
                    storage_client_timeout=60,
                ),
            )
        return cls._instance_anon

    @classmethod
    async def get_admin(cls) -> AsyncClient:
        if cls._instance_admin is None:
            url = cls._require_env("SUPABASE_URL")
            service_key = cls._require_env("SUPABASE_SERVICE_ROLE_KEY")
            cls._instance_admin = await create_async_client(
                url,
                service_key,
                options=AsyncClientOptions(
                    postgrest_client_timeout=60,
                    storage_client_timeout=60,
                ),
            )
        return cls._instance_admin

    @classmethod
    async def close_all(cls):
        cls._instance_anon = None
        cls._instance_admin = None
