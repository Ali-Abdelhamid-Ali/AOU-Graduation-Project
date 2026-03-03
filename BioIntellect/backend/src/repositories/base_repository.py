from typing import Generic, TypeVar, List, Optional, Any, Dict
from supabase import AsyncClient
from src.db.supabase.client import SupabaseProvider
from src.observability.logger import get_logger
from src.services.infrastructure.memory_cache import global_cache
import asyncio

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """
    Base Repository with Generic Type Support, Error Normalization,
    and Idempotent-safe Retry Logic.

    STRICT RULE: This layer is SENSITIVE to side-effects.
    Retries are ONLY allowed for idempotent operations.
    """

    def __init__(self, table_name: str):
        self.table_name = table_name
        self.logger = get_logger(f"repository.{table_name}")

    async def _get_client(self) -> AsyncClient:
        """Get the async supabase client."""
        return await SupabaseProvider.get_admin()

    async def _execute_with_retry(
        self, operation_func, is_idempotent: bool = False, max_retries: int = 3
    ):
        """
        Executes a database operation with safety-first retry logic.
        """
        attempt = 0
        while attempt < max_retries:
            try:
                # operation_func should be a coroutine
                return await operation_func()
            except Exception as e:
                attempt += 1
                self.logger.warning(
                    f"Operation failed (Attempt {attempt}/{max_retries}): {str(e)}"
                )

                if not is_idempotent:
                    self.logger.error(
                        "Non-idempotent operation failed. Aborting retry to prevent side-effects."
                    )
                    raise e

                if attempt >= max_retries:
                    self.logger.error(
                        f"Max retries reached for {self.table_name}. Raising exception."
                    )
                    raise e

                # Exponential backoff: 1s, 2s, 4s as per Plan Section 8.A
                await asyncio.sleep(2 ** (attempt - 1))

    async def get_by_id(self, id_val: Any, columns: str = "*") -> Optional[T]:
        """Fetch a single record by primary key. Uses limit(1) for robustness."""
        client = await self._get_client()

        async def _fetch():
            return await (
                client.table(self.table_name)
                .select(columns)
                .eq("id", id_val)
                .limit(1)
                .execute()
            )

        result = await self._execute_with_retry(_fetch, is_idempotent=True)
        return result.data[0] if result.data else None

    async def find_all(
        self,
        filters: dict[str, Any | None] | None = None,
        limit: int = 100,
        offset: int = 0,
        columns: str = "*",
    ) -> List[T]:
        """Fetch multiple records with basic filtering and pagination."""
        client = await self._get_client()

        async def _fetch_all():
            query = client.table(self.table_name).select(columns)
            if filters:
                for key, val in filters.items():
                    query = query.eq(key, val)
            return await query.range(offset, offset + limit - 1).execute()

        result = await self._execute_with_retry(_fetch_all, is_idempotent=True)
        return result.data or []

    async def create(self, data: Dict[str, Any]) -> Optional[T]:
        """Create a new record."""
        if not data or not isinstance(data, dict):
            self.logger.warning("Attempted to create record with invalid data")
            raise ValueError("Data must be a non-empty dictionary")

        client = await self._get_client()

        async def _create():
            return await client.table(self.table_name).insert(data).execute()

        try:
            result = await self._execute_with_retry(_create, is_idempotent=False)

            if result.data:
                # Plan Section 5.A: Invalidate list cache on write
                await global_cache.clear()  # Simple approach for Phase 1
                return result.data[0]

            return None

        except Exception as e:
            self.logger.error(f"Error creating record in {self.table_name}: {str(e)}")
            raise

    async def update(self, id_val: Any, data: Dict[str, Any]) -> Optional[T]:
        """Update a record by ID."""
        client = await self._get_client()

        async def _update():
            return (
                await client.table(self.table_name)
                .update(data)
                .eq("id", id_val)
                .execute()
            )

        # Update is generally idempotent if it's a full overwrite or simple field update
        result = await self._execute_with_retry(_update, is_idempotent=True)

        if result.data:
            await global_cache.clear()
            return result.data[0]

        return None

    async def delete(self, id_val: Any) -> bool:
        """Delete a record by ID."""
        client = await self._get_client()

        async def _delete():
            return (
                await client.table(self.table_name).delete().eq("id", id_val).execute()
            )

        # Delete is idempotent (deleting twice has the same effect as deleting once)
        result = await self._execute_with_retry(_delete, is_idempotent=True)

        if len(result.data) > 0:
            await global_cache.clear()
            return True

        return False

