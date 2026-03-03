from typing import List, Dict, Any, Optional
from src.db.supabase.client import SupabaseProvider
from src.services.infrastructure.memory_cache import global_cache
from src.services.infrastructure.retry_utils import async_retry
from src.observability.logger import get_logger

logger = get_logger("repository.analytics")


class AnalyticsRepository:
    """Analytics Repository for aggregated clinical data."""

    def __init__(self):
        self.cache = global_cache
        self._audit_time_column: Optional[str] = None

    async def _get_client(self):
        return await SupabaseProvider.get_admin()

    async def _resolve_audit_time_column(self, client) -> str:
        if self._audit_time_column:
            return self._audit_time_column

        for candidate in ("timestamp", "created_at"):
            try:
                await client.table("audit_logs").select(candidate).limit(1).execute()
                self._audit_time_column = candidate
                return candidate
            except Exception as exc:
                if "PGRST204" in str(exc):
                    continue
                continue

        self._audit_time_column = "created_at"
        return self._audit_time_column

    @staticmethod
    def _extract_status_code(details: Any) -> Optional[int]:
        if not isinstance(details, dict):
            return None
        try:
            value = details.get("status_code")
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    async def get_patient_stats(self, patient_id: str) -> Dict[str, Any]:
        """Get aggregated stats for a patient dashboard."""
        client = await self._get_client()

        # Plan Section 11: Parallel Query Execution
        import asyncio
        from datetime import datetime

        now = datetime.now().isoformat().split("T")[0]

        results = await asyncio.gather(
            client.table("ecg_results")
            .select("id", count="exact")
            .eq("patient_id", patient_id)
            .execute(),
            client.table("mri_segmentation_results")
            .select("id", count="exact")
            .eq("patient_id", patient_id)
            .execute(),
            client.table("appointments")
            .select("appointment_date, appointment_time")
            .eq("patient_id", patient_id)
            .gte("appointment_date", now)
            .order("appointment_date", desc=False)
            .limit(1)
            .execute(),
            client.table("ecg_results")
            .select("confidence_score, primary_diagnosis, created_at")
            .eq("patient_id", patient_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute(),
            client.table("mri_segmentation_results")
            .select("tumor_detected, created_at")
            .eq("patient_id", patient_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute(),
            return_exceptions=True,
        )

        # Safely extract results
        ecg_count_res = results[0]
        mri_count_res = results[1]
        next_apt_res = results[2]
        latest_ecg_res = results[3]
        latest_mri_res = results[4]

        def get_first(res):
            if not isinstance(res, Exception) and hasattr(res, "data") and res.data:
                return res.data[0]
            return None

        return {
            "total_reports": (
                (ecg_count_res.count or 0)
                if not isinstance(ecg_count_res, Exception)
                and hasattr(ecg_count_res, "count")
                else 0
            )
            + (
                (mri_count_res.count or 0)
                if not isinstance(mri_count_res, Exception)
                and hasattr(mri_count_res, "count")
                else 0
            ),
            "next_appointment": get_first(next_apt_res),
            "latest_ecg": get_first(latest_ecg_res),
            "latest_mri": get_first(latest_mri_res),
        }

    async def get_health_trends(
        self, patient_id: str, days: int = 30
    ) -> List[Dict[str, Any]]:
        """Fetch health trend data for visualizations."""
        # Simulated for now, or fetch from vital_signs table if it exists
        return [
            {"date": "2024-03-01", "score": 85},
            {"date": "2024-03-05", "score": 88},
            {"date": "2024-03-10", "score": 92},
            {"date": "2024-03-15", "score": 90},
            {"date": "2024-03-20", "score": 95},
        ]

    async def list_appointments(self, patient_id: str) -> List[Dict[str, Any]]:
        """Fetch all appointments for a patient with doctor details."""
        client = await self._get_client()
        try:
            # Plan Section 7.B: Specific selectors + Pagination
            result = await (
                client.table("appointments")
                .select(
                    "id, appointment_date, appointment_time, status, patient_id, doctor_id, doctors(first_name, last_name, specialty)"
                )
                .eq("patient_id", patient_id)
                .order("appointment_date", desc=True)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(
                f"Error listing appointments for patient {patient_id}: {str(e)}"
            )
            return []

    @async_retry(max_retries=3)
    async def update_appointment(self, appointment_id: str, data: dict):
        """Update appointment record."""
        client = await self._get_client()
        try:
            result = await (
                client.table("appointments")
                .update(data)
                .eq("id", appointment_id)
                .execute()
            )
            # Section 5.A: Invalidate analytics cache on write
            await self.cache.clear()
            return result.data[0] if result.data else None
        except Exception as e:
            from src.observability.logger import get_logger

            logger = get_logger(__name__)
            logger.error(f"Error updating appointment {appointment_id}: {str(e)}")
            return None

    async def get_total_users_count(self) -> int:
        """Get total number of users in the system."""
        # cache_key = "analytics:total_users_count"
        # cached = await self.cache.get(cache_key)
        # if cached is not None:
        #     return cached

        client = await self._get_client()
        try:
            # Count from user_roles table to get all active users
            result = await (
                client.table("user_roles").select("id", count="exact").execute()
            )
            count = result.count or 0
            # await self.cache.set(
            #     cache_key, count, ttl_seconds=300
            # )  # Cache for 5 minutes
            return count
        except Exception as e:
            from src.observability.logger import get_logger

            logger = get_logger(__name__)
            logger.error(f"Error getting total users count: {str(e)}")
            return 0

    async def get_active_users_count(self) -> int:
        """Get number of active users in the system."""
        # cache_key = "analytics:active_users_count"
        # cached = await self.cache.get(cache_key)
        # if cached is not None:
        #     return cached

        client = await self._get_client()
        try:
            # Count active users from user_roles table
            result = await (
                client.table("user_roles")
                .select("id", count="exact")
                .eq("is_active", True)
                .execute()
            )
            count = result.count or 0
            # await self.cache.set(cache_key, count, ttl_seconds=300)
            return count
        except Exception as e:
            from src.observability.logger import get_logger

            logger = get_logger(__name__)
            logger.error(f"Error getting active users count: {str(e)}")
            return 0

    async def get_system_health(self) -> str:
        """Get system health status."""
        client = await self._get_client()
        try:
            # Check if we can connect to the database
            result = await client.table("user_roles").select("id").limit(1).execute()
            if result.data:
                return "healthy"
            else:
                return "warning"
        except Exception as e:
            from src.observability.logger import get_logger

            logger = get_logger(__name__)
            logger.error(f"Error checking system health: {str(e)}")
            return "critical"

    async def get_audit_logs_count(self) -> int:
        """Get total number of audit logs."""
        client = await self._get_client()
        try:
            result = await (
                client.table("audit_logs").select("id", count="exact").execute()
            )
            return result.count or 0
        except Exception as e:
            from src.observability.logger import get_logger

            logger = get_logger(__name__)
            logger.error(f"Error getting audit logs count: {str(e)}")
            return 0

    async def get_system_activity_summary(self) -> dict:
        """Get system activity summary."""
        # client = await self._get_client()
        try:
            # Get recent activity counts by action type
            # PostgREST doesn't support group by directly through this client
            # For now, return a placeholder or implement an RPC
            # result = await client.table("audit_logs").select("action, count(*)").group("action").execute()
            return {}
        except Exception as e:
            from src.observability.logger import get_logger

            logger = get_logger(__name__)
            logger.error(f"Error getting system activity summary: {str(e)}")
            return {}

    async def get_user_activity_summary(self) -> dict:
        """Get user activity summary."""
        # client = await self._get_client()
        try:
            # Get user activity counts
            # PostgREST doesn't support group by directly through this client
            # result = await client.table("audit_logs").select("user_id, count(*)").group("user_id").execute()
            return {}
        except Exception as e:
            from src.observability.logger import get_logger

            logger = get_logger(__name__)
            logger.error(f"Error getting user activity summary: {str(e)}")
            return {}

    async def get_user_hospital_id(self, user_id: str) -> str:
        """Get hospital ID for a user."""
        client = await self._get_client()
        try:
            # Try to get from doctors table first
            result = await (
                client.table("doctors")
                .select("hospital_id")
                .eq("user_id", user_id)
                .execute()
            )
            if result.data:
                return result.data[0]["hospital_id"]

            # Try nurses table
            result = await (
                client.table("nurses")
                .select("hospital_id")
                .eq("user_id", user_id)
                .execute()
            )
            if result.data:
                return result.data[0]["hospital_id"]

            # Try administrators table
            result = await (
                client.table("administrators")
                .select("hospital_id")
                .eq("user_id", user_id)
                .execute()
            )
            if result.data:
                return result.data[0]["hospital_id"]

            return user_id
        except Exception as e:
            from src.observability.logger import get_logger

            logger = get_logger(__name__)
            logger.error(f"Error getting hospital ID for user {user_id}: {str(e)}")
            return user_id

    async def get_hospital_users_count(self, hospital_id: str) -> int:
        """Get total number of users in a hospital."""
        client = await self._get_client()
        try:
            # Plan Section 11: Parallel Query Execution
            import asyncio

            results = await asyncio.gather(
                client.table("doctors")
                .select("id", count="exact")
                .eq("hospital_id", hospital_id)
                .execute(),
                client.table("nurses")
                .select("id", count="exact")
                .eq("hospital_id", hospital_id)
                .execute(),
                client.table("administrators")
                .select("id", count="exact")
                .eq("hospital_id", hospital_id)
                .execute(),
                return_exceptions=True,
            )

            total = 0
            for res in results:
                if not isinstance(res, Exception) and hasattr(res, "count"):
                    total += res.count or 0
            return total
        except Exception as e:
            from src.observability.logger import get_logger

            logger = get_logger(__name__)
            logger.error(
                f"Error getting hospital users count for {hospital_id}: {str(e)}"
            )
            return 0

    async def get_hospital_active_users_count(self, hospital_id: str) -> int:
        """Get number of active users in a hospital."""
        client = await self._get_client()
        try:
            # Plan Section 11: Parallel Query Execution
            import asyncio

            results = await asyncio.gather(
                client.table("doctors")
                .select("id", count="exact")
                .eq("hospital_id", hospital_id)
                .eq("is_active", True)
                .execute(),
                client.table("nurses")
                .select("id", count="exact")
                .eq("hospital_id", hospital_id)
                .eq("is_active", True)
                .execute(),
                client.table("administrators")
                .select("id", count="exact")
                .eq("hospital_id", hospital_id)
                .eq("is_active", True)
                .execute(),
                return_exceptions=True,
            )

            total = 0
            for res in results:
                if not isinstance(res, Exception) and hasattr(res, "count"):
                    total += res.count or 0
            return total
        except Exception as e:
            from src.observability.logger import get_logger

            logger = get_logger(__name__)
            logger.error(
                f"Error getting hospital active users count for {hospital_id}: {str(e)}"
            )
            return 0

    async def get_hospital_system_health(self, hospital_id: str) -> str:
        """Get system health status for a hospital."""
        client = await self._get_client()
        try:
            # Check if we can access hospital data
            result = await (
                client.table("doctors")
                .select("id")
                .eq("hospital_id", hospital_id)
                .limit(1)
                .execute()
            )
            if result.data:
                return "healthy"
            else:
                return "warning"
        except Exception as e:
            from src.observability.logger import get_logger

            logger = get_logger(__name__)
            logger.error(
                f"Error checking hospital system health for {hospital_id}: {str(e)}"
            )
            return "critical"

    async def get_hospital_activity_summary(self, hospital_id: str) -> dict:
        """Get hospital activity summary."""
        # client = await self._get_client()
        try:
            # Get activity for users in this hospital
            # PostgREST doesn't support group by directly through this client
            # result = await client.table("audit_logs").select("action, count(*)").eq("hospital_id", hospital_id).group("action").execute()
            return {}
        except Exception as e:
            from src.observability.logger import get_logger

            logger = get_logger(__name__)
            logger.error(
                f"Error getting hospital activity summary for {hospital_id}: {str(e)}"
            )
            return {}

    async def get_doctor_assigned_patients_count(self, doctor_id: str) -> int:
        """Get number of patients assigned to a doctor."""
        client = await self._get_client()
        try:
            result = await (
                client.table("patients")
                .select("id", count="exact")
                .eq("assigned_doctor_id", doctor_id)
                .execute()
            )
            return result.count or 0
        except Exception as e:
            from src.observability.logger import get_logger

            logger = get_logger(__name__)
            logger.error(
                f"Error getting assigned patients count for doctor {doctor_id}: {str(e)}"
            )
            return 0

    async def get_doctor_pending_cases_count(self, doctor_id: str) -> int:
        """Get number of pending cases for a doctor."""
        client = await self._get_client()
        try:
            result = await (
                client.table("medical_cases")
                .select("id", count="exact")
                .eq("assigned_doctor_id", doctor_id)
                .eq("status", "pending")
                .execute()
            )
            return result.count or 0
        except Exception as e:
            from src.observability.logger import get_logger

            logger = get_logger(__name__)
            logger.error(
                f"Error getting pending cases count for doctor {doctor_id}: {str(e)}"
            )
            return 0

    async def get_doctor_completed_cases_count(self, doctor_id: str) -> int:
        """Get number of completed cases for a doctor."""
        client = await self._get_client()
        try:
            result = await (
                client.table("medical_cases")
                .select("id", count="exact")
                .eq("assigned_doctor_id", doctor_id)
                .eq("status", "completed")
                .execute()
            )
            return result.count or 0
        except Exception as e:
            from src.observability.logger import get_logger

            logger = get_logger(__name__)
            logger.error(
                f"Error getting completed cases count for doctor {doctor_id}: {str(e)}"
            )
            return 0

    async def get_doctor_workload_summary(self, doctor_id: str) -> dict:
        """Get doctor workload summary."""
        try:
            pending_count = await self.get_doctor_pending_cases_count(doctor_id)
            completed_count = await self.get_doctor_completed_cases_count(doctor_id)

            return {
                "pending_cases": pending_count,
                "completed_cases": completed_count,
                "total_cases": pending_count + completed_count,
                "completion_rate": (
                    completed_count / max(pending_count + completed_count, 1)
                )
                * 100,
            }
        except Exception as e:
            from src.observability.logger import get_logger

            logger = get_logger(__name__)
            logger.error(
                f"Error getting doctor workload summary for {doctor_id}: {str(e)}"
            )
            return {}

    async def get_nurse_assigned_patients_count(self, nurse_id: str) -> int:
        """Get number of patients assigned to a nurse."""
        client = await self._get_client()
        try:
            result = await (
                client.table("patients")
                .select("id", count="exact")
                .eq("assigned_nurse_id", nurse_id)
                .execute()
            )
            return result.count or 0
        except Exception as e:
            from src.observability.logger import get_logger

            logger = get_logger(__name__)
            logger.error(
                f"Error getting assigned patients count for nurse {nurse_id}: {str(e)}"
            )
            return 0

    async def get_nurse_pending_tasks_count(self, nurse_id: str) -> int:
        """Get number of pending tasks for a nurse."""
        try:
            # This would depend on your task management system
            # For now, return 0 as placeholder
            return 0
        except Exception as e:
            from src.observability.logger import get_logger

            logger = get_logger(__name__)
            logger.error(
                f"Error getting pending tasks count for nurse {nurse_id}: {str(e)}"
            )
            return 0

    async def get_nurse_completed_tasks_count(self, nurse_id: str) -> int:
        """Get number of completed tasks for a nurse."""
        try:
            # This would depend on your task management system
            # For now, return 0 as placeholder
            return 0
        except Exception as e:
            from src.observability.logger import get_logger

            logger = get_logger(__name__)
            logger.error(
                f"Error getting completed tasks count for nurse {nurse_id}: {str(e)}"
            )
            return 0

    async def get_nurse_task_summary(self, nurse_id: str) -> dict:
        """Get nurse task summary."""
        try:
            pending_tasks = await self.get_nurse_pending_tasks_count(nurse_id)
            completed_tasks = await self.get_nurse_completed_tasks_count(nurse_id)

            return {
                "pending_tasks": pending_tasks,
                "completed_tasks": completed_tasks,
                "total_tasks": pending_tasks + completed_tasks,
                "completion_rate": (
                    completed_tasks / max(pending_tasks + completed_tasks, 1)
                )
                * 100,
            }
        except Exception as e:
            from src.observability.logger import get_logger

            logger = get_logger(__name__)
            logger.error(f"Error getting nurse task summary for {nurse_id}: {str(e)}")
            return {}

    async def get_user_distribution(self) -> Dict[str, int]:
        """Get user distribution by role."""
        client = await self._get_client()
        try:
            # Count users by role from user_roles table
            result = await (
                client.table("user_roles")
                .select("role, count(*)")
                .group("role")
                .execute()
            )
            return (
                {item["role"]: item["count"] for item in result.data}
                if result.data
                else {}
            )
        except Exception as e:
            from src.observability.logger import get_logger

            logger = get_logger(__name__)
            logger.error(f"Failed to get user distribution: {str(e)}")
            return {}

    async def get_hospital_statistics(self, hospital_id: str) -> Dict[str, Any]:
        """Get statistics for a specific hospital."""
        try:
            # Get hospital-specific statistics
            stats = {
                "total_users": await self.get_hospital_users_count(hospital_id),
                "active_users": await self.get_hospital_active_users_count(hospital_id),
                "user_distribution": await self.get_hospital_user_distribution(
                    hospital_id
                ),
                "system_health": await self.get_hospital_system_health(hospital_id),
                "activity_summary": await self.get_hospital_activity_summary(
                    hospital_id
                ),
            }
            return stats
        except Exception as e:
            from src.observability.logger import get_logger

            logger = get_logger(__name__)
            logger.error(f"Failed to get hospital statistics: {str(e)}")
            return {}

    async def get_hospital_user_distribution(self, hospital_id: str) -> Dict[str, int]:
        """Get user distribution by role for a specific hospital."""
        client = await self._get_client()
        try:
            # Plan Section 11: Parallel Query Execution
            import asyncio

            results = await asyncio.gather(
                client.table("doctors")
                .select("id", count="exact")
                .eq("hospital_id", hospital_id)
                .execute(),
                client.table("nurses")
                .select("id", count="exact")
                .eq("hospital_id", hospital_id)
                .execute(),
                client.table("administrators")
                .select("id", count="exact")
                .eq("hospital_id", hospital_id)
                .execute(),
                return_exceptions=True,
            )

            # Extract values safely
            def get_count(idx):
                res = results[idx]
                return (
                    (res.count or 0)
                    if not isinstance(res, Exception) and hasattr(res, "count")
                    else 0
                )

            return {
                "doctor": get_count(0),
                "nurse": get_count(1),
                "admin": get_count(2),
            }
        except Exception as e:
            from src.observability.logger import get_logger

            logger = get_logger(__name__)
            logger.error(f"Failed to get hospital user distribution: {str(e)}")
            return {}

    async def get_hospital_user_growth(self, hospital_id: str) -> List[Dict[str, Any]]:
        """Get user growth trend for a specific hospital."""
        try:
            # This would require a more complex query with date filtering
            # For now, return simulated data
            return [
                {"date": "2024-01-01", "count": 5},
                {"date": "2024-02-01", "count": 8},
                {"date": "2024-03-01", "count": 12},
                {"date": "2024-04-01", "count": 15},
            ]
        except Exception as e:
            from src.observability.logger import get_logger

            logger = get_logger(__name__)
            logger.error(f"Failed to get hospital user growth: {str(e)}")
            return []

    async def get_user_recent_activity(
        self, user_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent activity for a specific user."""
        client = await self._get_client()
        try:
            # Get recent audit logs for this user
            result = await (
                client.table("audit_logs")
                .select("id, action, entity_type, entity_id, timestamp, performed_by")
                .eq("performed_by", user_id)
                .order("timestamp", desc=True)
                .limit(limit)
                .execute()
            )

            return result.data or []
        except Exception as e:
            from src.observability.logger import get_logger

            logger = get_logger(__name__)
            logger.error(f"Failed to get user recent activity: {str(e)}")
            return []

    async def get_user_growth_trend(self) -> List[Dict[str, Any]]:
        """Get user growth trend over time."""
        try:
            # This would require date-based aggregation
            # For now, return simulated data
            return [
                {"month": "Jan 2024", "total_users": 100, "new_users": 10},
                {"month": "Feb 2024", "total_users": 115, "new_users": 15},
                {"month": "Mar 2024", "total_users": 130, "new_users": 15},
                {"month": "Apr 2024", "total_users": 150, "new_users": 20},
            ]
        except Exception as e:
            from src.observability.logger import get_logger

            logger = get_logger(__name__)
            logger.error(f"Failed to get user growth trend: {str(e)}")
            return []

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # DASHBOARD ANALYTICS EXTENSIONS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    async def get_api_usage_stats(self) -> Dict[str, int]:
        """Get API usage statistics per endpoint."""
        client = await self._get_client()
        try:
            # Get API logs from last 24 hours
            from datetime import datetime, timedelta

            one_day_ago = (datetime.now() - timedelta(hours=24)).isoformat()
            time_col = await self._resolve_audit_time_column(client)

            # Use audit_logs table with api_request action pattern
            result = await (
                client.table("audit_logs")
                .select("details, action")
                .like("action", "api_request:%")
                .gte(time_col, one_day_ago)
                .execute()
            )

            # Process results - endpoint is stored in details.endpoint
            usage_stats = {}
            if result.data:
                for item in result.data:
                    details = item.get("details") or {}
                    endpoint = details.get("endpoint", "unknown")
                    usage_stats[endpoint] = usage_stats.get(endpoint, 0) + 1

            return usage_stats
        except Exception as e:
            logger.error(f"Failed to get API usage stats: {str(e)}")
            return {}

    async def get_error_trends(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get error trends aggregated by hour."""
        client = await self._get_client()
        try:
            from datetime import datetime, timedelta

            start_time = (datetime.now() - timedelta(hours=hours)).isoformat()
            time_col = await self._resolve_audit_time_column(client)

            # Get error logs from audit_logs (API metrics stored there)
            result = await (
                client.table("audit_logs")
                .select(f"details, {time_col}")
                .like("action", "api_request:%")
                .gte(time_col, start_time)
                .order(time_col, desc=True)
                .execute()
            )

            # Filter for errors (status_code >= 400 in details)
            errors = []
            for log in result.data or []:
                details = log.get("details", {}) or {}
                status_code = self._extract_status_code(details) or 0
                endpoint = details.get("endpoint")
                if status_code >= 400 and endpoint:
                    errors.append(
                        {
                            "timestamp": log.get(time_col),
                            "endpoint": endpoint,
                            "status_code": status_code,
                            "error_message": details.get("error_message"),
                        }
                    )

            # Group by hour
            hourly_errors: Dict[str, Dict[str, Any]] = {}
            for error in errors:
                timestamp = error.get("timestamp", "")
                hour = timestamp[:13] if timestamp else "unknown"  # YYYY-MM-DDTHH

                if hour not in hourly_errors:
                    hourly_errors[hour] = {
                        "hour": hour,
                        "count": 0,
                        "4xx_count": 0,
                        "5xx_count": 0,
                        "errors": [],
                    }

                status_code = error.get("status_code", 0)
                hourly_errors[hour]["count"] += 1

                if 400 <= status_code < 500:
                    hourly_errors[hour]["4xx_count"] += 1
                elif status_code >= 500:
                    hourly_errors[hour]["5xx_count"] += 1

                hourly_errors[hour]["errors"].append(
                    {
                        "endpoint": error.get("endpoint"),
                        "status_code": status_code,
                        "message": error.get("error_message", ""),
                    }
                )

            # Convert to list and sort
            trends = sorted(hourly_errors.values(), key=lambda x: x["hour"])

            return trends
        except Exception as e:
            logger.error(f"Failed to get error trends: {str(e)}")
            return []

    async def get_login_failure_stats(self) -> Dict[str, Any]:
        """Get login failure statistics grouped by user and IP."""
        client = await self._get_client()
        try:
            from datetime import datetime, timedelta

            seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
            time_col = await self._resolve_audit_time_column(client)

            # Derive failed signin attempts from real api_request logs.
            result = await (
                client.table("audit_logs")
                .select(f"user_id, ip_address, details, {time_col}")
                .like("action", "api_request:%")
                .gte(time_col, seven_days_ago)
                .execute()
            )

            failed_logins = []
            for row in result.data or []:
                details = row.get("details") or {}
                if (
                    details.get("endpoint") == "/v1/auth/signin"
                    and self._extract_status_code(details) == 401
                ):
                    failed_logins.append(row)

            # Group by user
            by_user: Dict[str, int] = {}
            for login in failed_logins:
                user_id = login.get("user_id", "unknown")
                by_user[user_id] = by_user.get(user_id, 0) + 1

            # Group by IP
            by_ip: Dict[str, int] = {}
            for login in failed_logins:
                ip = login.get("ip_address", "unknown")
                by_ip[ip] = by_ip.get(ip, 0) + 1

            # Time series (by day)
            by_date: Dict[str, int] = {}
            for login in failed_logins:
                date = str(login.get(time_col, ""))[:10]
                by_date[date] = by_date.get(date, 0) + 1

            time_series = [
                {"date": date, "count": count}
                for date, count in sorted(by_date.items())
            ]

            return {
                "total_failures_7d": len(failed_logins),
                "by_user": by_user,
                "by_ip": by_ip,
                "time_series": time_series,
                "top_failing_users": sorted(
                    [(user, count) for user, count in by_user.items()],
                    key=lambda x: x[1],
                    reverse=True,
                )[:10],
                "top_failing_ips": sorted(
                    [(ip, count) for ip, count in by_ip.items()],
                    key=lambda x: x[1],
                    reverse=True,
                )[:10],
            }
        except Exception as e:
            logger.error(f"Failed to get login failure stats: {str(e)}")
            return {
                "total_failures_7d": 0,
                "by_user": {},
                "by_ip": {},
                "time_series": [],
                "top_failing_users": [],
                "top_failing_ips": [],
            }

