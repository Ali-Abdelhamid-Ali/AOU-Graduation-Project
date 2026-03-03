"""System Repository - Complete System Settings and Model Version Management Implementation."""

import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime
from src.db.supabase.client import SupabaseProvider
from src.observability.logger import get_logger

logger = get_logger("repositories.system")


class SystemRepository:
    """Repository for system settings and model version management."""

    def __init__(self):
        # self.supabase = SupabaseProvider.get_client()
        pass

    async def _get_client(self):
        return await SupabaseProvider.get_admin()

    async def get_db_health_summary(self) -> Dict[str, Any]:
        """Get aggregate health counts for critical tables."""
        client = await self._get_client()
        try:
            results = await asyncio.gather(
                client.table("user_roles").select("id", count="exact").limit(1).execute(),
                client.table("audit_logs").select("id", count="exact").limit(1).execute(),
                client.table("medical_cases")
                .select("id", count="exact")
                .limit(1)
                .execute(),
                return_exceptions=True,
            )
            return {
                "users_count": results[0].count
                if not isinstance(results[0], Exception)
                else 0,
                "logs_count": results[1].count
                if not isinstance(results[1], Exception)
                else 0,
                "cases_count": results[2].count
                if not isinstance(results[2], Exception)
                else 0,
                "status": "healthy"
                if all(not isinstance(r, Exception) for r in results)
                else "degraded",
            }
        except Exception as e:
            logger.error(f"Failed to gather DB health summary: {str(e)}")
            raise

    async def check_admin_connection(self) -> bool:
        """Check admin database connectivity."""
        client = await self._get_client()
        await client.table("administrators").select("id").limit(1).execute()
        return True

    async def check_auth_service_connection(self) -> bool:
        """Check auth service connectivity via admin client."""
        client = await self._get_client()
        await client.auth.get_session()
        return True

    async def check_system_settings_connection(self) -> bool:
        """Check readiness against system_settings table."""
        client = await self._get_client()
        await client.table("system_settings").select("id").limit(1).execute()
        return True

    # â”پâ”پâ”پâ”پ SYSTEM SETTINGS â”پâ”پâ”پâ”پ

    async def list_system_settings(
        self, filters: Dict[str, Any], limit: int = 50, offset: int = 0
    ) -> List[Dict]:
        """List system settings with optional filtering."""
        client = await self._get_client()
        try:
            query = client.table("system_settings").select(
                "id, scope, scope_id, setting_key, setting_value, setting_type, description, is_sensitive, created_by, updated_by, created_at, updated_at"
            )

            # Apply filters
            for key, value in filters.items():
                if key == "is_sensitive":
                    query = query.eq("is_sensitive", value)
                else:
                    query = query.eq(key, value)

            # Apply pagination
            query = query.order("created_at", desc=True).range(
                offset, offset + limit - 1
            )

            result = await query.execute()
            return result.data or []

        except Exception as e:
            logger.error(f"Failed to list system settings: {str(e)}")
            return []

    async def get_system_setting(self, setting_id: str) -> Optional[Dict]:
        """Get a specific system setting by ID."""
        client = await self._get_client()
        try:
            result = await (
                client.table("system_settings")
                .select(
                    "id, scope, scope_id, setting_key, setting_value, setting_type, description, is_sensitive, created_by, updated_by, created_at, updated_at"
                )
                .eq("id", setting_id)
                .single()
                .execute()
            )
            return result.data
        except Exception as e:
            logger.error(f"Failed to get system setting {setting_id}: {str(e)}")
            return None

    async def get_settings_by_scope(self, scope: str, scope_id: str) -> List[Dict]:
        """Get all settings for a specific scope."""
        client = await self._get_client()
        try:
            result = await (
                client.table("system_settings")
                .select(
                    "id, scope, scope_id, setting_key, setting_value, setting_type, description, is_sensitive, created_by, updated_by, created_at, updated_at"
                )
                .eq("scope", scope)
                .eq("scope_id", scope_id)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(
                f"Failed to get settings for scope {scope}/{scope_id}: {str(e)}"
            )
            return []

    async def get_global_settings(self) -> List[Dict]:
        """Get all global system settings."""
        client = await self._get_client()
        try:
            result = await (
                client.table("system_settings")
                .select(
                    "id, scope, scope_id, setting_key, setting_value, setting_type, description, is_sensitive, created_by, updated_by, created_at, updated_at"
                )
                .eq("scope", "global")
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to get global settings: {str(e)}")
            return []

    async def get_sensitive_settings(self) -> List[Dict]:
        """Get all sensitive system settings."""
        client = await self._get_client()
        try:
            result = await (
                client.table("system_settings")
                .select(
                    "id, scope, scope_id, setting_key, setting_value, setting_type, description, is_sensitive, created_by, updated_by, created_at, updated_at"
                )
                .eq("is_sensitive", True)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to get sensitive settings: {str(e)}")
            return []

    async def create_system_setting(self, setting_data: Dict) -> Dict:
        """Create a new system setting."""
        client = await self._get_client()
        try:
            # Add required fields
            setting_data["created_at"] = datetime.utcnow().isoformat()
            setting_data["updated_at"] = datetime.utcnow().isoformat()

            result = await (
                client.table("system_settings").insert(setting_data).execute()
            )
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Failed to create system setting: {str(e)}")
            raise

    async def update_system_setting(
        self, setting_id: str, update_data: Dict
    ) -> Optional[Dict]:
        """Update a system setting."""
        client = await self._get_client()
        try:
            update_data["updated_at"] = datetime.utcnow().isoformat()

            result = await (
                client.table("system_settings")
                .update(update_data)
                .eq("id", setting_id)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to update system setting {setting_id}: {str(e)}")
            return None

    async def delete_system_setting(self, setting_id: str) -> bool:
        """Delete a system setting."""
        client = await self._get_client()
        try:
            result = await (
                client.table("system_settings").delete().eq("id", setting_id).execute()
            )
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Failed to delete system setting {setting_id}: {str(e)}")
            return False

    async def get_setting_keys(self) -> List[str]:
        """Get all available setting keys."""
        client = await self._get_client()
        try:
            result = await (
                client.table("system_settings")
                .select("setting_key", distinct=True)
                .execute()
            )
            return [row["setting_key"] for row in result.data or []]
        except Exception as e:
            logger.error(f"Failed to get setting keys: {str(e)}")
            return []

    # â”پâ”پâ”پâ”پ MODEL VERSIONS â”پâ”پâ”پâ”پ

    async def list_model_versions(
        self, filters: Dict[str, Any], limit: int = 50, offset: int = 0
    ) -> List[Dict]:
        """List model versions with optional filtering."""
        client = await self._get_client()
        try:
            query = client.table("model_versions").select(
                "id, model_name, model_version, model_type, description, provider, accuracy, precision_score, recall, f1_score, is_active, is_production, created_at, updated_at"
            )

            # Apply filters
            for key, value in filters.items():
                query = query.eq(key, value)

            # Apply pagination
            query = query.order("created_at", desc=True).range(
                offset, offset + limit - 1
            )

            result = await query.execute()
            return result.data or []

        except Exception as e:
            logger.error(f"Failed to list model versions: {str(e)}")
            return []

    async def get_model_version(self, model_id: str) -> Optional[Dict]:
        """Get a specific model version by ID."""
        client = await self._get_client()
        try:
            result = await (
                client.table("model_versions")
                .select(
                    "id, model_name, model_version, model_type, description, provider, accuracy, precision_score, recall, f1_score, is_active, is_production, created_at, updated_at"
                )
                .eq("id", model_id)
                .single()
                .execute()
            )
            return result.data
        except Exception as e:
            logger.error(f"Failed to get model version {model_id}: {str(e)}")
            return None

    async def get_model_by_name_and_version(
        self, model_name: str, model_version: str
    ) -> Optional[Dict]:
        """Get a specific model version by name and version."""
        client = await self._get_client()
        try:
            result = await (
                client.table("model_versions")
                .select(
                    "id, model_name, model_version, model_type, description, provider, accuracy, precision_score, recall, f1_score, is_active, is_production, created_at, updated_at"
                )
                .eq("model_name", model_name)
                .eq("model_version", model_version)
                .single()
                .execute()
            )
            return result.data
        except Exception as e:
            logger.error(f"Failed to get model {model_name}/{model_version}: {str(e)}")
            return None

    async def get_model_versions_by_name(self, model_name: str) -> List[Dict]:
        """Get all versions of a specific model."""
        client = await self._get_client()
        try:
            result = await (
                client.table("model_versions")
                .select(
                    "id, model_name, model_version, model_type, description, provider, accuracy, precision_score, recall, f1_score, is_active, is_production, created_at, updated_at"
                )
                .eq("model_name", model_name)
                .order("created_at", desc=True)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to get model versions for {model_name}: {str(e)}")
            return []

    async def get_active_models(self) -> List[Dict]:
        """Get all active model versions."""
        client = await self._get_client()
        try:
            result = await (
                client.table("model_versions")
                .select(
                    "id, model_name, model_version, model_type, description, provider, accuracy, precision_score, recall, f1_score, is_active, is_production, created_at, updated_at"
                )
                .eq("is_active", True)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to get active models: {str(e)}")
            return []

    async def get_production_models(self) -> List[Dict]:
        """Get all production model versions."""
        client = await self._get_client()
        try:
            result = await (
                client.table("model_versions")
                .select(
                    "id, model_name, model_version, model_type, description, provider, accuracy, precision_score, recall, f1_score, is_active, is_production, created_at, updated_at"
                )
                .eq("is_production", True)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to get production models: {str(e)}")
            return []

    async def get_model_types(self) -> List[str]:
        """Get all available model types."""
        client = await self._get_client()
        try:
            result = await (
                client.table("model_versions")
                .select("model_type", distinct=True)
                .execute()
            )
            return [row["model_type"] for row in result.data or []]
        except Exception as e:
            logger.error(f"Failed to get model types: {str(e)}")
            return []

    async def create_model_version(self, model_data: Dict) -> Dict:
        """Create a new model version."""
        client = await self._get_client()
        try:
            # Add required fields
            model_data["created_at"] = datetime.utcnow().isoformat()
            model_data["updated_at"] = datetime.utcnow().isoformat()

            result = await client.table("model_versions").insert(model_data).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Failed to create model version: {str(e)}")
            raise

    async def update_model_version(
        self, model_id: str, update_data: Dict
    ) -> Optional[Dict]:
        """Update a model version."""
        client = await self._get_client()
        try:
            update_data["updated_at"] = datetime.utcnow().isoformat()

            result = await (
                client.table("model_versions")
                .update(update_data)
                .eq("id", model_id)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to update model version {model_id}: {str(e)}")
            return None

    async def delete_model_version(self, model_id: str) -> bool:
        """Delete a model version."""
        client = await self._get_client()
        try:
            result = await (
                client.table("model_versions").delete().eq("id", model_id).execute()
            )
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Failed to delete model version {model_id}: {str(e)}")
            return False

    async def activate_model_version(self, model_id: str, activated_by: str) -> bool:
        """Activate a model version."""
        client = await self._get_client()
        try:
            # First deactivate all other versions of the same model
            model_info = await self.get_model_version(model_id)
            if not model_info:
                return False

            await (
                client.table("model_versions")
                .update(
                    {"is_active": False, "updated_at": datetime.utcnow().isoformat()}
                )
                .eq("model_name", model_info["model_name"])
                .execute()
            )

            # Then activate the specific version
            update_data = {
                "is_active": True,
                "activated_by": activated_by,
                "activated_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }

            result = await (
                client.table("model_versions")
                .update(update_data)
                .eq("id", model_id)
                .execute()
            )
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Failed to activate model version {model_id}: {str(e)}")
            return False

    async def deactivate_model_version(self, model_id: str) -> bool:
        """Deactivate a model version."""
        client = await self._get_client()
        try:
            update_data = {
                "is_active": False,
                "deactivated_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }

            result = await (
                client.table("model_versions")
                .update(update_data)
                .eq("id", model_id)
                .execute()
            )
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Failed to deactivate model version {model_id}: {str(e)}")
            return False

    async def promote_model_to_production(
        self, model_id: str, promoted_by: str
    ) -> bool:
        """Promote a model version to production."""
        client = await self._get_client()
        try:
            # First deactivate all other production versions of the same model
            model_info = await self.get_model_version(model_id)
            if not model_info:
                return False

            await (
                client.table("model_versions")
                .update(
                    {
                        "is_production": False,
                        "updated_at": datetime.utcnow().isoformat(),
                    }
                )
                .eq("model_name", model_info["model_name"])
                .execute()
            )

            # Then promote the specific version
            update_data = {
                "is_production": True,
                "promoted_by": promoted_by,
                "promoted_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }

            result = await (
                client.table("model_versions")
                .update(update_data)
                .eq("id", model_id)
                .execute()
            )
            return len(result.data) > 0
        except Exception as e:
            logger.error(
                f"Failed to promote model version {model_id} to production: {str(e)}"
            )
            return False

    async def deprecate_model_version(
        self, model_id: str, deprecated_by: str, reason: Optional[str] = None
    ) -> bool:
        """Deprecate a model version."""
        client = await self._get_client()
        try:
            update_data = {
                "is_deprecated": True,
                "deprecated_by": deprecated_by,
                "deprecated_at": datetime.utcnow().isoformat(),
                "deprecation_reason": reason,
                "updated_at": datetime.utcnow().isoformat(),
            }

            result = await (
                client.table("model_versions")
                .update(update_data)
                .eq("id", model_id)
                .execute()
            )
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Failed to deprecate model version {model_id}: {str(e)}")
            return False

