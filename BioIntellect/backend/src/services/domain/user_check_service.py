"""User existence check service - optimized for single API call."""

from typing import Dict
from src.db.supabase.client import SupabaseProvider
from src.observability.logger import get_logger

logger = get_logger(__name__)


class UserCheckService:
    """Service to check user existence with optimized API calls."""

    async def _get_client(self):
        """Standard helper to get the admin client."""
        return await SupabaseProvider.get_admin()

    async def check_all_users_exist(self) -> Dict[str, bool]:
        """
        Check if all required user types exist in a single optimized operation.
        """
        user_types = ["admin", "doctor", "patient", "super_admin"]
        try:
            # Single query to check all user types existence
            client = await self._get_client()
            result = await client.rpc(
                "check_user_existence_batch", {"user_types": user_types}
            ).execute()

            if result.data and isinstance(result.data, dict):
                return {ut: result.data.get(ut, False) for ut in user_types}

            # Fallback if RPC returns unexpected format
            logger.warning("Batch RPC returned unexpected data format, falling back.")
            return await self._fallback_check_individual()

        except Exception as e:
            msg = str(e)
            if "PGRST202" in msg or "404" in msg:
                logger.info(
                    "RPC 'check_user_existence_batch' not found. This is expected before SQL fix. Falling back."
                )
            else:
                logger.warning(f"Batch user check failed: {e}. Falling back.")
            return await self._fallback_check_individual()

    async def _fallback_check_individual(self) -> Dict[str, bool]:
        """Fallback method that checks each user type individually."""
        checks = {}

        try:
            client = await self._get_client()
            # Check administrators - try with role column first, fallback to simple existence check
            try:
                admin_result = await (
                    client.table("administrators")
                    .select("id")
                    .eq("role", "admin")
                    .limit(1)
                    .execute()
                )
                checks["admin"] = len(admin_result.data) > 0
            except Exception as role_error:
                if "column administrators.role does not exist" in str(role_error):
                    # Fallback to simple existence check if role column doesn't exist
                    admin_result = await (
                        client.table("administrators").select("id").limit(1).execute()
                    )
                    checks["admin"] = len(admin_result.data) > 0
                else:
                    raise role_error

            # Check super admins - try with role column first, fallback to simple existence check
            try:
                super_admin_result = await (
                    client.table("administrators")
                    .select("id")
                    .eq("role", "super_admin")
                    .limit(1)
                    .execute()
                )
                checks["super_admin"] = len(super_admin_result.data) > 0
            except Exception as role_error:
                if "column administrators.role does not exist" in str(role_error):
                    # Fallback to simple existence check if role column doesn't exist
                    super_admin_result = await (
                        client.table("administrators").select("id").limit(1).execute()
                    )
                    checks["super_admin"] = len(super_admin_result.data) > 0
                else:
                    raise role_error

            # Check doctors
            doctor_result = await (
                client.table("doctors").select("id").limit(1).execute()
            )
            checks["doctor"] = len(doctor_result.data) > 0

            # Check patients
            patient_result = await (
                client.table("patients").select("id").limit(1).execute()
            )
            checks["patient"] = len(patient_result.data) > 0

        except Exception as e:
            logger.error(f"Individual user checks failed: {e}")
            checks = {ut: False for ut in ["admin", "doctor", "patient", "super_admin"]}

        return checks


# Global instance with lazy initialization
user_check_service = UserCheckService()

