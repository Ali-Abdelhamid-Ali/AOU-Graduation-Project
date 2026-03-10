"""Enhanced Logging Repository - Real-time monitoring data operations."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.db.supabase.client import SupabaseProvider
from src.observability.logger import get_logger
from src.repositories.schema_compat import (
    build_execution_log_payload,
    normalize_execution_log_record,
)

logger = get_logger("repositories.real_time_monitoring")


class RealTimeMonitoringRepository:
    """Repository for real-time monitoring and execution tracking."""

    async def _get_admin(self):
        return await SupabaseProvider.get_admin()

    async def _query_execution_audits(self, *, start_time: Optional[str] = None):
        client = await self._get_admin()
        query = (
            client.table("audit_logs")
            .select("id, user_id, user_role, description, changes, ip_address, user_agent, created_at")
            .eq("action", "execution_log")
            .order("created_at", desc=True)
            .limit(30000)
        )
        if start_time:
            query = query.gte("created_at", start_time)
        result = await query.execute()
        return result.data or []

    async def create_execution_log(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        client = await self._get_admin()
        try:
            payload = build_execution_log_payload(log_entry)
            response = await client.table("audit_logs").insert(payload).execute()
            if response.data:
                return {
                    "success": True,
                    "log_id": response.data[0]["id"],
                    "correlation_id": log_entry.get("correlation_id"),
                    "message": "Execution log created successfully",
                }
            return {"success": False, "message": "Failed to create execution log"}
        except Exception as e:
            logger.error(f"Error creating execution log: {str(e)}")
            return {
                "success": False,
                "message": f"Error creating execution log: {str(e)}",
            }

    async def batch_create_execution_logs(
        self, log_entries: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        client = await self._get_admin()
        try:
            payload = [build_execution_log_payload(entry) for entry in log_entries]
            response = await client.table("audit_logs").insert(payload).execute()
            created_count = len(response.data or [])
            return {
                "success": True,
                "count": created_count,
                "message": f"Successfully created {created_count} execution logs",
            }
        except Exception as e:
            logger.error(f"Error creating batch execution logs: {str(e)}")
            return {
                "success": False,
                "message": f"Error creating batch execution logs: {str(e)}",
            }

    async def get_execution_logs(
        self,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        status_code: Optional[int] = None,
        error_category: Optional[str] = None,
        path_pattern: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        try:
            rows = await self._query_execution_audits(start_time=start_time)
            logs = [normalize_execution_log_record(row) for row in rows]

            filtered: List[Dict[str, Any]] = []
            for log in logs:
                if end_time and str(log.get("timestamp") or "") > end_time:
                    continue
                if status_code is not None and log.get("status_code") != status_code:
                    continue
                if error_category and log.get("error_category") != error_category:
                    continue
                if path_pattern and path_pattern.lower() not in str(
                    log.get("request_path") or ""
                ).lower():
                    continue
                filtered.append(log)

            paginated = filtered[offset : offset + limit]
            return {"success": True, "data": paginated, "count": len(filtered)}
        except Exception as e:
            logger.error(f"Error retrieving execution logs: {str(e)}")
            return {
                "success": False,
                "message": f"Error retrieving execution logs: {str(e)}",
            }

    async def get_execution_summary(self, hours: int = 24) -> Dict[str, Any]:
        try:
            start_time = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
            rows = await self.get_execution_logs(start_time=start_time, limit=30000)
            if not rows["success"]:
                return rows

            logs = rows["data"]
            total_requests = len(logs)
            successful_requests = sum(1 for log in logs if log.get("success", True))
            error_requests = total_requests - successful_requests

            durations = [
                float(log.get("duration_ms"))
                for log in logs
                if log.get("duration_ms") is not None
            ]
            avg_duration = sum(durations) / len(durations) if durations else 0.0

            error_categories: Dict[str, int] = {}
            for log in logs:
                category = log.get("error_category")
                if category:
                    error_categories[category] = error_categories.get(category, 0) + 1

            slowest_endpoints = sorted(
                [
                    {
                        "request_path": log.get("request_path"),
                        "duration_ms": log.get("duration_ms", 0),
                    }
                    for log in logs
                ],
                key=lambda item: float(item.get("duration_ms") or 0),
                reverse=True,
            )[:5]

            summary = {
                "time_range_hours": hours,
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "error_requests": error_requests,
                "success_rate": (successful_requests / total_requests * 100)
                if total_requests > 0
                else 0,
                "average_duration_ms": round(avg_duration, 2),
                "error_categories": error_categories,
                "slowest_endpoints": slowest_endpoints,
            }
            return {"success": True, "data": summary}
        except Exception as e:
            logger.error(f"Error retrieving execution summary: {str(e)}")
            return {
                "success": False,
                "message": f"Error retrieving execution summary: {str(e)}",
            }

    async def cleanup_old_logs(self, days_to_keep: int = 7) -> Dict[str, Any]:
        client = await self._get_admin()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            response = await (
                client.table("audit_logs")
                .delete()
                .eq("action", "execution_log")
                .lt("created_at", cutoff_date.isoformat())
                .execute()
            )
            deleted_count = len(response.data or [])
            return {
                "success": True,
                "deleted_count": deleted_count,
                "message": f"Successfully deleted {deleted_count} old execution logs",
            }
        except Exception as e:
            logger.error(f"Error cleaning up old execution logs: {str(e)}")
            return {
                "success": False,
                "message": f"Error cleaning up old execution logs: {str(e)}",
            }

    async def get_performance_metrics(self, hours: int = 24) -> Dict[str, Any]:
        try:
            start_time = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
            rows = await self.get_execution_logs(start_time=start_time, limit=30000)
            if not rows["success"]:
                return rows

            data = rows["data"]
            if not data:
                return {
                    "success": True,
                    "data": {
                        "time_range_hours": hours,
                        "total_requests": 0,
                        "average_duration_ms": 0,
                        "p50_duration": 0,
                        "p95_duration": 0,
                        "p99_duration": 0,
                        "average_memory": 0,
                        "average_cpu": 0,
                        "max_duration": 0,
                        "min_duration": 0,
                    },
                }

            durations = sorted(
                float(row.get("duration_ms"))
                for row in data
                if row.get("duration_ms") is not None
            )
            memory_usage = sorted(
                float(row.get("memory_usage_mb"))
                for row in data
                if row.get("memory_usage_mb") is not None
            )
            cpu_usage = sorted(
                float(row.get("cpu_percent"))
                for row in data
                if row.get("cpu_percent") is not None
            )

            def percentile(values: List[float], p: int) -> float:
                if not values:
                    return 0.0
                index = int(len(values) * p / 100)
                return values[min(index, len(values) - 1)]

            metrics = {
                "time_range_hours": hours,
                "total_requests": len(data),
                "average_duration_ms": round(sum(durations) / len(durations), 2)
                if durations
                else 0,
                "p50_duration": round(percentile(durations, 50), 2),
                "p95_duration": round(percentile(durations, 95), 2),
                "p99_duration": round(percentile(durations, 99), 2),
                "average_memory": round(sum(memory_usage) / len(memory_usage), 2)
                if memory_usage
                else 0,
                "average_cpu": round(sum(cpu_usage) / len(cpu_usage), 2)
                if cpu_usage
                else 0,
                "max_duration": round(max(durations), 2) if durations else 0,
                "min_duration": round(min(durations), 2) if durations else 0,
            }
            return {"success": True, "data": metrics}
        except Exception as e:
            logger.error(f"Error retrieving performance metrics: {str(e)}")
            return {
                "success": False,
                "message": f"Error retrieving performance metrics: {str(e)}",
            }
