"""Logging Repository - Database operations for audit logs."""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from src.db.supabase.client import SupabaseProvider
from src.observability.logger import get_logger

logger = get_logger("repositories.logging")
unsupported_audit_columns: set[str] = set()


class LoggingRepository:
    """Repository for audit log operations."""

    def __init__(self):
        pass

    async def _get_admin(self):
        return await SupabaseProvider.get_admin()

    async def create_audit_log(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new audit log entry."""
        client = await self._get_admin()
        try:
            log_data = {
                "user_id": user_id,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "details": details or {},
                "ip_address": ip_address,
                "user_agent": user_agent,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Handle schema drift across environments (e.g. missing optional columns).
            payload = dict(log_data)
            for col in unsupported_audit_columns:
                payload.pop(col, None)

            response = None
            while True:
                try:
                    response = await client.table("audit_logs").insert(payload).execute()
                    break
                except Exception as insert_err:
                    error_text = str(insert_err)
                    if "PGRST204" in error_text:
                        marker = "Could not find the '"
                        unknown_column = None
                        if marker in error_text:
                            unknown_column = error_text.split(marker, 1)[1].split(
                                "'", 1
                            )[0]

                        if unknown_column and unknown_column in payload:
                            unsupported_audit_columns.add(unknown_column)
                            payload.pop(unknown_column, None)
                            logger.warning(
                                f"audit_logs missing column '{unknown_column}', retrying without it"
                            )
                            continue
                    raise

            if response.data:
                logger.info(f"Audit log created: {action} by user {user_id}")
                return {
                    "success": True,
                    "log_id": response.data[0]["id"],
                    "message": "Audit log created successfully",
                }
            else:
                logger.error(f"Failed to create audit log for action: {action}")
                return {"success": False, "message": "Failed to create audit log"}

        except Exception as e:
            logger.error(f"Error creating audit log: {str(e)}")
            return {"success": False, "message": f"Error creating audit log: {str(e)}"}

    async def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Get audit logs with filtering options."""
        client = await self._get_admin()
        try:
            query = client.table("audit_logs").select(
                "id, action, resource_type, resource_id, details, timestamp, user_id, ip_address, user_agent"
            )

            if user_id:
                query = query.eq("user_id", user_id)

            if action:
                query = query.eq("action", action)

            if resource_type:
                query = query.eq("resource_type", resource_type)

            if start_date:
                query = query.gte("timestamp", start_date)

            if end_date:
                query = query.lte("timestamp", end_date)

            query = query.order("timestamp", desc=True).range(
                offset, offset + limit - 1
            )

            response = await query.execute()

            if response.data:
                logger.info(f"Retrieved {len(response.data)} audit logs")
                return {
                    "success": True,
                    "data": response.data,
                    "count": len(response.data),
                }
            else:
                logger.info("No audit logs found")
                return {"success": True, "data": [], "count": 0}
        except Exception:
            # Backward-compatible fallback for environments still using system_logs.
            try:
                legacy_query = client.table("system_logs").select(
                    "id, action, resource_type, resource_id, details, timestamp, user_id, ip_address, user_agent"
                )
                if user_id:
                    legacy_query = legacy_query.eq("user_id", user_id)
                if action:
                    legacy_query = legacy_query.eq("action", action)
                if resource_type:
                    legacy_query = legacy_query.eq("resource_type", resource_type)
                if start_date:
                    legacy_query = legacy_query.gte("timestamp", start_date)
                if end_date:
                    legacy_query = legacy_query.lte("timestamp", end_date)

                legacy_response = await legacy_query.order("timestamp", desc=True).range(
                    offset, offset + limit - 1
                ).execute()

                data = legacy_response.data or []
                return {"success": True, "data": data, "count": len(data)}
            except Exception as e:
                logger.error(f"Error retrieving audit logs: {str(e)}")
                return {
                    "success": False,
                    "message": f"Error retrieving audit logs: {str(e)}",
                }

    async def get_user_activity_summary(self, user_id: str) -> Dict[str, Any]:
        """Get activity summary for a specific user."""
        client = await self._get_admin()
        try:
            # Get recent activity count by action type
            response = await (
                client.table("audit_logs")
                .select("action, count(*)")
                .eq("user_id", user_id)
                .group("action")
                .execute()
            )

            if response.data:
                logger.info(f"Retrieved activity summary for user {user_id}")
                return {"success": True, "data": response.data}
            else:
                logger.info(f"No activity found for user {user_id}")
                return {"success": True, "data": []}

        except Exception as e:
            logger.error(f"Error retrieving user activity summary: {str(e)}")
            return {
                "success": False,
                "message": f"Error retrieving user activity summary: {str(e)}",
            }

    async def get_system_activity_summary(self) -> Dict[str, Any]:
        """Get system-wide activity summary."""
        client = await self._get_admin()
        try:
            # Get system activity stats
            response = await (
                client.table("audit_logs")
                .select("action, count(*)")
                .group("action")
                .execute()
            )

            if response.data:
                logger.info("Retrieved system activity summary")
                return {"success": True, "data": response.data}
            else:
                logger.info("No system activity data available")
                return {"success": True, "data": []}

        except Exception as e:
            logger.error(f"Error retrieving system activity summary: {str(e)}")
            return {
                "success": False,
                "message": f"Error retrieving system activity summary: {str(e)}",
            }

    async def cleanup_old_logs(self, days_to_keep: int = 90) -> Dict[str, Any]:
        """Clean up audit logs older than specified days."""
        client = await self._get_admin()
        try:
            # Calculate cutoff date as ISO string
            cutoff_date = (datetime.utcnow() - timedelta(days=days_to_keep)).isoformat()

            # Delete old logs directly
            response = await (
                client.table("audit_logs")
                .delete()
                .lt("timestamp", cutoff_date)
                .execute()
            )

            if response.data:
                deleted_count = len(response.data)
                logger.info(f"Cleaned up {deleted_count} old audit logs")
                return {
                    "success": True,
                    "deleted_count": deleted_count,
                    "message": f"Successfully deleted {deleted_count} old audit logs",
                }
            else:
                logger.info("No old audit logs to clean up")
                return {
                    "success": True,
                    "deleted_count": 0,
                    "message": "No old audit logs found",
                }

        except Exception as e:
            logger.error(f"Error cleaning up old audit logs: {str(e)}")
            return {
                "success": False,
                "message": f"Error cleaning up old audit logs: {str(e)}",
            }

