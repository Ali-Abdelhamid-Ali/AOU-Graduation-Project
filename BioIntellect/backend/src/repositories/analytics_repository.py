from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.db.supabase.client import SupabaseProvider
from src.observability.logger import get_logger
from src.repositories.schema_compat import (
    audit_payload,
    build_follow_up_appointment,
    normalize_audit_log,
    normalize_ecg_result_record,
    normalize_mri_result_record,
)
from src.services.infrastructure.memory_cache import global_cache
from src.services.infrastructure.retry_utils import async_retry

logger = get_logger("repository.analytics")


class AnalyticsRepository:
    """Analytics Repository for aggregated clinical data."""

    def __init__(self):
        self.cache = global_cache
        self._audit_time_column: Optional[str] = None

    async def _get_client(self):
        return await SupabaseProvider.get_admin()

    async def _resolve_audit_time_column(self, _client) -> str:
        if not self._audit_time_column:
            self._audit_time_column = "created_at"
        return self._audit_time_column

    @staticmethod
    def _extract_status_code(payload: Any) -> Optional[int]:
        if not isinstance(payload, dict):
            return None
        try:
            value = payload.get("status_code")
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    async def _list_follow_up_appointments(self, patient_id: str) -> List[Dict[str, Any]]:
        client = await self._get_client()
        result = await (
            client.table("medical_cases")
            .select(
                "id, patient_id, assigned_doctor_id, follow_up_date, status, notes, chief_complaint, metadata"
            )
            .eq("patient_id", patient_id)
            .not_.is_("follow_up_date", "null")
            .order("follow_up_date", desc=True)
            .execute()
        )

        case_rows = result.data or []
        doctor_ids = {
            row.get("assigned_doctor_id")
            for row in case_rows
            if row.get("assigned_doctor_id")
        }
        doctors_by_id: Dict[str, Dict[str, Any]] = {}
        if doctor_ids:
            doctors_result = await (
                client.table("doctors")
                .select("id, first_name, last_name, qualification")
                .in_("id", list(doctor_ids))
                .execute()
            )
            doctors_by_id = {
                row["id"]: row for row in (doctors_result.data or []) if row.get("id")
            }

        appointments: List[Dict[str, Any]] = []
        for row in case_rows:
            appointment = build_follow_up_appointment(
                row,
                doctor=doctors_by_id.get(str(row.get("assigned_doctor_id") or "")),
            )
            if appointment:
                appointments.append(appointment)
        return appointments

    async def _list_api_audit_logs_since(self, start_time: str) -> List[Dict[str, Any]]:
        client = await self._get_client()
        time_col = await self._resolve_audit_time_column(client)
        result = await (
            client.table("audit_logs")
            .select(f"id, user_id, ip_address, action, changes, {time_col}")
            .like("action", "api_request:%")
            .gte(time_col, start_time)
            .order(time_col, desc=True)
            .limit(30000)
            .execute()
        )
        return result.data or []

    async def get_patient_stats(self, patient_id: str) -> Dict[str, Any]:
        """Get aggregated stats for a patient dashboard."""
        client = await self._get_client()
        today = datetime.now().date().isoformat()

        results = await asyncio.gather(
            client.table("ecg_results")
            .select("id", count="exact")
            .eq("patient_id", patient_id)
            .execute(),
            client.table("mri_segmentation_results")
            .select("id", count="exact")
            .eq("patient_id", patient_id)
            .execute(),
            self._list_follow_up_appointments(patient_id),
            client.table("ecg_results")
            .select(
                "id, rhythm_classification, rhythm_confidence, analysis_status, created_at"
            )
            .eq("patient_id", patient_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute(),
            client.table("mri_segmentation_results")
            .select(
                "id, analysis_status, detected_abnormalities, measurements, severity_score, created_at"
            )
            .eq("patient_id", patient_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute(),
            return_exceptions=True,
        )

        ecg_count_res, mri_count_res, appointments_res, latest_ecg_res, latest_mri_res = (
            results
        )

        appointments = []
        if not isinstance(appointments_res, Exception):
            appointments = [
                item
                for item in appointments_res
                if str(item.get("appointment_date") or "") >= today
            ]
            appointments.sort(
                key=lambda item: (
                    str(item.get("appointment_date") or ""),
                    str(item.get("appointment_time") or ""),
                )
            )

        latest_ecg = None
        if not isinstance(latest_ecg_res, Exception) and latest_ecg_res.data:
            latest_ecg = normalize_ecg_result_record(latest_ecg_res.data[0])

        latest_mri = None
        if not isinstance(latest_mri_res, Exception) and latest_mri_res.data:
            latest_mri = normalize_mri_result_record(latest_mri_res.data[0])

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
            "next_appointment": appointments[0] if appointments else None,
            "latest_ecg": latest_ecg,
            "latest_mri": latest_mri,
        }

    async def get_health_trends(
        self, patient_id: str, days: int = 30
    ) -> List[Dict[str, Any]]:
        """Fetch health trend data for visualizations."""
        return [
            {"date": "2024-03-01", "score": 85},
            {"date": "2024-03-05", "score": 88},
            {"date": "2024-03-10", "score": 92},
            {"date": "2024-03-15", "score": 90},
            {"date": "2024-03-20", "score": 95},
        ]

    async def list_appointments(self, patient_id: str) -> List[Dict[str, Any]]:
        """Fetch follow-up appointments derived from medical cases."""
        try:
            return await self._list_follow_up_appointments(patient_id)
        except Exception as e:
            logger.error(
                f"Error listing appointments for patient {patient_id}: {str(e)}"
            )
            return []

    @async_retry(max_retries=3)
    async def update_appointment(self, appointment_id: str, data: dict):
        """Update follow-up appointment data stored on medical_cases."""
        client = await self._get_client()
        try:
            current = await (
                client.table("medical_cases")
                .select(
                    "id, patient_id, assigned_doctor_id, follow_up_date, status, notes, chief_complaint, metadata"
                )
                .eq("id", appointment_id)
                .limit(1)
                .execute()
            )
            if not current.data:
                return None

            case_record = current.data[0]
            metadata = case_record.get("metadata")
            metadata = dict(metadata) if isinstance(metadata, dict) else {}
            update_data: Dict[str, Any] = {}

            appointment_date = data.get("appointment_date")
            if appointment_date:
                update_data["follow_up_date"] = str(appointment_date)[:10]

            if data.get("doctor_id"):
                update_data["assigned_doctor_id"] = data["doctor_id"]

            if data.get("appointment_time") is not None:
                metadata["appointment_time"] = data.get("appointment_time")
            if data.get("status") is not None:
                metadata["appointment_status"] = data.get("status")
            if data.get("reason") is not None:
                metadata["appointment_reason"] = data.get("reason")
            if data.get("department") is not None:
                metadata["department"] = data.get("department")
            if data.get("notes") is not None:
                metadata["appointment_notes"] = data.get("notes")

            if metadata:
                update_data["metadata"] = metadata

            if update_data:
                updated = await (
                    client.table("medical_cases")
                    .update(update_data)
                    .eq("id", appointment_id)
                    .execute()
                )
                case_record = updated.data[0] if updated.data else case_record

            await self.cache.clear()
            return build_follow_up_appointment(case_record)
        except Exception as e:
            logger.error(f"Error updating appointment {appointment_id}: {str(e)}")
            return None

    async def get_total_users_count(self) -> int:
        client = await self._get_client()
        try:
            result = await client.table("user_roles").select("id", count="exact").execute()
            return result.count or 0
        except Exception as e:
            logger.error(f"Error getting total users count: {str(e)}")
            return 0

    async def get_active_users_count(self) -> int:
        client = await self._get_client()
        try:
            result = await (
                client.table("user_roles")
                .select("id", count="exact")
                .eq("is_active", True)
                .execute()
            )
            return result.count or 0
        except Exception as e:
            logger.error(f"Error getting active users count: {str(e)}")
            return 0

    async def get_system_health(self) -> str:
        client = await self._get_client()
        try:
            result = await client.table("user_roles").select("id").limit(1).execute()
            return "healthy" if result.data is not None else "warning"
        except Exception as e:
            logger.error(f"Error checking system health: {str(e)}")
            return "critical"

    async def get_audit_logs_count(self) -> int:
        client = await self._get_client()
        try:
            result = await client.table("audit_logs").select("id", count="exact").execute()
            return result.count or 0
        except Exception as e:
            logger.error(f"Error getting audit logs count: {str(e)}")
            return 0

    async def get_system_activity_summary(self) -> dict:
        try:
            return {}
        except Exception as e:
            logger.error(f"Error getting system activity summary: {str(e)}")
            return {}

    async def get_user_activity_summary(self) -> dict:
        try:
            return {}
        except Exception as e:
            logger.error(f"Error getting user activity summary: {str(e)}")
            return {}

    async def get_user_hospital_id(self, user_id: str) -> str:
        client = await self._get_client()
        try:
            for table_name in ("doctors", "nurses", "administrators"):
                result = await (
                    client.table(table_name)
                    .select("hospital_id")
                    .eq("user_id", user_id)
                    .execute()
                )
                if result.data:
                    return result.data[0]["hospital_id"]
            return user_id
        except Exception as e:
            logger.error(f"Error getting hospital ID for user {user_id}: {str(e)}")
            return user_id

    async def get_hospital_users_count(self, hospital_id: str) -> int:
        client = await self._get_client()
        try:
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
            logger.error(
                f"Error getting hospital users count for {hospital_id}: {str(e)}"
            )
            return 0

    async def get_hospital_active_users_count(self, hospital_id: str) -> int:
        client = await self._get_client()
        try:
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
            logger.error(
                f"Error getting hospital active users count for {hospital_id}: {str(e)}"
            )
            return 0

    async def get_hospital_system_health(self, hospital_id: str) -> str:
        client = await self._get_client()
        try:
            result = await (
                client.table("doctors")
                .select("id")
                .eq("hospital_id", hospital_id)
                .limit(1)
                .execute()
            )
            return "healthy" if result.data is not None else "warning"
        except Exception as e:
            logger.error(
                f"Error checking hospital system health for {hospital_id}: {str(e)}"
            )
            return "critical"

    async def get_hospital_activity_summary(self, hospital_id: str) -> dict:
        try:
            return {}
        except Exception as e:
            logger.error(
                f"Error getting hospital activity summary for {hospital_id}: {str(e)}"
            )
            return {}

    async def get_doctor_assigned_patients_count(self, doctor_id: str) -> int:
        client = await self._get_client()
        try:
            result = await (
                client.table("patients")
                .select("id", count="exact")
                .eq("primary_doctor_id", doctor_id)
                .execute()
            )
            return result.count or 0
        except Exception as e:
            logger.error(
                f"Error getting assigned patients count for doctor {doctor_id}: {str(e)}"
            )
            return 0

    async def get_doctor_pending_cases_count(self, doctor_id: str) -> int:
        client = await self._get_client()
        try:
            result = await (
                client.table("medical_cases")
                .select("id", count="exact")
                .eq("assigned_doctor_id", doctor_id)
                .eq("status", "pending_review")
                .execute()
            )
            return result.count or 0
        except Exception as e:
            logger.error(
                f"Error getting pending cases count for doctor {doctor_id}: {str(e)}"
            )
            return 0

    async def get_doctor_completed_cases_count(self, doctor_id: str) -> int:
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
            logger.error(
                f"Error getting completed cases count for doctor {doctor_id}: {str(e)}"
            )
            return 0

    async def get_doctor_workload_summary(self, doctor_id: str) -> dict:
        try:
            pending_count = await self.get_doctor_pending_cases_count(doctor_id)
            completed_count = await self.get_doctor_completed_cases_count(doctor_id)
            total_cases = pending_count + completed_count
            return {
                "pending_cases": pending_count,
                "completed_cases": completed_count,
                "total_cases": total_cases,
                "completion_rate": (completed_count / max(total_cases, 1)) * 100,
            }
        except Exception as e:
            logger.error(
                f"Error getting doctor workload summary for {doctor_id}: {str(e)}"
            )
            return {}

    async def get_nurse_assigned_patients_count(self, nurse_id: str) -> int:
        """The current schema does not assign patients directly to nurses."""
        _ = nurse_id
        return 0

    async def get_nurse_pending_tasks_count(self, nurse_id: str) -> int:
        _ = nurse_id
        return 0

    async def get_nurse_completed_tasks_count(self, nurse_id: str) -> int:
        _ = nurse_id
        return 0

    async def get_nurse_task_summary(self, nurse_id: str) -> dict:
        _ = nurse_id
        return {
            "pending_tasks": 0,
            "completed_tasks": 0,
            "total_tasks": 0,
            "completion_rate": 0.0,
        }

    async def get_user_distribution(self) -> Dict[str, int]:
        client = await self._get_client()
        try:
            result = await client.table("user_roles").select("role").execute()
            distribution: Dict[str, int] = {}
            for row in result.data or []:
                role = row.get("role") or "unknown"
                distribution[role] = distribution.get(role, 0) + 1
            return distribution
        except Exception as e:
            logger.error(f"Failed to get user distribution: {str(e)}")
            return {}

    async def get_hospital_statistics(self, hospital_id: str) -> Dict[str, Any]:
        try:
            return {
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
        except Exception as e:
            logger.error(f"Failed to get hospital statistics: {str(e)}")
            return {}

    async def get_hospital_user_distribution(self, hospital_id: str) -> Dict[str, int]:
        client = await self._get_client()
        try:
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

            def get_count(idx: int) -> int:
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
            logger.error(f"Failed to get hospital user distribution: {str(e)}")
            return {}

    async def get_hospital_user_growth(self, hospital_id: str) -> List[Dict[str, Any]]:
        try:
            _ = hospital_id
            return [
                {"date": "2024-01-01", "count": 5},
                {"date": "2024-02-01", "count": 8},
                {"date": "2024-03-01", "count": 12},
                {"date": "2024-04-01", "count": 15},
            ]
        except Exception as e:
            logger.error(f"Failed to get hospital user growth: {str(e)}")
            return []

    async def get_user_recent_activity(
        self, user_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        client = await self._get_client()
        try:
            result = await (
                client.table("audit_logs")
                .select(
                    "id, action, resource_type, resource_id, user_id, user_role, description, changes, created_at"
                )
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            activity: List[Dict[str, Any]] = []
            for row in result.data or []:
                normalized = normalize_audit_log(row)
                normalized.setdefault("entity_type", normalized.get("resource_type"))
                normalized.setdefault("entity_id", normalized.get("resource_id"))
                normalized.setdefault("performed_by", normalized.get("user_id"))
                activity.append(normalized)
            return activity
        except Exception as e:
            logger.error(f"Failed to get user recent activity: {str(e)}")
            return []

    async def get_user_growth_trend(self) -> List[Dict[str, Any]]:
        try:
            return [
                {"month": "Jan 2024", "total_users": 100, "new_users": 10},
                {"month": "Feb 2024", "total_users": 115, "new_users": 15},
                {"month": "Mar 2024", "total_users": 130, "new_users": 15},
                {"month": "Apr 2024", "total_users": 150, "new_users": 20},
            ]
        except Exception as e:
            logger.error(f"Failed to get user growth trend: {str(e)}")
            return []

    async def get_api_usage_stats(self) -> Dict[str, int]:
        client = await self._get_client()
        try:
            start_time = (datetime.now() - timedelta(hours=24)).isoformat()
            time_col = await self._resolve_audit_time_column(client)
            result = await (
                client.table("audit_logs")
                .select(f"changes, {time_col}")
                .like("action", "api_request:%")
                .gte(time_col, start_time)
                .execute()
            )

            usage_stats: Dict[str, int] = {}
            for item in result.data or []:
                payload = audit_payload(item)
                endpoint = payload.get("endpoint", "unknown")
                usage_stats[endpoint] = usage_stats.get(endpoint, 0) + 1
            return usage_stats
        except Exception as e:
            logger.error(f"Failed to get API usage stats: {str(e)}")
            return {}

    async def get_error_trends(self, hours: int = 24) -> List[Dict[str, Any]]:
        client = await self._get_client()
        try:
            start_time = (datetime.now() - timedelta(hours=hours)).isoformat()
            time_col = await self._resolve_audit_time_column(client)
            result = await (
                client.table("audit_logs")
                .select(f"changes, {time_col}")
                .like("action", "api_request:%")
                .gte(time_col, start_time)
                .order(time_col, desc=True)
                .execute()
            )

            errors = []
            for log in result.data or []:
                payload = audit_payload(log)
                status_code = self._extract_status_code(payload) or 0
                endpoint = payload.get("endpoint")
                if status_code >= 400 and endpoint:
                    errors.append(
                        {
                            "timestamp": log.get(time_col),
                            "endpoint": endpoint,
                            "status_code": status_code,
                            "error_message": payload.get("error_message"),
                        }
                    )

            hourly_errors: Dict[str, Dict[str, Any]] = {}
            for error in errors:
                timestamp = error.get("timestamp", "")
                hour = timestamp[:13] if timestamp else "unknown"
                bucket = hourly_errors.setdefault(
                    hour,
                    {
                        "hour": hour,
                        "count": 0,
                        "4xx_count": 0,
                        "5xx_count": 0,
                        "errors": [],
                    },
                )
                status_code = error.get("status_code", 0)
                bucket["count"] += 1
                if 400 <= status_code < 500:
                    bucket["4xx_count"] += 1
                elif status_code >= 500:
                    bucket["5xx_count"] += 1
                bucket["errors"].append(
                    {
                        "endpoint": error.get("endpoint"),
                        "status_code": status_code,
                        "message": error.get("error_message", ""),
                    }
                )

            return sorted(hourly_errors.values(), key=lambda item: item["hour"])
        except Exception as e:
            logger.error(f"Failed to get error trends: {str(e)}")
            return []

    async def get_login_failure_stats(self) -> Dict[str, Any]:
        try:
            seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
            rows = await self._list_api_audit_logs_since(seven_days_ago)

            failed_logins = []
            for row in rows:
                payload = audit_payload(row)
                if (
                    payload.get("endpoint") == "/v1/auth/signin"
                    and self._extract_status_code(payload) == 401
                ):
                    failed_logins.append(row)

            by_user: Dict[str, int] = {}
            by_ip: Dict[str, int] = {}
            by_date: Dict[str, int] = {}

            time_col = self._audit_time_column or "created_at"
            for login in failed_logins:
                user_key = login.get("user_id") or "unknown"
                ip_key = login.get("ip_address") or "unknown"
                date_key = str(login.get(time_col, ""))[:10]
                by_user[user_key] = by_user.get(user_key, 0) + 1
                by_ip[ip_key] = by_ip.get(ip_key, 0) + 1
                by_date[date_key] = by_date.get(date_key, 0) + 1

            return {
                "total_failures_7d": len(failed_logins),
                "by_user": by_user,
                "by_ip": by_ip,
                "time_series": [
                    {"date": date, "count": count}
                    for date, count in sorted(by_date.items())
                ],
                "top_failing_users": sorted(
                    by_user.items(), key=lambda item: item[1], reverse=True
                )[:10],
                "top_failing_ips": sorted(
                    by_ip.items(), key=lambda item: item[1], reverse=True
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
