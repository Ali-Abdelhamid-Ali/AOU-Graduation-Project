"""Audit Repository - Complete Audit and Notification System Implementation."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from src.db.supabase.client import SupabaseProvider
from src.observability.logger import get_logger
from src.repositories.schema_compat import (
    build_audit_log_payload,
    build_data_access_log_payload,
    coerce_notification_payload,
    normalize_audit_log,
    normalize_data_access_log,
    normalize_notification_record,
)
from src.services.infrastructure.retry_utils import async_retry

logger = get_logger("repositories.audit")


class AuditRepository:
    """Repository for audit logs, data access logs, and notifications management."""

    async def _get_client(self):
        return await SupabaseProvider.get_admin()

    async def list_audit_logs(
        self, filters: Dict[str, Any], limit: int = 50, offset: int = 0
    ) -> List[Dict]:
        client = await self._get_client()
        try:
            query = client.table("audit_logs").select(
                "id, action, resource_type, resource_id, user_id, user_role, description, old_values, new_values, changes, ip_address, user_agent, is_sensitive, is_flagged, flag_reason, created_at"
            )
            for key, value in filters.items():
                query = query.eq(key, value)
            result = await query.order("created_at", desc=True).range(
                offset, offset + limit - 1
            ).execute()
            return [normalize_audit_log(row) for row in (result.data or [])]
        except Exception as e:
            logger.error(f"Failed to list audit logs: {str(e)}")
            return []

    async def get_audit_log(self, log_id: str) -> Optional[Dict]:
        client = await self._get_client()
        try:
            result = await (
                client.table("audit_logs")
                .select(
                    "id, action, resource_type, resource_id, user_id, user_role, description, old_values, new_values, changes, ip_address, user_agent, is_sensitive, is_flagged, flag_reason, created_at"
                )
                .eq("id", log_id)
                .single()
                .execute()
            )
            return normalize_audit_log(result.data)
        except Exception as e:
            logger.error(f"Failed to get audit log {log_id}: {str(e)}")
            return None

    @async_retry(max_retries=3)
    async def create_audit_log(self, log_data: Dict) -> Dict:
        client = await self._get_client()
        try:
            payload = build_audit_log_payload(log_data)
            payload.setdefault("created_at", datetime.utcnow().isoformat())
            result = await client.table("audit_logs").insert(payload).execute()
            return normalize_audit_log(result.data[0]) if result.data else {}
        except Exception as e:
            logger.error(f"Failed to create audit log: {str(e)}")
            raise

    @async_retry(max_retries=3)
    async def flag_audit_log(
        self, log_id: str, flag_reason: str, flagged_by: str
    ) -> bool:
        client = await self._get_client()
        try:
            update_data = {
                "is_flagged": True,
                "flag_reason": f"{flag_reason} (flagged by {flagged_by})",
            }
            result = await (
                client.table("audit_logs")
                .update(update_data)
                .eq("id", log_id)
                .execute()
            )
            return len(result.data or []) > 0
        except Exception as e:
            logger.error(f"Failed to flag audit log {log_id}: {str(e)}")
            return False

    @async_retry(max_retries=3)
    async def delete_audit_log(self, log_id: str) -> bool:
        client = await self._get_client()
        try:
            result = await client.table("audit_logs").delete().eq("id", log_id).execute()
            return len(result.data or []) > 0
        except Exception as e:
            logger.error(f"Failed to delete audit log {log_id}: {str(e)}")
            return False

    async def get_user_audit_summary(self, user_id: str) -> Dict:
        client = await self._get_client()
        import asyncio

        try:
            results = await asyncio.gather(
                client.table("audit_logs")
                .select("id", count="exact")
                .eq("user_id", user_id)
                .execute(),
                client.table("audit_logs")
                .select("id", count="exact")
                .eq("user_id", user_id)
                .eq("is_flagged", True)
                .execute(),
                client.table("audit_logs")
                .select("id", count="exact")
                .eq("user_id", user_id)
                .eq("is_sensitive", True)
                .execute(),
                self._get_last_activity(user_id),
                return_exceptions=True,
            )

            return {
                "user_id": user_id,
                "total_logs": results[0].count if not isinstance(results[0], Exception) else 0,
                "flagged_logs": results[1].count if not isinstance(results[1], Exception) else 0,
                "sensitive_logs": results[2].count if not isinstance(results[2], Exception) else 0,
                "last_activity": results[3] if not isinstance(results[3], Exception) else None,
            }
        except Exception as e:
            logger.error(f"Failed to get audit summary for user {user_id}: {str(e)}")
            return {
                "user_id": user_id,
                "total_logs": 0,
                "flagged_logs": 0,
                "sensitive_logs": 0,
                "last_activity": None,
            }

    async def get_patient_access_summary(self, patient_id: str) -> Dict:
        client = await self._get_client()
        try:
            access_logs = await (
                client.table("data_access_logs")
                .select(
                    "id, access_type, user_id, patient_id, access_reason, relationship_type, has_treatment_relationship, created_at"
                )
                .eq("patient_id", patient_id)
                .execute()
            )

            access_types: Dict[str, int] = {}
            treatment_relationship = False
            for log in access_logs.data or []:
                access_type = log.get("access_type", "unknown")
                access_types[access_type] = access_types.get(access_type, 0) + 1
                treatment_relationship = treatment_relationship or bool(
                    log.get("has_treatment_relationship")
                )

            return {
                "patient_id": patient_id,
                "total_accesses": len(access_logs.data or []),
                "access_types": access_types,
                "has_treatment_relationship": treatment_relationship,
            }
        except Exception as e:
            logger.error(
                f"Failed to get access summary for patient {patient_id}: {str(e)}"
            )
            return {
                "patient_id": patient_id,
                "total_accesses": 0,
                "access_types": {},
                "has_treatment_relationship": False,
            }

    async def get_flagged_logs(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        try:
            return await self.list_audit_logs(
                {"is_flagged": True}, limit=limit, offset=offset
            )
        except Exception as e:
            logger.error(f"Failed to get flagged logs: {str(e)}")
            return []

    async def get_sensitive_logs(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        try:
            return await self.list_audit_logs(
                {"is_sensitive": True}, limit=limit, offset=offset
            )
        except Exception as e:
            logger.error(f"Failed to get sensitive logs: {str(e)}")
            return []

    async def list_data_access_logs(
        self, filters: Dict[str, Any], limit: int = 50, offset: int = 0
    ) -> List[Dict]:
        client = await self._get_client()
        try:
            query = client.table("data_access_logs").select(
                "id, access_type, accessed_table, accessed_record_id, user_id, user_role, patient_id, access_reason, has_treatment_relationship, relationship_type, hospital_id, case_id, conversation_id, ip_address, user_agent, created_at"
            )
            for key, value in filters.items():
                query = query.eq(key, value)
            result = await query.order("created_at", desc=True).range(
                offset, offset + limit - 1
            ).execute()
            return [normalize_data_access_log(row) for row in (result.data or [])]
        except Exception as e:
            logger.error(f"Failed to list data access logs: {str(e)}")
            return []

    async def get_data_access_log(self, log_id: str) -> Optional[Dict]:
        client = await self._get_client()
        try:
            result = await (
                client.table("data_access_logs")
                .select(
                    "id, access_type, accessed_table, accessed_record_id, user_id, user_role, patient_id, access_reason, has_treatment_relationship, relationship_type, hospital_id, case_id, conversation_id, ip_address, user_agent, created_at"
                )
                .eq("id", log_id)
                .single()
                .execute()
            )
            return normalize_data_access_log(result.data)
        except Exception as e:
            logger.error(f"Failed to get data access log {log_id}: {str(e)}")
            return None

    @async_retry(max_retries=3)
    async def create_data_access_log(self, log_data: Dict) -> Dict:
        client = await self._get_client()
        try:
            payload = build_data_access_log_payload(log_data)
            payload.setdefault("created_at", datetime.utcnow().isoformat())
            result = await client.table("data_access_logs").insert(payload).execute()
            return normalize_data_access_log(result.data[0]) if result.data else {}
        except Exception as e:
            logger.error(f"Failed to create data access log: {str(e)}")
            raise

    async def list_notifications(
        self, filters: Dict[str, Any], limit: int = 50, offset: int = 0
    ) -> List[Dict]:
        client = await self._get_client()
        try:
            query = client.table("notifications").select("*")
            for key, value in filters.items():
                if key == "notification_type":
                    query = query.eq("notification_type", coerce_notification_payload({"notification_type": value})["notification_type"])
                else:
                    query = query.eq(key, value)
            result = await query.order("created_at", desc=True).range(
                offset, offset + limit - 1
            ).execute()
            return [normalize_notification_record(row) for row in (result.data or [])]
        except Exception as e:
            logger.error(f"Failed to list notifications: {str(e)}")
            return []

    async def get_notification(self, notification_id: str) -> Optional[Dict]:
        client = await self._get_client()
        try:
            result = await (
                client.table("notifications")
                .select("*")
                .eq("id", notification_id)
                .single()
                .execute()
            )
            return normalize_notification_record(result.data)
        except Exception as e:
            logger.error(f"Failed to get notification {notification_id}: {str(e)}")
            return None

    @async_retry(max_retries=3)
    async def create_notification(self, notification_data: Dict) -> Dict:
        client = await self._get_client()
        try:
            payload = coerce_notification_payload(notification_data)
            payload.setdefault("created_at", datetime.utcnow().isoformat())
            result = await client.table("notifications").insert(payload).execute()
            return normalize_notification_record(result.data[0]) if result.data else {}
        except Exception as e:
            logger.error(f"Failed to create notification: {str(e)}")
            raise

    @async_retry(max_retries=3)
    async def update_notification(
        self, notification_id: str, update_data: Dict
    ) -> Optional[Dict]:
        client = await self._get_client()
        try:
            payload = coerce_notification_payload(update_data)
            result = await (
                client.table("notifications")
                .update(payload)
                .eq("id", notification_id)
                .execute()
            )
            return normalize_notification_record(result.data[0]) if result.data else None
        except Exception as e:
            logger.error(f"Failed to update notification {notification_id}: {str(e)}")
            return None

    @async_retry(max_retries=3)
    async def delete_notification(self, notification_id: str) -> bool:
        client = await self._get_client()
        try:
            result = await (
                client.table("notifications")
                .delete()
                .eq("id", notification_id)
                .execute()
            )
            return len(result.data or []) > 0
        except Exception as e:
            logger.error(f"Failed to delete notification {notification_id}: {str(e)}")
            return False

    async def get_unread_notification_count(self, user_id: str) -> int:
        client = await self._get_client()
        try:
            result = await (
                client.table("notifications")
                .select("id", count="exact")
                .eq("user_id", user_id)
                .eq("is_read", False)
                .execute()
            )
            return result.count or 0
        except Exception as e:
            logger.error(
                f"Failed to get unread notification count for user {user_id}: {str(e)}"
            )
            return 0

    @async_retry(max_retries=3)
    async def mark_notifications_as_read(
        self, notification_ids: List[str], user_id: str
    ) -> bool:
        client = await self._get_client()
        try:
            update_data = {
                "is_read": True,
                "read_at": datetime.utcnow().isoformat(),
            }
            result = await (
                client.table("notifications")
                .update(update_data)
                .in_("id", notification_ids)
                .eq("user_id", user_id)
                .execute()
            )
            return len(result.data or []) > 0
        except Exception as e:
            logger.error(
                f"Failed to mark notifications as read for user {user_id}: {str(e)}"
            )
            return False

    @async_retry(max_retries=3)
    async def mark_all_notifications_as_read(self, user_id: str) -> int:
        client = await self._get_client()
        try:
            result = await (
                client.table("notifications")
                .update(
                    {"is_read": True, "read_at": datetime.utcnow().isoformat()}
                )
                .eq("user_id", user_id)
                .eq("is_read", False)
                .execute()
            )
            return len(result.data or [])
        except Exception as e:
            logger.error(
                f"Failed to mark all notifications as read for user {user_id}: {str(e)}"
            )
            return 0

    async def _get_last_activity(self, user_id: str) -> Optional[str]:
        client = await self._get_client()
        try:
            result = await (
                client.table("audit_logs")
                .select("created_at")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            return result.data[0]["created_at"] if result.data else None
        except Exception:
            return None
