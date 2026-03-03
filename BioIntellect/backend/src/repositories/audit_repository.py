"""Audit Repository - Complete Audit and Notification System Implementation."""

from typing import List, Dict, Optional, Any
from datetime import datetime
from src.db.supabase.client import SupabaseProvider
from src.observability.logger import get_logger
from src.services.infrastructure.retry_utils import async_retry

logger = get_logger("repositories.audit")


class AuditRepository:
    """Repository for audit logs, data access logs, and notifications management."""

    def __init__(self):
        pass

    async def _get_client(self):
        return await SupabaseProvider.get_admin()


    async def list_audit_logs(
        self, filters: Dict[str, Any], limit: int = 50, offset: int = 0
    ) -> List[Dict]:
        """List audit logs with optional filtering."""
        client = await self._get_client()
        try:
            # Plan Section 7.B: Specific selectors
            query = client.table("audit_logs").select(
                "id, action, resource_type, resource_id, timestamp, user_id, user_role, description, is_sensitive, is_flagged, created_at"
            )

            # Apply filters
            for key, value in filters.items():
                if key == "is_sensitive":
                    query = query.eq("is_sensitive", value)
                elif key == "is_flagged":
                    query = query.eq("is_flagged", value)
                else:
                    query = query.eq(key, value)

            # Apply pagination
            query = query.order("created_at", desc=True).range(
                offset, offset + limit - 1
            )

            result = await query.execute()
            return result.data or []

        except Exception as e:
            logger.error(f"Failed to list audit logs: {str(e)}")
            return []

    async def get_audit_log(self, log_id: str) -> Optional[Dict]:
        """Get a specific audit log by ID."""
        client = await self._get_client()
        try:
            result = await (
                client.table("audit_logs")
                .select(
                    "id, action, resource_type, resource_id, timestamp, user_id, user_role, description, details, old_values, new_values, changes, ip_address, user_agent, is_sensitive, is_flagged, created_at"
                )
                .eq("id", log_id)
                .single()
                .execute()
            )
            return result.data
        except Exception as e:
            logger.error(f"Failed to get audit log {log_id}: {str(e)}")
            return None

    @async_retry(max_retries=3)
    async def create_audit_log(self, log_data: Dict) -> Dict:
        """Create a new audit log."""
        client = await self._get_client()
        try:
            # Add required fields
            log_data["created_at"] = datetime.utcnow().isoformat()
            log_data["updated_at"] = datetime.utcnow().isoformat()

            result = await client.table("audit_logs").insert(log_data).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Failed to create audit log: {str(e)}")
            raise

    @async_retry(max_retries=3)
    async def flag_audit_log(
        self, log_id: str, flag_reason: str, flagged_by: str
    ) -> bool:
        """Flag an audit log for review."""
        client = await self._get_client()
        try:
            update_data = {
                "is_flagged": True,
                "flag_reason": flag_reason,
                "flagged_by": flagged_by,
                "flagged_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }

            result = await (
                client.table("audit_logs")
                .update(update_data)
                .eq("id", log_id)
                .execute()
            )
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Failed to flag audit log {log_id}: {str(e)}")
            return False

    @async_retry(max_retries=3)
    async def delete_audit_log(self, log_id: str) -> bool:
        """Delete an audit log."""
        client = await self._get_client()
        try:
            result = await (
                client.table("audit_logs").delete().eq("id", log_id).execute()
            )
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Failed to delete audit log {log_id}: {str(e)}")
            return False

    async def get_user_audit_summary(self, user_id: str) -> Dict:
        """Get audit summary for a specific user."""
        client = await self._get_client()
        # Plan Section 11: Parallel Query Execution
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
                "total_logs": results[0].count
                if not isinstance(results[0], Exception)
                else 0,
                "flagged_logs": results[1].count
                if not isinstance(results[1], Exception)
                else 0,
                "sensitive_logs": results[2].count
                if not isinstance(results[2], Exception)
                else 0,
                "last_activity": results[3]
                if not isinstance(results[3], Exception)
                else None,
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
        """Get access summary for a specific patient."""
        client = await self._get_client()
        try:
            # Get data access logs for this patient
            access_logs = await (
                client.table("data_access_logs")
                .select("id, access_type, patient_id, accessed_by, accessed_at")
                .eq("patient_id", patient_id)
                .execute()
            )

            # Count different access types
            access_types: dict[str, int] = {}
            for log in access_logs.data or []:
                access_type = log.get("access_type", "unknown")
                access_types[access_type] = access_types.get(access_type, 0) + 1

            return {
                "patient_id": patient_id,
                "total_accesses": len(access_logs.data or []),
                "access_types": access_types,
                "has_treatment_relationship": await self._check_treatment_relationship(
                    patient_id
                ),
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
        """Get all flagged audit logs."""
        client = await self._get_client()
        try:
            result = await (
                client.table("audit_logs")
                .select(
                    "id, action, resource_type, resource_id, timestamp, user_id, user_role, description, is_flagged, flagged_at, flagged_by"
                )
                .eq("is_flagged", True)
                .order("flagged_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to get flagged logs: {str(e)}")
            return []

    async def get_sensitive_logs(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get all sensitive data access logs."""
        client = await self._get_client()
        try:
            result = await (
                client.table("audit_logs")
                .select(
                    "id, action, resource_type, resource_id, timestamp, user_id, user_role, description, is_sensitive"
                )
                .eq("is_sensitive", True)
                .order("created_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to get sensitive logs: {str(e)}")
            return []

    # â”پâ”پâ”پâ”پ DATA ACCESS LOGS â”پâ”پâ”پâ”پ

    async def list_data_access_logs(
        self, filters: Dict[str, Any], limit: int = 50, offset: int = 0
    ) -> List[Dict]:
        """List data access logs with optional filtering."""
        client = await self._get_client()
        try:
            # Plan Section 7.B: Specific selectors
            query = client.table("data_access_logs").select(
                "id, access_type, accessed_table, accessed_record_id, accessed_at, user_id, user_role, patient_id"
            )

            # Apply filters
            for key, value in filters.items():
                query = query.eq(key, value)

            # Apply pagination
            query = query.order("accessed_at", desc=True).range(
                offset, offset + limit - 1
            )

            result = await query.execute()
            return result.data or []

        except Exception as e:
            logger.error(f"Failed to list data access logs: {str(e)}")
            return []

    async def get_data_access_log(self, log_id: str) -> Optional[Dict]:
        """Get a specific data access log by ID."""
        client = await self._get_client()
        try:
            result = await (
                client.table("data_access_logs")
                .select(
                    "id, access_type, accessed_table, accessed_record_id, accessed_at, user_id, user_role, patient_id, details, created_at"
                )
                .eq("id", log_id)
                .single()
                .execute()
            )
            return result.data
        except Exception as e:
            logger.error(f"Failed to get data access log {log_id}: {str(e)}")
            return None

    @async_retry(max_retries=3)
    async def create_data_access_log(self, log_data: Dict) -> Dict:
        """Create a new data access log."""
        client = await self._get_client()
        try:
            # Add required fields
            log_data["accessed_at"] = datetime.utcnow().isoformat()
            log_data["created_at"] = datetime.utcnow().isoformat()

            result = await client.table("data_access_logs").insert(log_data).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Failed to create data access log: {str(e)}")
            raise

    # â”پâ”پâ”پâ”پ NOTIFICATIONS â”پâ”پâ”پâ”پ

    async def list_notifications(
        self, filters: Dict[str, Any], limit: int = 50, offset: int = 0
    ) -> List[Dict]:
        """List notifications with optional filtering."""
        client = await self._get_client()
        try:
            # Plan Section 7.B: Specific selectors
            query = client.table("notifications").select(
                "id, user_id, type, title, message, is_read, is_archived, created_at"
            )

            # Apply filters
            for key, value in filters.items():
                if key == "is_read":
                    query = query.eq("is_read", value)
                elif key == "is_archived":
                    query = query.eq("is_archived", value)
                else:
                    query = query.eq(key, value)

            # Apply pagination
            query = query.order("created_at", desc=True).range(
                offset, offset + limit - 1
            )

            result = await query.execute()
            return result.data or []

        except Exception as e:
            logger.error(f"Failed to list notifications: {str(e)}")
            return []

    async def get_notification(self, notification_id: str) -> Optional[Dict]:
        """Get a specific notification by ID."""
        client = await self._get_client()
        try:
            result = await (
                client.table("notifications")
                .select(
                    "id, user_id, type, title, message, is_read, is_archived, created_at, updated_at"
                )
                .eq("id", notification_id)
                .single()
                .execute()
            )
            return result.data
        except Exception as e:
            logger.error(f"Failed to get notification {notification_id}: {str(e)}")
            return None

    @async_retry(max_retries=3)
    async def create_notification(self, notification_data: Dict) -> Dict:
        """Create a new notification."""
        client = await self._get_client()
        try:
            # Add required fields
            notification_data["created_at"] = datetime.utcnow().isoformat()
            notification_data["updated_at"] = datetime.utcnow().isoformat()

            result = await (
                client.table("notifications").insert(notification_data).execute()
            )
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Failed to create notification: {str(e)}")
            raise

    @async_retry(max_retries=3)
    async def update_notification(
        self, notification_id: str, update_data: Dict
    ) -> Optional[Dict]:
        """Update a notification."""
        client = await self._get_client()
        try:
            update_data["updated_at"] = datetime.utcnow().isoformat()

            result = await (
                client.table("notifications")
                .update(update_data)
                .eq("id", notification_id)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to update notification {notification_id}: {str(e)}")
            return None

    @async_retry(max_retries=3)
    async def delete_notification(self, notification_id: str) -> bool:
        """Delete a notification."""
        client = await self._get_client()
        try:
            result = await (
                client.table("notifications")
                .delete()
                .eq("id", notification_id)
                .execute()
            )
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Failed to delete notification {notification_id}: {str(e)}")
            return False

    async def get_unread_notification_count(self, user_id: str) -> int:
        """Get unread notification count for a user."""
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
        """Mark multiple notifications as read."""
        client = await self._get_client()
        try:
            update_data = {
                "is_read": True,
                "read_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }

            result = await (
                client.table("notifications")
                .update(update_data)
                .in_("id", notification_ids)
                .eq("user_id", user_id)
                .execute()
            )
            return len(result.data) > 0
        except Exception as e:
            logger.error(
                f"Failed to mark notifications as read for user {user_id}: {str(e)}"
            )
            return False

    @async_retry(max_retries=3)
    async def mark_all_notifications_as_read(self, user_id: str) -> int:
        """Mark all notifications as read for a user."""
        client = await self._get_client()
        try:
            update_data = {
                "is_read": True,
                "read_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }

            result = await (
                client.table("notifications")
                .update(update_data)
                .eq("user_id", user_id)
                .eq("is_read", False)
                .execute()
            )
            return len(result.data)
        except Exception as e:
            logger.error(
                f"Failed to mark all notifications as read for user {user_id}: {str(e)}"
            )
            return 0

    # â”پâ”پâ”پâ”پ HELPER METHODS â”پâ”پâ”پâ”پ

    async def _get_last_activity(self, user_id: str) -> Optional[str]:
        """Get the last activity timestamp for a user."""
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

    async def _check_treatment_relationship(self, patient_id: str) -> bool:
        """Check if there's a treatment relationship for the patient."""
        try:
            # This would typically check a treatment_relationships table
            # For now, return False as a placeholder
            return False
        except Exception:
            return False

