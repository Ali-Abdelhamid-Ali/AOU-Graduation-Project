"""User Repository - Complete User Management Data Access."""

from typing import Any, Dict, List, Optional

from src.db.supabase.client import SupabaseProvider
from src.observability.logger import get_logger
from src.repositories.schema_compat import sanitize_for_table, select_columns_for_table
from src.services.infrastructure.retry_utils import async_retry

logger = get_logger("repository.user")

_USER_ROLE_SELECT_COLUMNS = (
    "id, user_id, role, hospital_id, granted_by, granted_at, expires_at, "
    "is_active, created_at"
)

_PATIENT_SELECT_COLUMNS = select_columns_for_table(
    "patients",
    (
        "id",
        "user_id",
        "hospital_id",
        "mrn",
        "first_name",
        "last_name",
        "first_name_ar",
        "last_name_ar",
        "email",
        "phone",
        "gender",
        "date_of_birth",
        "blood_type",
        "avatar_url",
        "national_id",
        "passport_number",
        "address",
        "city",
        "region_id",
        "country_id",
        "emergency_contact_name",
        "emergency_contact_phone",
        "emergency_contact_relation",
        "allergies",
        "chronic_conditions",
        "current_medications",
        "insurance_provider",
        "insurance_number",
        "primary_doctor_id",
        "is_active",
        "notes",
        "settings",
        "created_at",
        "updated_at",
    ),
)


class UserRepository:
    def __init__(self):
        pass

    async def _get_client(self):
        return await SupabaseProvider.get_admin()

    async def _get_profile_from_table(
        self, client: Any, table: str, user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Read profiles using user_id first, then legacy rows keyed by id."""
        for key in ("user_id", "id"):
            result = (
                await client.table(table)
                .select("*")
                .eq(key, user_id)
                .limit(1)
                .execute()
            )
            if result.data:
                return result.data[0]
        return None

    async def _resolve_profile_lookup_key(
        self, client: Any, table: str, user_id: str
    ) -> Optional[str]:
        """Find the active lookup key for profile rows."""
        for key in ("user_id", "id"):
            result = (
                await client.table(table)
                .select("id")
                .eq(key, user_id)
                .limit(1)
                .execute()
            )
            if result.data:
                return key
        return None

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
            query = client.table("user_roles").select(_USER_ROLE_SELECT_COLUMNS)

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
                .select(_USER_ROLE_SELECT_COLUMNS)
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
            payload = sanitize_for_table("user_roles", role_data)
            result = await client.table("user_roles").insert(payload).execute()
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
            payload = sanitize_for_table("user_roles", role_data)
            result = await (
                client.table("user_roles").update(payload).eq("id", role_id).execute()
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
            payload = sanitize_for_table("doctors", doctor_data)
            result = await client.table("doctors").insert(payload).execute()
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
            payload = sanitize_for_table("doctors", doctor_data)
            result = await (
                client.table("doctors")
                .update(payload)
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
            payload = sanitize_for_table(
                "doctor_specialties", {**specialty_data, "doctor_id": doctor_id}
            )
            result = await (
                client.table("doctor_specialties").insert(payload).execute()
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
            payload = sanitize_for_table("nurses", nurse_data)
            result = await client.table("nurses").insert(payload).execute()
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
            payload = sanitize_for_table("nurses", nurse_data)
            result = await (
                client.table("nurses").update(payload).eq("id", nurse_id).execute()
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
            payload = sanitize_for_table("administrators", admin_data)
            result = await client.table("administrators").insert(payload).execute()
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
            payload = sanitize_for_table("administrators", admin_data)
            result = await (
                client.table("administrators")
                .update(payload)
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
            query = client.table("patients").select(_PATIENT_SELECT_COLUMNS)

            if filters:
                for key, val in filters.items():
                    if val is not None:
                        if key == "search":
                            # Handle search separately
                            search_term = str(val)
                            for unsafe in ("%", "_", ",", "(", ")", "{", "}"):
                                search_term = search_term.replace(unsafe, "")
                            query = query.or_(
                                "first_name.ilike.%{0}%,last_name.ilike.%{0}%,"
                                "mrn.ilike.%{0}%,phone.ilike.%{0}%".format(search_term)
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
            payload = sanitize_for_table("patients", patient_data)
            result = await client.table("patients").insert(payload).execute()
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
            payload = sanitize_for_table("patients", patient_data)
            result = (
                await client.table("patients")
                .update(payload)
                .eq("id", patient_id)
                .execute()
            )
            if result.data:
                return result.data[0]

            result = (
                await client.table("patients")
                .update(payload)
                .eq("user_id", patient_id)
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
                return await self._get_profile_from_table(client, target_table, user_id)

        # Fallback to known profile tables when the role is missing or stale.
        tables = ["patients", "doctors", "nurses", "administrators"]
        for table in tables:
            profile = await self._get_profile_from_table(client, table, user_id)
            if profile:
                return profile

        return None

    @async_retry(max_retries=3)
    async def update_my_profile(
        self, user_id: str, profile_data: Dict[str, Any], role: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Updates user profile data across role tables safely."""
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
            ],
            "nurses": [
                "first_name",
                "last_name",
                "phone",
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
                filtered_data = sanitize_for_table(
                    target_table,
                    {k: v for k, v in profile_data.items() if k in allowed_fields},
                )
                if filtered_data:
                    lookup_key = await self._resolve_profile_lookup_key(
                        client, target_table, user_id
                    )
                    if not lookup_key:
                        return None
                    await (
                        client.table(target_table)
                        .update(filtered_data)
                        .eq(lookup_key, user_id)
                        .execute()
                    )
                return await self._get_profile_from_table(client, target_table, user_id)

        # Fallback to checked loop if role not provided or unknown
        for table, allowed_fields in table_fields.items():
            # Filter profile_data to only include fields that exist in this table
            filtered_data = sanitize_for_table(
                table, {k: v for k, v in profile_data.items() if k in allowed_fields}
            )
            if filtered_data:
                lookup_key = await self._resolve_profile_lookup_key(client, table, user_id)
                if not lookup_key:
                    continue
                await (
                    client.table(table)
                    .update(filtered_data)
                    .eq(lookup_key, user_id)
                    .execute()
                )
                return await self._get_profile_from_table(client, table, user_id)

        return None

