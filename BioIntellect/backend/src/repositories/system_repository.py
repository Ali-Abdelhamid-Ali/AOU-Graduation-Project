"""System Repository - Complete System Settings and Model Version Management Implementation."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from src.db.supabase.client import SupabaseProvider
from src.observability.logger import get_logger
from src.repositories.schema_compat import sanitize_for_table

logger = get_logger("repositories.system")


class SystemRepository:
    """Repository for system settings and model version management."""

    async def _get_client(self):
        return await SupabaseProvider.get_admin()

    @staticmethod
    def _normalize_scope_id(value: Any) -> Optional[str]:
        if value in (None, "", "global"):
            return None
        try:
            return str(UUID(str(value)))
        except (TypeError, ValueError):
            return None

    def _prepare_setting_payload(self, setting_data: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(setting_data or {})
        payload["scope_id"] = self._normalize_scope_id(payload.get("scope_id"))
        return sanitize_for_table("system_settings", payload)

    def _prepare_model_payload(self, model_data: Dict[str, Any]) -> Dict[str, Any]:
        return sanitize_for_table("model_versions", dict(model_data or {}))

    async def get_db_health_summary(self) -> Dict[str, Any]:
        client = await self._get_client()
        try:
            results = await asyncio.gather(
                client.table("user_roles").select("id", count="exact").limit(1).execute(),
                client.table("audit_logs").select("id", count="exact").limit(1).execute(),
                client.table("medical_cases").select("id", count="exact").limit(1).execute(),
                return_exceptions=True,
            )
            return {
                "users_count": results[0].count if not isinstance(results[0], Exception) else 0,
                "logs_count": results[1].count if not isinstance(results[1], Exception) else 0,
                "cases_count": results[2].count if not isinstance(results[2], Exception) else 0,
                "status": "healthy"
                if all(not isinstance(r, Exception) for r in results)
                else "degraded",
            }
        except Exception as e:
            logger.error(f"Failed to gather DB health summary: {str(e)}")
            raise

    async def check_admin_connection(self) -> bool:
        client = await self._get_client()
        await client.table("administrators").select("id").limit(1).execute()
        return True

    async def check_auth_service_connection(self) -> bool:
        client = await self._get_client()
        await client.auth.get_session()
        return True

    async def check_system_settings_connection(self) -> bool:
        client = await self._get_client()
        await client.table("system_settings").select("id").limit(1).execute()
        return True

    async def list_system_settings(
        self, filters: Dict[str, Any], limit: int = 50, offset: int = 0
    ) -> List[Dict]:
        client = await self._get_client()
        try:
            query = client.table("system_settings").select(
                "id, scope, scope_id, setting_key, setting_value, setting_type, description, is_sensitive, created_by, updated_by, created_at, updated_at"
            )
            for key, value in filters.items():
                if key == "scope_id":
                    normalized_scope_id = self._normalize_scope_id(value)
                    if normalized_scope_id is None:
                        continue
                    query = query.eq("scope_id", normalized_scope_id)
                else:
                    query = query.eq(key, value)
            result = await query.order("created_at", desc=True).range(
                offset, offset + limit - 1
            ).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to list system settings: {str(e)}")
            return []

    async def get_system_setting(self, setting_id: str) -> Optional[Dict]:
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
        client = await self._get_client()
        try:
            query = (
                client.table("system_settings")
                .select(
                    "id, scope, scope_id, setting_key, setting_value, setting_type, description, is_sensitive, created_by, updated_by, created_at, updated_at"
                )
                .eq("scope", scope)
            )
            normalized_scope_id = self._normalize_scope_id(scope_id)
            if normalized_scope_id:
                query = query.eq("scope_id", normalized_scope_id)
            result = await query.execute()
            return result.data or []
        except Exception as e:
            logger.error(
                f"Failed to get settings for scope {scope}/{scope_id}: {str(e)}"
            )
            return []

    async def get_global_settings(self) -> List[Dict]:
        return await self.get_settings_by_scope("global", "")

    async def get_sensitive_settings(self) -> List[Dict]:
        return await self.list_system_settings({"is_sensitive": True})

    async def create_system_setting(self, setting_data: Dict) -> Dict:
        client = await self._get_client()
        try:
            payload = self._prepare_setting_payload(setting_data)
            payload.setdefault("created_at", datetime.utcnow().isoformat())
            payload.setdefault("updated_at", datetime.utcnow().isoformat())
            result = await client.table("system_settings").insert(payload).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Failed to create system setting: {str(e)}")
            raise

    async def update_system_setting(
        self, setting_id: str, update_data: Dict
    ) -> Optional[Dict]:
        client = await self._get_client()
        try:
            payload = self._prepare_setting_payload(update_data)
            payload["updated_at"] = datetime.utcnow().isoformat()
            result = await (
                client.table("system_settings")
                .update(payload)
                .eq("id", setting_id)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to update system setting {setting_id}: {str(e)}")
            return None

    async def delete_system_setting(self, setting_id: str) -> bool:
        client = await self._get_client()
        try:
            result = await (
                client.table("system_settings").delete().eq("id", setting_id).execute()
            )
            return len(result.data or []) > 0
        except Exception as e:
            logger.error(f"Failed to delete system setting {setting_id}: {str(e)}")
            return False

    async def get_setting_keys(self) -> List[str]:
        client = await self._get_client()
        try:
            result = await client.table("system_settings").select("setting_key").execute()
            return sorted({row["setting_key"] for row in (result.data or []) if row.get("setting_key")})
        except Exception as e:
            logger.error(f"Failed to get setting keys: {str(e)}")
            return []

    async def list_model_versions(
        self, filters: Dict[str, Any], limit: int = 50, offset: int = 0
    ) -> List[Dict]:
        client = await self._get_client()
        try:
            query = client.table("model_versions").select(
                "id, model_name, model_version, model_type, description, provider, accuracy, precision_score, recall, f1_score, validation_dataset, default_config, is_active, is_production, deployed_at, deprecated_at, created_by, created_at, updated_at"
            )
            for key, value in filters.items():
                query = query.eq(key, value)
            result = await query.order("created_at", desc=True).range(
                offset, offset + limit - 1
            ).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to list model versions: {str(e)}")
            return []

    async def get_model_version(self, model_id: str) -> Optional[Dict]:
        client = await self._get_client()
        try:
            result = await (
                client.table("model_versions")
                .select(
                    "id, model_name, model_version, model_type, description, provider, accuracy, precision_score, recall, f1_score, validation_dataset, default_config, is_active, is_production, deployed_at, deprecated_at, created_by, created_at, updated_at"
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
        client = await self._get_client()
        try:
            result = await (
                client.table("model_versions")
                .select(
                    "id, model_name, model_version, model_type, description, provider, accuracy, precision_score, recall, f1_score, validation_dataset, default_config, is_active, is_production, deployed_at, deprecated_at, created_by, created_at, updated_at"
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
        return await self.list_model_versions({"model_name": model_name})

    async def get_active_models(self) -> List[Dict]:
        return await self.list_model_versions({"is_active": True})

    async def get_production_models(self) -> List[Dict]:
        return await self.list_model_versions({"is_production": True})

    async def get_model_types(self) -> List[str]:
        client = await self._get_client()
        try:
            result = await client.table("model_versions").select("model_type").execute()
            return sorted({row["model_type"] for row in (result.data or []) if row.get("model_type")})
        except Exception as e:
            logger.error(f"Failed to get model types: {str(e)}")
            return []

    async def create_model_version(self, model_data: Dict) -> Dict:
        client = await self._get_client()
        try:
            payload = self._prepare_model_payload(model_data)
            payload.setdefault("created_at", datetime.utcnow().isoformat())
            payload.setdefault("updated_at", datetime.utcnow().isoformat())
            result = await client.table("model_versions").insert(payload).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Failed to create model version: {str(e)}")
            raise

    async def update_model_version(
        self, model_id: str, update_data: Dict
    ) -> Optional[Dict]:
        client = await self._get_client()
        try:
            payload = self._prepare_model_payload(update_data)
            payload["updated_at"] = datetime.utcnow().isoformat()
            result = await (
                client.table("model_versions")
                .update(payload)
                .eq("id", model_id)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to update model version {model_id}: {str(e)}")
            return None

    async def delete_model_version(self, model_id: str) -> bool:
        client = await self._get_client()
        try:
            result = await (
                client.table("model_versions").delete().eq("id", model_id).execute()
            )
            return len(result.data or []) > 0
        except Exception as e:
            logger.error(f"Failed to delete model version {model_id}: {str(e)}")
            return False

    async def activate_model_version(self, model_id: str, activated_by: str) -> bool:
        client = await self._get_client()
        try:
            model_info = await self.get_model_version(model_id)
            if not model_info:
                return False

            await (
                client.table("model_versions")
                .update({"is_active": False, "updated_at": datetime.utcnow().isoformat()})
                .eq("model_name", model_info["model_name"])
                .execute()
            )

            update_data = self._prepare_model_payload(
                {
                    "is_active": True,
                    "updated_at": datetime.utcnow().isoformat(),
                    "created_by": activated_by if model_info.get("created_by") is None else model_info.get("created_by"),
                }
            )
            result = await (
                client.table("model_versions")
                .update(update_data)
                .eq("id", model_id)
                .execute()
            )
            return len(result.data or []) > 0
        except Exception as e:
            logger.error(f"Failed to activate model version {model_id}: {str(e)}")
            return False

    async def deactivate_model_version(self, model_id: str) -> bool:
        client = await self._get_client()
        try:
            result = await (
                client.table("model_versions")
                .update(
                    {
                        "is_active": False,
                        "updated_at": datetime.utcnow().isoformat(),
                    }
                )
                .eq("id", model_id)
                .execute()
            )
            return len(result.data or []) > 0
        except Exception as e:
            logger.error(f"Failed to deactivate model version {model_id}: {str(e)}")
            return False

    async def promote_model_to_production(
        self, model_id: str, promoted_by: str
    ) -> bool:
        client = await self._get_client()
        try:
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

            update_data = self._prepare_model_payload(
                {
                    "is_production": True,
                    "deployed_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                    "created_by": promoted_by if model_info.get("created_by") is None else model_info.get("created_by"),
                }
            )
            result = await (
                client.table("model_versions")
                .update(update_data)
                .eq("id", model_id)
                .execute()
            )
            return len(result.data or []) > 0
        except Exception as e:
            logger.error(
                f"Failed to promote model version {model_id} to production: {str(e)}"
            )
            return False

    async def deprecate_model_version(
        self, model_id: str, deprecated_by: str, reason: Optional[str] = None
    ) -> bool:
        client = await self._get_client()
        try:
            model = await self.get_model_version(model_id)
            if not model:
                return False

            description = model.get("description") or ""
            if reason:
                description = (
                    f"{description}\nDeprecated by {deprecated_by}: {reason}".strip()
                )

            update_data = self._prepare_model_payload(
                {
                    "is_active": False,
                    "deprecated_at": datetime.utcnow().isoformat(),
                    "description": description,
                    "updated_at": datetime.utcnow().isoformat(),
                }
            )
            result = await (
                client.table("model_versions")
                .update(update_data)
                .eq("id", model_id)
                .execute()
            )
            return len(result.data or []) > 0
        except Exception as e:
            logger.error(f"Failed to deprecate model version {model_id}: {str(e)}")
            return False
