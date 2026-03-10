"""Logging Repository - Database operations for audit logs."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from src.db.supabase.client import SupabaseProvider
from src.observability.logger import get_logger
from src.repositories.schema_compat import build_audit_log_payload, normalize_audit_log

logger = get_logger("repositories.logging")


class LoggingRepository:
    """Repository for audit log operations."""

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
        client = await self._get_admin()
        try:
            payload = build_audit_log_payload(
                {
                    "user_id": user_id,
                    "action": action,
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "details": details or {},
                    "ip_address": ip_address,
                    "user_agent": user_agent,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
            response = await client.table("audit_logs").insert(payload).execute()
            if response.data:
                return {
                    "success": True,
                    "log_id": response.data[0]["id"],
                    "message": "Audit log created successfully",
                }
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
        client = await self._get_admin()
        try:
            query = client.table("audit_logs").select(
                "id, action, resource_type, resource_id, changes, created_at, user_id, ip_address, user_agent, user_role, description, is_sensitive, is_flagged, flag_reason"
            )

            if user_id:
                query = query.eq("user_id", user_id)
            if action:
                query = query.eq("action", action)
            if resource_type:
                query = query.eq("resource_type", resource_type)
            if start_date:
                query = query.gte("created_at", start_date)
            if end_date:
                query = query.lte("created_at", end_date)

            response = await query.order("created_at", desc=True).range(
                offset, offset + limit - 1
            ).execute()

            data = [normalize_audit_log(row) for row in (response.data or [])]
            return {"success": True, "data": data, "count": len(data)}
        except Exception as e:
            logger.error(f"Error retrieving audit logs: {str(e)}")
            return {
                "success": False,
                "message": f"Error retrieving audit logs: {str(e)}",
            }

    async def get_user_activity_summary(self, user_id: str) -> Dict[str, Any]:
        client = await self._get_admin()
        try:
            response = await (
                client.table("audit_logs")
                .select("action")
                .eq("user_id", user_id)
                .execute()
            )
            counter = Counter(row.get("action", "unknown") for row in (response.data or []))
            data = [{"action": action, "count": count} for action, count in counter.items()]
            return {"success": True, "data": data}
        except Exception as e:
            logger.error(f"Error retrieving user activity summary: {str(e)}")
            return {
                "success": False,
                "message": f"Error retrieving user activity summary: {str(e)}",
            }

    async def get_system_activity_summary(self) -> Dict[str, Any]:
        client = await self._get_admin()
        try:
            response = await client.table("audit_logs").select("action").execute()
            counter = Counter(row.get("action", "unknown") for row in (response.data or []))
            data = [{"action": action, "count": count} for action, count in counter.items()]
            return {"success": True, "data": data}
        except Exception as e:
            logger.error(f"Error retrieving system activity summary: {str(e)}")
            return {
                "success": False,
                "message": f"Error retrieving system activity summary: {str(e)}",
            }

    async def cleanup_old_logs(self, days_to_keep: int = 90) -> Dict[str, Any]:
        client = await self._get_admin()
        try:
            cutoff_date = (datetime.utcnow() - timedelta(days=days_to_keep)).isoformat()
            response = await (
                client.table("audit_logs")
                .delete()
                .lt("created_at", cutoff_date)
                .execute()
            )
            deleted_count = len(response.data or [])
            return {
                "success": True,
                "deleted_count": deleted_count,
                "message": f"Successfully deleted {deleted_count} old audit logs",
            }
        except Exception as e:
            logger.error(f"Error cleaning up old audit logs: {str(e)}")
            return {
                "success": False,
                "message": f"Error cleaning up old audit logs: {str(e)}",
            }
