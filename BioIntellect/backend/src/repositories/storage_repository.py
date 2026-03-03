"""Storage Repository - Managed Supabase Storage Access."""

import os
from src.db.supabase.client import SupabaseProvider
from src.services.infrastructure.retry_utils import async_retry


class StorageRepository:
    """
    Handles direct Supabase Storage interactions.
    STRICT RULE: Only handles binary data and paths. Metadata goes to DB repositories.
    """

    def __init__(self, bucket_name: str = "medical-files"):
        self.bucket = bucket_name

    async def _get_client(self):
        return await SupabaseProvider.get_admin()

    @async_retry(max_retries=3)
    async def upload_file(self, path: str, content: bytes, content_type: str) -> str:
        """Uploads binary content to a specific path."""
        client = await self._get_client()
        await client.storage.from_(self.bucket).upload(
            path=path, file=content, file_options={"content-type": content_type}
        )
        return path

    @async_retry(max_retries=3)
    async def get_signed_url(self, path: str, expires_in: int = 3600) -> str:
        """Generates a transient signed URL for secure download."""
        client = await self._get_client()
        response = await client.storage.from_(self.bucket).create_signed_url(
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

    async def delete_file(self, path: str):
        """Removes a file from storage."""
        client = await self._get_client()
        await client.storage.from_(self.bucket).remove([path])

    async def is_accessible(self) -> bool:
        """Checks whether the configured storage bucket is reachable."""
        client = await self._get_client()
        await client.storage.from_(self.bucket).list(path="", options={"limit": 1})
        return True

    def get_public_url(self, path: str) -> str:
        """Get public URL for a file (synchronous generation)."""
        url = os.getenv("SUPABASE_URL", "")
        if url.endswith("/"):
            url = url[:-1]

        return f"{url}/storage/v1/object/public/{self.bucket}/{path}"

