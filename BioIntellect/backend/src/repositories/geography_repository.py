"""Geography Repository - Complete Geographic Data Access."""

from typing import Optional, List, Dict, Any
from src.db.supabase.client import SupabaseProvider
from src.observability.logger import get_logger
from src.services.infrastructure.retry_utils import async_retry

logger = get_logger("repository.geography")


class GeographyRepository:
    def __init__(self):
        pass

    async def _get_client(self):
        return await SupabaseProvider.get_admin()

    # â”پâ”پâ”پâ”پ COUNTRIES â”پâ”پâ”پâ”پ

    async def list_countries(
        self,
        filters: dict[str, Any | None] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List all countries with optional filtering."""
        client = await self._get_client()
        try:
            # Plan Section 7.B: Specific selectors
            query = client.table("countries").select("*")

            if filters:
                for key, val in filters.items():
                    if val is not None:
                        query = query.eq(key, val)

            result = await (
                query.order("country_name_en")
                .range(offset, offset + limit - 1)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to list countries: {str(e)}")
            raise

    async def get_country(self, country_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific country by ID."""
        client = await self._get_client()
        try:
            result = await (
                client.table("countries")
                .select("*")
                .eq("id", country_id)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to get country {country_id}: {str(e)}")
            raise

    @async_retry(max_retries=3)
    async def create_country(self, country_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new country."""
        client = await self._get_client()
        try:
            result = await client.table("countries").insert(country_data).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Failed to create country: {str(e)}")
            raise

    @async_retry(max_retries=3)
    async def update_country(
        self, country_id: str, country_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update a country."""
        client = await self._get_client()
        try:
            result = await (
                client.table("countries")
                .update(country_data)
                .eq("id", country_id)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to update country {country_id}: {str(e)}")
            raise

    @async_retry(max_retries=3)
    async def delete_country(self, country_id: str) -> bool:
        """Delete a country."""
        client = await self._get_client()
        try:
            result = await (
                client.table("countries").delete().eq("id", country_id).execute()
            )
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Failed to delete country {country_id}: {str(e)}")
            raise

    # â”پâ”پâ”پâ”پ REGIONS â”پâ”پâ”پâ”پ

    async def list_regions(
        self,
        filters: dict[str, Any | None] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List all regions with optional filtering."""
        client = await self._get_client()
        try:
            # Plan Section 7.B: Specific selectors
            query = client.table("regions").select("*")

            if filters:
                for key, val in filters.items():
                    if val is not None:
                        query = query.eq(key, val)

            result = await (
                query.order("region_name_en")
                .range(offset, offset + limit - 1)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to list regions: {str(e)}")
            raise

    async def get_region(self, region_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific region by ID."""
        client = await self._get_client()
        try:
            result = await (
                client.table("regions")
                .select("*")
                .eq("id", region_id)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to get region {region_id}: {str(e)}")
            raise

    @async_retry(max_retries=3)
    async def create_region(self, region_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new region."""
        client = await self._get_client()
        try:
            result = await client.table("regions").insert(region_data).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Failed to create region: {str(e)}")
            raise

    @async_retry(max_retries=3)
    async def update_region(
        self, region_id: str, region_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update a region."""
        client = await self._get_client()
        try:
            result = await (
                client.table("regions")
                .update(region_data)
                .eq("id", region_id)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to update region {region_id}: {str(e)}")
            raise

    @async_retry(max_retries=3)
    async def delete_region(self, region_id: str) -> bool:
        """Delete a region."""
        client = await self._get_client()
        try:
            result = (
                await client.table("regions").delete().eq("id", region_id).execute()
            )
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Failed to delete region {region_id}: {str(e)}")
            raise

    # â”پâ”پâ”پâ”پ HOSPITALS â”پâ”پâ”پâ”پ

    async def list_hospitals(
        self,
        filters: dict[str, Any | None] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List all hospitals with optional filtering."""
        client = await self._get_client()
        try:
            # Plan Section 7.B: Specific selectors
            query = client.table("hospitals").select("*")

            if filters:
                for key, val in filters.items():
                    if val is not None:
                        query = query.eq(key, val)

            result = await (
                query.order("hospital_name_en")
                .range(offset, offset + limit - 1)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to list hospitals: {str(e)}")
            raise

    async def get_hospital(self, hospital_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific hospital by ID."""
        client = await self._get_client()
        try:
            result = await (
                client.table("hospitals")
                .select("*")
                .eq("id", hospital_id)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to get hospital {hospital_id}: {str(e)}")
            raise

    @async_retry(max_retries=3)
    async def create_hospital(self, hospital_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new hospital."""
        client = await self._get_client()
        try:
            result = await client.table("hospitals").insert(hospital_data).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Failed to create hospital: {str(e)}")
            raise

    @async_retry(max_retries=3)
    async def update_hospital(
        self, hospital_id: str, hospital_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update a hospital."""
        client = await self._get_client()
        try:
            result = await (
                client.table("hospitals")
                .update(hospital_data)
                .eq("id", hospital_id)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to update hospital {hospital_id}: {str(e)}")
            raise

    @async_retry(max_retries=3)
    async def delete_hospital(self, hospital_id: str) -> bool:
        """Delete a hospital."""
        client = await self._get_client()
        try:
            result = await (
                client.table("hospitals").delete().eq("id", hospital_id).execute()
            )
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Failed to delete hospital {hospital_id}: {str(e)}")
            raise

    # â”پâ”پâ”پâ”پ SPECIALTIES â”پâ”پâ”پâ”پ

    async def list_specialties(
        self,
        filters: dict[str, Any | None] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List all medical specialties with optional filtering."""
        client = await self._get_client()
        try:
            # Plan Section 7.B: Specific selectors
            query = client.table("specialty_types").select(
                "id, specialty_code, specialty_name_en, specialty_name_ar"
            )

            if filters:
                for key, val in filters.items():
                    if val is not None:
                        query = query.eq(key, val)

            result = await (
                query.order("specialty_name_en")
                .range(offset, offset + limit - 1)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to list specialties: {str(e)}")
            raise

