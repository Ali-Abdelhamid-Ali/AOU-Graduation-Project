"""Auth Repository - Data Access for Authentication and Profiles."""

from typing import Any, Dict, Optional

from src.db.supabase.client import SupabaseProvider
from src.observability.logger import get_logger
from src.repositories.schema_compat import sanitize_for_table
from src.services.infrastructure.retry_utils import async_retry

logger = get_logger("repository.auth")


class AuthRepository:
    """
    Handles all direct interactions with Supabase Auth and Role-based tables.
    STRICT RULE: This is the ONLY place allowed to talk to Supabase Auth/Profiles.
    """

    async def _get_admin(self):
        return await SupabaseProvider.get_admin()

    async def _get_anon(self):
        return await SupabaseProvider.get_client()

    async def _create_anon(self):
        return await SupabaseProvider.create_anon_client()

    async def _get_profile_by_identity(
        self, client: Any, table: str, user_id: str, columns: str = "*"
    ) -> Optional[Dict[str, Any]]:
        """Support both schema-correct user_id rows and legacy id-keyed rows."""
        for key in ("user_id", "id"):
            result = (
                await client.table(table)
                .select(columns)
                .eq(key, user_id)
                .limit(1)
                .execute()
            )
            if result.data:
                return result.data[0]
        return None

    @async_retry(max_retries=3)
    async def create_auth_user(
        self, email: str, password: str, metadata: Dict[str, Any]
    ) -> str:
        """Create user in Supabase Auth."""
        client = await self._get_admin()
        # gotrue-py (used by supabase-py) methods are often sync wrappers or allow async depending on version
        # But supabase-py v2 Client.auth... methods are usually sync unless we use AsyncClient
        # With AsyncClient, .auth.admin... calls should be awaited if they perform IO.
        # However, supabase-py's AsyncClient.auth might still be the sync GoTrueClient in some versions?
        # Checking implementation: AsyncClient.auth returns an AsyncGoTrueClient usually.
        # We will assume await is needed.

        response = await client.auth.admin.create_user(
            {
                "email": email,
                "password": password,
                "email_confirm": True,
                "user_metadata": metadata,
            }
        )
        if not response.user:
            raise Exception("Auth user creation failed")
        return str(response.user.id)

    @async_retry(max_retries=3)
    async def delete_auth_user(self, user_id: str):
        """Delete user from Supabase Auth (Compensation task)."""
        client = await self._get_admin()
        await client.auth.admin.delete_user(user_id)

    @async_retry(max_retries=3)
    async def create_profile(self, table: str, profile_data: Dict[str, Any]):
        """Create role-specific profile record."""
        client = await self._get_admin()
        payload = sanitize_for_table(table, profile_data)
        return await client.table(table).upsert(payload).execute()

    async def get_profile_by_user_id(
        self, table: str, user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch the full role profile for a specific auth user."""
        client = await self._get_admin()
        return await self._get_profile_by_identity(client, table, user_id)

    async def resolve_user_role(
        self, user_id: str, metadata_role: Optional[str] = None
    ) -> str:
        """Resolve user role using profile tables, with metadata as a constrained fallback."""
        client = await self._get_admin()
        metadata_role_normalized = (metadata_role or "").strip().lower()

        # administrators table can store admin/super_admin in the role column.
        try:
            admin_result = await (
                client.table("administrators")
                .select("role")
                .eq("user_id", user_id)
                .limit(1)
                .execute()
            )
            if admin_result.data:
                admin_role = (
                    str(admin_result.data[0].get("role") or "admin").strip().lower()
                )
                return admin_role if admin_role in {"admin", "super_admin"} else "admin"
        except Exception:
            # Do not fail auth flow for table shape differences.
            pass

        for table_name, role_name in (
            ("doctors", "doctor"),
            ("nurses", "nurse"),
            ("patients", "patient"),
        ):
            try:
                profile = await self._get_profile_by_identity(
                    client, table_name, user_id, "id, user_id"
                )
                if profile:
                    return role_name
            except Exception:
                continue

        # Never trust elevated metadata role without a backing profile.
        if metadata_role_normalized in {"doctor", "nurse", "patient"}:
            return metadata_role_normalized
        return "patient"

    async def sign_in(self, email: str, password: str):
        """Standard user sign in."""
        client = await self._create_anon()
        return await client.auth.sign_in_with_password(
            {"email": email, "password": password}
        )

    async def get_user_from_token(self, access_token: str) -> Dict[str, str]:
        """Resolve user identity from an access token."""
        client = await self._create_anon()
        user_response = await client.auth.get_user(access_token)
        user = getattr(user_response, "user", None)
        if user is None:
            raise Exception("Invalid access token")

        user_id = str(getattr(user, "id", "") or "")
        user_email = str(getattr(user, "email", "") or "")
        if not user_id or not user_email:
            raise Exception("Invalid access token payload")

        return {"id": user_id, "email": user_email}

    async def refresh_session(self, refresh_token: str):
        """Refresh a session using a dedicated anon client."""
        client = await self._create_anon()
        return await client.auth.refresh_session(refresh_token)

    async def reset_password(self, email: str, redirect_to: Optional[str] = None):
        """Send password reset email."""
        client = await self._create_anon()
        options = {"redirect_to": redirect_to} if redirect_to else None
        return await client.auth.reset_password_for_email(email, options=options)

    @async_retry(max_retries=3)
    async def update_password(self, user_id: str, new_password: str):
        """Update user password using Admin API (More reliable)."""
        client = await self._get_admin()
        response = await client.auth.admin.update_user_by_id(
            user_id, {"password": new_password}
        )
        if not response.user:
            logger.error(
                f"Password update failed for {user_id}: No user returned in response"
            )
            raise Exception("Password update failed on server")
        return response

    async def sign_out(
        self, user_id: str, scope: str = "local", jwt: Optional[str] = None
    ):
        """Sign out user. For global scope, invalidates all sessions."""
        client = await self._get_admin()
        if scope == "global":
            # If we have a JWT, use it as the admin.sign_out expects it
            token_to_use = (
                jwt or user_id
            )  # Fallback to user_id (sig says jwt but let's be safe)
            try:
                return await client.auth.admin.sign_out(token_to_use, scope="global")
            except Exception as e:
                logger.error(f"Global signout failed for {user_id}: {str(e)}")
                # Don't fail the whole operation if signout fails but password was changed
                return {"error": str(e)}

        # Local sign out (server-side acknowledgment)
        return {"message": "Signed out successfully"}

    @async_retry(max_retries=3)
    async def link_doctor_specialty(self, doctor_id: str, specialty_code: str):
        """Links a doctor to a specialty using the code."""
        # 1. Get Specialty ID
        client = await self._get_admin()
        spec = await (
            client.table("specialty_types")
            .select("id")
            .eq("specialty_code", specialty_code)
            .limit(1)
            .execute()
        )
        if not spec.data:
            return None  # Specialty not found

        spec_id = spec.data[0]["id"]

        # 2. Link
        payload = sanitize_for_table(
            "doctor_specialties",
            {"doctor_id": doctor_id, "specialty_id": spec_id, "is_primary": True},
        )
        return await client.table("doctor_specialties").insert(payload).execute()

