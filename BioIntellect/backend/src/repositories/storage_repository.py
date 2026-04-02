"""Storage Repository - Managed Supabase Storage Access."""

import os
from typing import Optional

from src.db.supabase.client import SupabaseProvider
from src.services.infrastructure.retry_utils import (
    async_retry,
    should_retry_http_exception,
)

DEFAULT_STORAGE_BUCKET = "medical-files"


class StorageRepository:
    """
    Handles direct Supabase Storage interactions.
    STRICT RULE: Only handles binary data and paths. Metadata goes to DB repositories.
    """

    def __init__(self, bucket_name: str = DEFAULT_STORAGE_BUCKET):
        self.bucket = bucket_name

    def _resolve_bucket(self, bucket_name: Optional[str] = None) -> str:
        return bucket_name or self.bucket

    async def _get_client(self):
        return await SupabaseProvider.get_admin()

    @async_retry(max_retries=3, retry_if=should_retry_http_exception)
    async def upload_file(
        self,
        path: str,
        content: bytes,
        content_type: str,
        bucket_name: Optional[str] = None,
    ) -> str:
        """Uploads binary content to a specific path."""
        client = await self._get_client()
        bucket = self._resolve_bucket(bucket_name)
        await client.storage.from_(bucket).upload(
            path=path, file=content, file_options={"content-type": content_type}
        )
        return path

    @async_retry(max_retries=3, retry_if=should_retry_http_exception)
    async def get_signed_url(
        self,
        path: str,
        expires_in: int = 3600,
        bucket_name: Optional[str] = None,
    ) -> str:
        """Generates a transient signed URL for secure download."""
        client = await self._get_client()
        bucket = self._resolve_bucket(bucket_name)
        response = await client.storage.from_(bucket).create_signed_url(
            path, expires_in
        )

        if isinstance(response, str):
            return response

        signedURL = (
            response.get("signedURL")
            if isinstance(response, dict)
            else getattr(response, "signedURL", None)
        )

        if signedURL is None:
            signedURL = (
                response.get("signedUrl") if isinstance(response, dict) else None
            )

        if signedURL is None:
            if isinstance(response, str) and "http" in response:
                signedURL = response

        if signedURL is None:
            raise ValueError(f"Failed to generate signed URL for path: {path}")
        return signedURL

    async def delete_file(self, path: str, bucket_name: Optional[str] = None):
        """Removes a file from storage."""
        client = await self._get_client()
        bucket = self._resolve_bucket(bucket_name)
        await client.storage.from_(bucket).remove([path])

    async def download_file(
        self, path: str, bucket_name: Optional[str] = None
    ) -> bytes:
        """Downloads raw binary content from storage."""
        client = await self._get_client()
        bucket = self._resolve_bucket(bucket_name)
        response = await client.storage.from_(bucket).download(path)
        if isinstance(response, (bytes, bytearray)):
            return bytes(response)
        if hasattr(response, "read"):
            return await response.read()
        raise ValueError(f"Failed to download file from storage: {path}")

    async def is_accessible(self, bucket_name: Optional[str] = None) -> bool:
        """Checks whether the configured storage bucket is reachable."""
        client = await self._get_client()
        bucket = self._resolve_bucket(bucket_name)
        await client.storage.from_(bucket).list(path="", options={"limit": 1})
        return True

    def get_public_url(self, path: str, bucket_name: Optional[str] = None) -> str:
        """Get public URL for a file (synchronous generation)."""
        url = os.getenv("SUPABASE_URL", "")
        if url.endswith("/"):
            url = url[:-1]

        bucket = self._resolve_bucket(bucket_name)
        return f"{url}/storage/v1/object/public/{bucket}/{path}"
