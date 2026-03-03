"""User Repository - Complete User Management Data Access."""

from typing import Optional, List, Dict, Any
from src.db.supabase.client import SupabaseProvider
from src.observability.logger import get_logger
from src.services.infrastructure.retry_utils import async_retry

logger = get_logger("repository.user")


class UserRepository:
    def __init__(self):
        pass

    async def _get_client(self):
        return await SupabaseProvider.get_admin()

    # â”پâ”پâ”پâ”پ USER ROLES â”پâ”پâ”پâ”پ

    async def list_user_roles(
        self,
        filters: Dict[str, Any | None] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List all user roles with optional filtering."""
        client = await self._get_client()
        try:
            # Plan Section 7.B: Specific selectors
            query = client.table("user_roles").select(
                "id, role_name, permissions, created_at"
            )

            if filters:
                for key, val in filters.items():
                    if val is not None:
                        query = query.eq(key, val)

            result = await (
                query.order("created_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to list user roles: {str(e)}")
            raise

    async def get_user_role(self, role_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific user role by ID."""
        client = await self._get_client()
        try:
            result = await (
                client.table("user_roles")
                .select("id, role_name, permissions, created_at")
                .eq("id", role_id)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to get user role {role_id}: {str(e)}")
            raise

    @async_retry(max_retries=3)
    async def create_user_role(self, role_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user role."""
        client = await self._get_client()
        try:
            result = await client.table("user_roles").insert(role_data).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Failed to create user role: {str(e)}")
            raise

    @async_retry(max_retries=3)
    async def update_user_role(
        self, role_id: str, role_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update a user role."""
        client = await self._get_client()
        try:
            result = await (
                client.table("user_roles").update(role_data).eq("id", role_id).execute()
            )
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to update user role {role_id}: {str(e)}")
            raise

    @async_retry(max_retries=3)
    async def delete_user_role(self, role_id: str) -> bool:
        """Delete a user role."""
        client = await self._get_client()
        try:
            result = await (
                client.table("user_roles").delete().eq("id", role_id).execute()
            )
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Failed to delete user role {role_id}: {str(e)}")
            raise

    # â”پâ”پâ”پâ”پ DOCTORS â”پâ”پâ”پâ”پ

    async def list_doctors(
        self,
        filters: Dict[str, Any | None] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List all doctors with optional filtering."""
        client = await self._get_client()
        try:
            # Plan Section 7.B: Specific selectors
            query = client.table("doctors").select(
                "id, user_id, hospital_id, employee_id, first_name, last_name, first_name_ar, last_name_ar, email, phone, gender, date_of_birth, license_number, license_expiry, qualification, years_of_experience, bio, country_id, region_id, avatar_url, is_active, is_verified, verified_at, verified_by, settings, created_at, updated_at"
            )

            if filters:
                for key, val in filters.items():
                    if val is not None:
                        query = query.eq(key, val)

            result = await (
                query.order("first_name").range(offset, offset + limit - 1).execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to list doctors: {str(e)}")
            raise

    async def get_doctor(self, doctor_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific doctor by ID or User ID."""
        client = await self._get_client()
        try:
            result_by_id = (
                await client.table("doctors")
                .select("*")
                .eq("id", doctor_id)
                .limit(1)
                .execute()
            )
            if result_by_id.data:
                return result_by_id.data[0]

            result_by_user = (
                await client.table("doctors")
                .select("*")
                .eq("user_id", doctor_id)
                .limit(1)
                .execute()
            )
            return result_by_user.data[0] if result_by_user.data else None
        except Exception as e:
            logger.error(f"Failed to get doctor {doctor_id}: {str(e)}")
            raise

    @async_retry(max_retries=3)
    async def create_doctor(self, doctor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new doctor."""
        client = await self._get_client()
        try:
            result = await client.table("doctors").insert(doctor_data).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Failed to create doctor: {str(e)}")
            raise

    @async_retry(max_retries=3)
    async def update_doctor(
        self, doctor_id: str, doctor_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update a doctor."""
        client = await self._get_client()
        try:
            result = await (
                client.table("doctors")
                .update(doctor_data)
                .eq("id", doctor_id)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to update doctor {doctor_id}: {str(e)}")
            raise

    @async_retry(max_retries=3)
    async def delete_doctor(self, doctor_id: str) -> bool:
        """Delete a doctor."""
        client = await self._get_client()
        try:
            result = (
                await client.table("doctors").delete().eq("id", doctor_id).execute()
            )
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Failed to delete doctor {doctor_id}: {str(e)}")
            raise

    # â”پâ”پâ”پâ”پ DOCTOR SPECIALTIES â”پâ”پâ”پâ”پ

    async def list_doctor_specialties(
        self,
        filters: Dict[str, Any | None] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List doctor specialties with optional filtering."""
        client = await self._get_client()
        try:
            query = client.table("doctor_specialties").select(
                "id, doctor_id, specialty_id, is_primary, created_at"
            )

            if filters:
                for key, val in filters.items():
                    if val is not None:
                        query = query.eq(key, val)

            result = await (
                query.order("created_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to list doctor specialties: {str(e)}")
            raise

    async def add_doctor_specialty(
        self, doctor_id: str, specialty_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add a specialty to a doctor."""
        client = await self._get_client()
        try:
            # Ensure doctor_id is set in the data
            specialty_data["doctor_id"] = doctor_id
            result = await (
                client.table("doctor_specialties").insert(specialty_data).execute()
            )
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Failed to add specialty to doctor {doctor_id}: {str(e)}")
            raise

    async def remove_doctor_specialty(self, doctor_id: str, specialty_id: str) -> bool:
        """Remove a specialty from a doctor."""
        client = await self._get_client()
        try:
            result = await (
                client.table("doctor_specialties")
                .delete()
                .eq("id", specialty_id)
                .eq("doctor_id", doctor_id)
                .execute()
            )
            return len(result.data) > 0
        except Exception as e:
            logger.error(
                f"Failed to remove specialty from doctor {doctor_id}: {str(e)}"
            )
            raise

    # â”پâ”پâ”پâ”پ NURSES â”پâ”پâ”پâ”پ

    async def list_nurses(
        self,
        filters: Dict[str, Any | None] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List all nurses with optional filtering."""
        client = await self._get_client()
        try:
            # Plan Section 7.B: Specific selectors
            query = client.table("nurses").select(
                "id, first_name, last_name, hospital_id, license_number, created_at"
            )

            if filters:
                for key, val in filters.items():
                    if val is not None:
                        query = query.eq(key, val)

            result = await (
                query.order("first_name").range(offset, offset + limit - 1).execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to list nurses: {str(e)}")
            raise

    async def get_nurse(self, nurse_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific nurse by ID or User ID."""
        client = await self._get_client()
        try:
            result_by_id = (
                await client.table("nurses")
                .select("*")
                .eq("id", nurse_id)
                .limit(1)
                .execute()
            )
            if result_by_id.data:
                return result_by_id.data[0]

            result_by_user = (
                await client.table("nurses")
                .select("*")
                .eq("user_id", nurse_id)
                .limit(1)
                .execute()
            )
            return result_by_user.data[0] if result_by_user.data else None
        except Exception as e:
            logger.error(f"Failed to get nurse {nurse_id}: {str(e)}")
            raise

    @async_retry(max_retries=3)
    async def create_nurse(self, nurse_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new nurse."""
        client = await self._get_client()
        try:
            result = await client.table("nurses").insert(nurse_data).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Failed to create nurse: {str(e)}")
            raise

    @async_retry(max_retries=3)
    async def update_nurse(
        self, nurse_id: str, nurse_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update a nurse."""
        client = await self._get_client()
        try:
            result = await (
                client.table("nurses").update(nurse_data).eq("id", nurse_id).execute()
            )
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to update nurse {nurse_id}: {str(e)}")
            raise

    @async_retry(max_retries=3)
    async def delete_nurse(self, nurse_id: str) -> bool:
        """Delete a nurse."""
        client = await self._get_client()
        try:
            result = await client.table("nurses").delete().eq("id", nurse_id).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Failed to delete nurse {nurse_id}: {str(e)}")
            raise

    # â”پâ”پâ”پâ”پ ADMINISTRATORS â”پâ”پâ”پâ”پ

    async def list_administrators(
        self,
        filters: Dict[str, Any | None] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List all administrators with optional filtering."""
        client = await self._get_client()
        try:
            # Plan Section 7.B: Specific selectors
            query = client.table("administrators").select(
                "id, first_name, last_name, hospital_id, created_at"
            )

            if filters:
                for key, val in filters.items():
                    if val is not None:
                        query = query.eq(key, val)

            result = await (
                query.order("first_name").range(offset, offset + limit - 1).execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to list administrators: {str(e)}")
            raise

    async def get_administrator(self, admin_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific administrator by ID or User ID."""
        client = await self._get_client()
        try:
            result_by_id = (
                await client.table("administrators")
                .select("*")
                .eq("id", admin_id)
                .limit(1)
                .execute()
            )
            if result_by_id.data:
                return result_by_id.data[0]

            result_by_user = (
                await client.table("administrators")
                .select("*")
                .eq("user_id", admin_id)
                .limit(1)
                .execute()
            )
            return result_by_user.data[0] if result_by_user.data else None
        except Exception as e:
            logger.error(f"Failed to get administrator {admin_id}: {str(e)}")
            raise

    @async_retry(max_retries=3)
    async def create_administrator(self, admin_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new administrator."""
        client = await self._get_client()
        try:
            result = await client.table("administrators").insert(admin_data).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Failed to create administrator: {str(e)}")
            raise

    @async_retry(max_retries=3)
    async def update_administrator(
        self, admin_id: str, admin_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update an administrator."""
        client = await self._get_client()
        try:
            result = await (
                client.table("administrators")
                .update(admin_data)
                .eq("id", admin_id)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to update administrator {admin_id}: {str(e)}")
            raise

    @async_retry(max_retries=3)
    async def delete_administrator(self, admin_id: str) -> bool:
        """Delete an administrator."""
        client = await self._get_client()
        try:
            result = await (
                client.table("administrators").delete().eq("id", admin_id).execute()
            )
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Failed to delete administrator {admin_id}: {str(e)}")
            raise

    # â”پâ”پâ”پâ”پ PATIENTS â”پâ”پâ”پâ”پ

    async def list_patients(
        self,
        filters: Dict[str, Any | None] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List all patients with optional filtering."""
        client = await self._get_client()
        try:
            # Plan Section 7.B: Specific selectors
            query = client.table("patients").select(
                "id, mrn, first_name, last_name, hospital_id, created_at"
            )

            if filters:
                for key, val in filters.items():
                    if val is not None:
                        if key == "search":
                            # Handle search separately
                            search_term = str(val)
                            for unsafe in ("%", "_", ",", "(", ")", "{", "}"):
                                search_term = search_term.replace(unsafe, "")
                            query = query.or_(
                                f"first_name.ilike.%{search_term}%,last_name.ilike.%{search_term}%,mrn.ilike.%{search_term}%"
                            )
                        else:
                            query = query.eq(key, val)

            result = await (
                query.order("first_name").range(offset, offset + limit - 1).execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to list patients: {str(e)}")
            raise

    async def get_patient(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific patient by ID or User ID."""
        client = await self._get_client()
        try:
            result_by_id = (
                await client.table("patients")
                .select("*")
                .eq("id", patient_id)
                .limit(1)
                .execute()
            )
            if result_by_id.data:
                return result_by_id.data[0]

            result_by_user = (
                await client.table("patients")
                .select("*")
                .eq("user_id", patient_id)
                .limit(1)
                .execute()
            )
            return result_by_user.data[0] if result_by_user.data else None
        except Exception as e:
            logger.error(f"Failed to get patient {patient_id}: {str(e)}")
            raise

    @async_retry(max_retries=3)
    async def create_patient(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new patient."""
        client = await self._get_client()
        try:
            result = await client.table("patients").insert(patient_data).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Failed to create patient: {str(e)}")
            raise

    @async_retry(max_retries=3)
    async def update_patient(
        self, patient_id: str, patient_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update a patient."""
        client = await self._get_client()
        try:
            result = await (
                client.table("patients")
                .update(patient_data)
                .eq("id", patient_id)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to update patient {patient_id}: {str(e)}")
            raise

    @async_retry(max_retries=3)
    async def delete_patient(self, patient_id: str) -> bool:
        """Delete a patient."""
        client = await self._get_client()
        try:
            result = await (
                client.table("patients").delete().eq("id", patient_id).execute()
            )
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Failed to delete patient {patient_id}: {str(e)}")
            raise

    # â”پâ”پâ”پâ”پ USER PROFILE MANAGEMENT â”پâ”پâ”پâ”پ

    async def get_my_profile(
        self, user_id: str, role: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get current user's profile from appropriate table."""
        import asyncio

        client = await self._get_client()

        # If role is provided, query only that specific table
        if role:
            table_map = {
                "patient": "patients",
                "doctor": "doctors",
                "nurse": "nurses",
                "admin": "administrators",
                "super_admin": "administrators",
            }
            target_table = table_map.get(role)
            if target_table:
                result = (
                    await client.table(target_table)
                    .select("*")
                    .eq("user_id", user_id)
                    .limit(1)
                    .execute()
                )
                return result.data[0] if result.data else None

        # Fallback to parallel execution if role is unknown or not provided
        tables = ["patients", "doctors", "nurses", "administrators"]

        tasks = [
            client.table(table).select("*").eq("user_id", user_id).limit(1).execute()
            for table in tables
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for res in results:
            if not isinstance(res, BaseException) and res.data:
                return res.data[0]

        return None

    @async_retry(max_retries=3)
    async def update_my_profile(
        self, user_id: str, profile_data: Dict[str, Any], role: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Updates user profile data across role tables safely."""
        import asyncio

        client = await self._get_client()

        # Define allowed fields for each table to prevent Supabase errors
        # Now including geography and hospital IDs
        table_fields = {
            "patients": [
                "first_name",
                "last_name",
                "first_name_ar",
                "last_name_ar",
                "phone",
                "gender",
                "date_of_birth",
                "avatar_url",
                "mrn",
                "blood_type",
                "national_id",
                "passport_number",
                "address",
                "city",
                "country_id",
                "region_id",
                "hospital_id",
                "insurance_provider",
                "insurance_number",
                "emergency_contact_name",
                "emergency_contact_phone",
                "emergency_contact_relation",
                "allergies",
                "chronic_conditions",
                "current_medications",
                "notes",
            ],
            "doctors": [
                "first_name",
                "last_name",
                "first_name_ar",
                "last_name_ar",
                "phone",
                "gender",
                "date_of_birth",
                "avatar_url",
                "license_number",
                "qualification",
                "years_of_experience",
                "bio",
                "country_id",
                "region_id",
                "hospital_id",
                "specialty",
                "department",
            ],
            "nurses": [
                "first_name",
                "last_name",
                "phone",
                "avatar_url",
                "license_number",
                "department",
                "country_id",
                "region_id",
                "hospital_id",
            ],
            "administrators": [
                "first_name",
                "last_name",
                "phone",
                "avatar_url",
                "department",
                "country_id",
                "region_id",
                "hospital_id",
            ],
        }

        # If role is provided, update only that specific table for efficiency
        if role:
            table_map = {
                "patient": "patients",
                "doctor": "doctors",
                "nurse": "nurses",
                "admin": "administrators",
                "super_admin": "administrators",
            }
            target_table = table_map.get(role)
            if target_table and target_table in table_fields:
                allowed_fields = table_fields[target_table]
                filtered_data = {
                    k: v for k, v in profile_data.items() if k in allowed_fields
                }
                if filtered_data:
                    result = (
                        await client.table(target_table)
                        .update(filtered_data)
                        .eq("user_id", user_id)
                        .execute()
                    )
                    return result.data[0] if result.data else None

        # Fallback to checked loop if role not provided or unknown
        tasks = []
        for table, allowed_fields in table_fields.items():
            # Filter profile_data to only include fields that exist in this table
            filtered_data = {
                k: v for k, v in profile_data.items() if k in allowed_fields
            }
            if filtered_data:
                tasks.append(
                    client.table(table)
                    .update(filtered_data)
                    .eq("user_id", user_id)
                    .execute()
                )

        if not tasks:
            return None

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for res in results:
            if not isinstance(res, BaseException) and getattr(res, "data", None):
                return res.data[0]

        return None

