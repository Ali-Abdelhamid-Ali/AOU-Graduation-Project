"""Enhanced Logging Repository - Real-time monitoring data operations."""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from src.db.supabase.client import SupabaseProvider
from src.observability.logger import get_logger

logger = get_logger("repositories.real_time_monitoring")


class RealTimeMonitoringRepository:
    """Repository for real-time monitoring and execution tracking."""

    def __init__(self):
        pass

    async def _get_admin(self):
        return await SupabaseProvider.get_admin()

    async def create_execution_log(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new execution log entry."""
        client = await self._get_admin()
        try:
            # Prepare data for Supabase insertion
            supabase_data = {
                "correlation_id": log_entry["correlation_id"],
                "timestamp": log_entry["timestamp"],
                "request_method": log_entry["request"]["method"],
                "request_path": log_entry["request"]["path"],
                "request_headers": log_entry["request"]["headers"],
                "request_query_params": log_entry["request"]["query_params"],
                "status_code": log_entry["response"]["status_code"],
                "response_headers": log_entry["response"]["headers"],
                "duration_ms": log_entry["performance"]["total_duration_ms"],
                "memory_usage_mb": log_entry["performance"]["memory_usage_mb"],
                "cpu_percent": log_entry["performance"]["cpu_percent"],
                "success": log_entry["performance"]["success"],
                "error_category": log_entry["performance"].get("error_category"),
                "error_priority": log_entry["performance"].get("error_priority"),
                "client_ip": log_entry["request"]["client_ip"],
                "user_agent": log_entry["request"]["user_agent"],
                "raw_data": log_entry,  # Store full structured data
            }

            # Add error data if present
            if "error" in log_entry:
                supabase_data.update(
                    {
                        "error_type": log_entry["error"]["type"],
                        "error_message": log_entry["error"]["message"],
                        "error_category": log_entry["error"]["category"],
                        "error_priority": log_entry["error"]["priority"],
                        "error_stack_trace": log_entry["error"]["stack_trace"],
                    }
                )

            response = await (
                client.table("execution_logs").insert(supabase_data).execute()
            )

            if response.data:
                logger.info(
                    f"Execution log created: {log_entry['request']['method']} {log_entry['request']['path']}"
                )
                return {
                    "success": True,
                    "log_id": response.data[0]["id"],
                    "correlation_id": log_entry["correlation_id"],
                    "message": "Execution log created successfully",
                }
            else:
                logger.error(
                    f"Failed to create execution log for: {log_entry['request']['path']}"
                )
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
        """Create multiple execution log entries in batch."""
        client = await self._get_admin()
        try:
            supabase_data = []

            for log_entry in log_entries:
                data = {
                    "correlation_id": log_entry["correlation_id"],
                    "timestamp": log_entry["timestamp"],
                    "request_method": log_entry["request"]["method"],
                    "request_path": log_entry["request"]["path"],
                    "request_headers": log_entry["request"]["headers"],
                    "request_query_params": log_entry["request"]["query_params"],
                    "status_code": log_entry["response"]["status_code"],
                    "response_headers": log_entry["response"]["headers"],
                    "duration_ms": log_entry["performance"]["total_duration_ms"],
                    "memory_usage_mb": log_entry["performance"]["memory_usage_mb"],
                    "cpu_percent": log_entry["performance"]["cpu_percent"],
                    "success": log_entry["performance"]["success"],
                    "error_category": log_entry["performance"].get("error_category"),
                    "error_priority": log_entry["performance"].get("error_priority"),
                    "client_ip": log_entry["request"]["client_ip"],
                    "user_agent": log_entry["request"]["user_agent"],
                    "raw_data": log_entry,
                }

                # Add error data if present
                if "error" in log_entry:
                    data.update(
                        {
                            "error_type": log_entry["error"]["type"],
                            "error_message": log_entry["error"]["message"],
                            "error_category": log_entry["error"]["category"],
                            "error_priority": log_entry["error"]["priority"],
                            "error_stack_trace": log_entry["error"]["stack_trace"],
                        }
                    )

                supabase_data.append(data)

            response = (
                await client.table("execution_logs").insert(supabase_data).execute()
            )

            if response.data:
                logger.info(f"Batch created {len(response.data)} execution logs")
                return {
                    "success": True,
                    "count": len(response.data),
                    "message": f"Successfully created {len(response.data)} execution logs",
                }
            else:
                logger.error("Failed to create batch execution logs")
                return {
                    "success": False,
                    "message": "Failed to create batch execution logs",
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
        """Get execution logs with filtering options."""
        client = await self._get_admin()
        try:
            query = client.table("execution_logs").select(
                "id, request_method, request_path, status_code, duration_ms, cpu_percent, memory_usage_mb, success, timestamp"
            )

            # Apply filters
            if start_time:
                query = query.gte("timestamp", start_time)

            if end_time:
                query = query.lte("timestamp", end_time)

            if status_code:
                query = query.eq("status_code", status_code)

            if error_category:
                query = query.eq("error_category", error_category)

            if path_pattern:
                query = query.ilike("request_path", f"%{path_pattern}%")

            query = query.order("timestamp", desc=True).range(
                offset, offset + limit - 1
            )

            response = await query.execute()

            if response.data:
                logger.info(f"Retrieved {len(response.data)} execution logs")
                return {
                    "success": True,
                    "data": response.data,
                    "count": len(response.data),
                }
            else:
                logger.info("No execution logs found")
                return {"success": True, "data": [], "count": 0}

        except Exception as e:
            logger.error(f"Error retrieving execution logs: {str(e)}")
            return {
                "success": False,
                "message": f"Error retrieving execution logs: {str(e)}",
            }

    async def get_execution_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get execution summary for the last N hours."""
        client = await self._get_admin()
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)

            # Plan Section 11: Parallel Query Execution
            import asyncio

            # Prepare independent queries
            total_q = (
                client.table("execution_logs")
                .select("id", count="exact")
                .gte("timestamp", start_time.isoformat())
            )
            success_q = (
                client.table("execution_logs")
                .select("id", count="exact")
                .gte("timestamp", start_time.isoformat())
                .eq("success", True)
            )
            error_q = (
                client.table("execution_logs")
                .select("id", count="exact")
                .gte("timestamp", start_time.isoformat())
                .eq("success", False)
            )
            dur_q = (
                client.table("execution_logs")
                .select("duration_ms")
                .gte("timestamp", start_time.isoformat())
            )
            err_cat_q = (
                client.table("execution_logs")
                .select("error_category")
                .gte("timestamp", start_time.isoformat())
                .neq("error_category", None)
            )
            slow_q = (
                client.table("execution_logs")
                .select("request_path, duration_ms")
                .gte("timestamp", start_time.isoformat())
                .order("duration_ms", desc=True)
                .limit(5)
            )

            results = await asyncio.gather(
                total_q.execute(),
                success_q.execute(),
                error_q.execute(),
                dur_q.execute(),
                err_cat_q.execute(),
                slow_q.execute(),
                return_exceptions=True,
            )

            # Map results
            total_requests = (
                results[0].count if not isinstance(results[0], Exception) else 0
            )
            successful_requests = (
                results[1].count if not isinstance(results[1], Exception) else 0
            )
            error_requests = (
                results[2].count if not isinstance(results[2], Exception) else 0
            )
            durations = [
                row["duration_ms"]
                for row in (
                    results[3].data
                    if not isinstance(results[3], Exception) and results[3].data
                    else []
                )
            ]
            avg_duration = sum(durations) / len(durations) if durations else 0

            error_categories: dict[str, Any] = {}
            error_cat_data = (
                results[4].data
                if not isinstance(results[4], Exception) and results[4].data
                else []
            )
            for row in error_cat_data:
                category = row["error_category"]
                error_categories[category] = error_categories.get(category, 0) + 1

            slowest_endpoints = (
                results[5].data
                if not isinstance(results[5], Exception) and results[5].data
                else []
            )

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

            logger.info(f"Retrieved execution summary for last {hours} hours")
            return {"success": True, "data": summary}

        except Exception as e:
            logger.error(f"Error retrieving execution summary: {str(e)}")
            return {
                "success": False,
                "message": f"Error retrieving execution summary: {str(e)}",
            }

    async def cleanup_old_logs(self, days_to_keep: int = 7) -> Dict[str, Any]:
        """Clean up execution logs older than specified days."""
        client = await self._get_admin()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

            # Delete old logs
            response = await (
                client.table("execution_logs")
                .delete()
                .lt("timestamp", cutoff_date.isoformat())
                .execute()
            )

            deleted_count = len(response.data) if response.data else 0
            logger.info(f"Cleaned up {deleted_count} old execution logs")

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
        """Get performance metrics for the last N hours."""
        client = await self._get_admin()
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)

            # Get all performance data
            query = (
                client.table("execution_logs")
                .select("duration_ms, memory_usage_mb, cpu_percent, timestamp")
                .gte("timestamp", start_time.isoformat())
            )
            response = await query.execute()

            if not response.data:
                return {
                    "success": True,
                    "data": {
                        "total_requests": 0,
                        "average_duration": 0,
                        "p50_duration": 0,
                        "p95_duration": 0,
                        "p99_duration": 0,
                        "average_memory": 0,
                        "average_cpu": 0,
                    },
                }

            data = response.data

            # Calculate metrics
            durations = [row["duration_ms"] for row in data]
            memory_usage = [row["memory_usage_mb"] for row in data]
            cpu_usage = [row["cpu_percent"] for row in data]

            durations.sort()
            memory_usage.sort()
            cpu_usage.sort()

            def percentile(data, p):
                if not data:
                    return 0
                index = int(len(data) * p / 100)
                return data[min(index, len(data) - 1)]

            metrics = {
                "time_range_hours": hours,
                "total_requests": len(data),
                "average_duration": round(sum(durations) / len(durations), 2),
                "p50_duration": round(percentile(durations, 50), 2),
                "p95_duration": round(percentile(durations, 95), 2),
                "p99_duration": round(percentile(durations, 99), 2),
                "average_memory": round(sum(memory_usage) / len(memory_usage), 2),
                "average_cpu": round(sum(cpu_usage) / len(cpu_usage), 2),
                "max_duration": round(max(durations), 2),
                "min_duration": round(min(durations), 2),
            }

            logger.info(f"Retrieved performance metrics for last {hours} hours")
            return {"success": True, "data": metrics}

        except Exception as e:
            logger.error(f"Error retrieving performance metrics: {str(e)}")
            return {
                "success": False,
                "message": f"Error retrieving performance metrics: {str(e)}",
            }

