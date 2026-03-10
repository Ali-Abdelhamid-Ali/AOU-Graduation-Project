"""
Dashboard Repository - Advanced metrics and analytics for Admin/Super Admin dashboards.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import psutil

from src.db.supabase.client import SupabaseProvider
from src.observability.logger import get_logger
from src.repositories.schema_compat import audit_payload, normalize_audit_log
from src.services.infrastructure.memory_cache import global_cache

logger = get_logger("repository.dashboard")


class DashboardRepository:
    """Repository for dashboard metrics and analytics."""

    def __init__(self):
        self.cache = global_cache
        self.cache_ttl = 35
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
            code = payload.get("status_code")
            return int(code) if code is not None else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _extract_response_time_ms(payload: Any) -> Optional[float]:
        if not isinstance(payload, dict):
            return None
        try:
            value = payload.get("response_time_ms")
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    async def _list_api_logs_since(self, start_time: str):
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
        return result.data or [], time_col

    async def get_system_health_metrics(self) -> Dict[str, Any]:
        cache_key = f"dashboard:system_health:{datetime.now().strftime('%Y-%m-%d_%H:%M')}"
        try:
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                return cached_data
        except Exception:
            pass

        try:
            client = await self._get_client()
            time_col = await self._resolve_audit_time_column(client)

            db_check_result = await (
                client.table("administrators").select("id").limit(1).execute()
            )
            db_status = (
                "healthy"
                if db_check_result and db_check_result.data is not None
                else "degraded"
            )

            one_min_ago = (datetime.now() - timedelta(minutes=1)).isoformat()
            one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
            one_day_ago = (datetime.now() - timedelta(hours=24)).isoformat()
            seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()

            one_hour_logs, _ = await self._list_api_logs_since(one_hour_ago)
            one_day_logs, _ = await self._list_api_logs_since(one_day_ago)
            seven_days_logs, _ = await self._list_api_logs_since(seven_days_ago)

            active_requests_count = sum(
                1 for row in one_hour_logs if str(row.get(time_col, "")) >= one_min_ago
            )
            total_requests_last_hour = len(one_hour_logs)

            hour_payloads = [audit_payload(row) for row in one_hour_logs]
            hour_statuses = [
                self._extract_status_code(payload)
                for payload in hour_payloads
                if self._extract_status_code(payload) is not None
            ]
            response_times = [
                self._extract_response_time_ms(payload)
                for payload in hour_payloads
                if self._extract_response_time_ms(payload) is not None
            ]

            error_count = sum(1 for code in hour_statuses if code >= 400)
            error_rate = (
                round((error_count / len(hour_statuses)) * 100, 2)
                if hour_statuses
                else 0.0
            )
            response_time_avg = (
                round(sum(response_times) / len(response_times), 2)
                if response_times
                else 0.0
            )

            day_statuses = [
                self._extract_status_code(audit_payload(row))
                for row in one_day_logs
                if self._extract_status_code(audit_payload(row)) is not None
            ]
            week_statuses = [
                self._extract_status_code(audit_payload(row))
                for row in seven_days_logs
                if self._extract_status_code(audit_payload(row)) is not None
            ]

            uptime_24h = (
                round((sum(1 for code in day_statuses if code < 500) / len(day_statuses)) * 100, 2)
                if day_statuses
                else 0.0
            )
            uptime_7d = (
                round((sum(1 for code in week_statuses if code < 500) / len(week_statuses)) * 100, 2)
                if week_statuses
                else 0.0
            )

            metrics = {
                "response_time_avg": response_time_avg,
                "error_rate": error_rate,
                "uptime_24h": uptime_24h,
                "uptime_7d": uptime_7d,
                "active_requests": active_requests_count,
                "database_status": db_status,
                "cache_status": "healthy" if await self.cache.ping() else "disabled",
                "total_requests_last_hour": total_requests_last_hour,
                "timestamp": datetime.now().isoformat(),
                "cpu_load": psutil.cpu_percent(interval=0.1),
                "memory_usage": psutil.virtual_memory().percent,
                "memory_used_gb": round(psutil.virtual_memory().used / (1024**3), 2),
            }

            try:
                await self.cache.set(cache_key, metrics, ttl_seconds=self.cache_ttl)
            except Exception:
                pass
            return metrics
        except Exception as e:
            logger.error(f"Failed to get system health metrics: {str(e)}")
            return {
                "response_time_avg": 0,
                "error_rate": 0,
                "uptime_24h": 0,
                "uptime_7d": 0,
                "active_requests": 0,
                "database_status": "unknown",
                "error": str(e),
            }

    async def get_user_activity_metrics(self) -> Dict[str, Any]:
        try:
            client = await self._get_client()
            time_col = await self._resolve_audit_time_column(client)

            fifteen_min_ago = (datetime.now() - timedelta(minutes=15)).isoformat()
            one_day_ago = (datetime.now() - timedelta(hours=24)).isoformat()

            api_logs, _ = await self._list_api_logs_since(one_day_ago)
            recent_logins_res = await (
                client.table("audit_logs")
                .select(f"user_id, ip_address, action, changes, {time_col}")
                .eq("action", "USER_LOGIN")
                .order(time_col, desc=True)
                .limit(50)
                .execute()
            )

            admin_res = await (
                client.table("administrators").select("id", count="exact").execute()
            )
            doctor_res = await (
                client.table("doctors").select("id", count="exact").execute()
            )
            patient_res = await (
                client.table("patients").select("id", count="exact").execute()
            )

            active_users_now = {
                row.get("user_id")
                for row in api_logs
                if row.get("user_id") and str(row.get(time_col, "")) >= fifteen_min_ago
            }
            active_users_24h = {row.get("user_id") for row in api_logs if row.get("user_id")}

            failed_login_attempts = []
            for row in api_logs:
                payload = audit_payload(row)
                endpoint = payload.get("endpoint")
                status_code = self._extract_status_code(payload)
                if endpoint == "/v1/auth/signin" and status_code in (401, 429):
                    failed_login_attempts.append(
                        {
                            "user_id": row.get("user_id"),
                            "ip_address": row.get("ip_address"),
                            "status_code": status_code,
                            "timestamp": row.get(time_col),
                            "endpoint": endpoint,
                        }
                    )

            total_users = (
                (admin_res.count or 0) + (doctor_res.count or 0) + (patient_res.count or 0)
            )
            recent_logins = [
                normalize_audit_log(row) for row in (recent_logins_res.data or [])
            ]

            return {
                "active_users_now": len(active_users_now),
                "active_users_24h": len(active_users_24h),
                "total_users": total_users,
                "recent_logins": recent_logins,
                "failed_login_attempts": failed_login_attempts[:100],
                "active_sessions_count": len(active_users_now),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to get user activity metrics: {str(e)}")
            return {
                "active_users_now": 0,
                "active_users_24h": 0,
                "total_users": 0,
                "recent_logins": [],
                "failed_login_attempts": [],
                "active_sessions_count": 0,
                "error": str(e),
            }

    async def get_business_metrics(self) -> Dict[str, Any]:
        try:
            client = await self._get_client()
            cases_result = await client.table("medical_cases").select(
                "status", count="exact"
            ).execute()
            ecg_result = await client.table("ecg_results").select(
                "id", count="exact"
            ).execute()
            mri_result = await client.table("mri_segmentation_results").select(
                "id", count="exact"
            ).execute()

            cases_by_status: Dict[str, int] = {}
            for case in cases_result.data or []:
                status = case.get("status", "unknown")
                cases_by_status[status] = cases_by_status.get(status, 0) + 1

            return {
                "total_cases": cases_result.count or 0,
                "cases_by_status": cases_by_status,
                "ecg_analysis_count": ecg_result.count or 0,
                "mri_analysis_count": mri_result.count or 0,
                "api_usage_stats": {},
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to get business metrics: {str(e)}")
            return {
                "total_cases": 0,
                "cases_by_status": {},
                "ecg_analysis_count": 0,
                "mri_analysis_count": 0,
                "api_usage_stats": {},
                "error": str(e),
            }

    async def get_security_metrics(self) -> Dict[str, Any]:
        try:
            seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
            api_logs, time_col = await self._list_api_logs_since(seven_days_ago)

            failed_logins = []
            rate_limit_violations = 0
            escalation_events = []
            for event in api_logs:
                payload = audit_payload(event)
                endpoint = payload.get("endpoint", "")
                status_code = self._extract_status_code(payload)

                if endpoint == "/v1/auth/signin" and status_code == 401:
                    failed_logins.append(event)
                if endpoint == "/v1/auth/signin" and status_code == 429:
                    rate_limit_violations += 1
                if status_code == 403 and (
                    "/super-admin/" in endpoint
                    or "/admin/" in endpoint
                    or endpoint == "/v1/users/roles"
                ):
                    escalation_events.append(event)

            ip_failures: Dict[str, int] = {}
            for login in failed_logins:
                ip = login.get("ip_address", "unknown")
                ip_failures[ip] = ip_failures.get(ip, 0) + 1

            suspicious_ips = [
                {"ip": ip, "failure_count": count}
                for ip, count in ip_failures.items()
                if count > 5
            ]

            login_trends: Dict[str, int] = {}
            for login in failed_logins:
                date = str(login.get(time_col, ""))[:10]
                login_trends[date] = login_trends.get(date, 0) + 1

            alerts = []
            for event in escalation_events[:10]:
                payload = audit_payload(event)
                alerts.append(
                    {
                        "id": event.get("id"),
                        "type": "unauthorized_access",
                        "severity": "high",
                        "message": f"Unauthorized access attempt by user {str(event.get('user_id') or 'unknown')[:8]}",
                        "timestamp": event.get(time_col),
                        "details": payload,
                    }
                )

            return {
                "failed_login_trends": [
                    {"date": date, "count": count}
                    for date, count in sorted(login_trends.items())
                ],
                "suspicious_ips": suspicious_ips,
                "total_failed_logins_7d": len(failed_logins),
                "rate_limit_violations": rate_limit_violations,
                "permission_escalation_attempts": len(escalation_events),
                "security_alerts": alerts,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to get security metrics: {str(e)}")
            return {
                "failed_login_trends": [],
                "suspicious_ips": [],
                "total_failed_logins_7d": 0,
                "rate_limit_violations": 0,
                "permission_escalation_attempts": 0,
                "error": str(e),
            }

    async def get_admin_audit_trail(
        self, limit: int = 50, admin_id: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            client = await self._get_client()
            time_col = await self._resolve_audit_time_column(client)

            query = (
                client.table("audit_logs")
                .select("*")
                .limit(limit)
                .order(time_col, desc=True)
            )
            if admin_id:
                query = query.eq("user_id", admin_id)

            result = await query.execute()
            audit_logs = result.data or []

            formatted_logs = []
            by_admin_stats: Dict[str, int] = {}
            for log in audit_logs:
                normalized = normalize_audit_log(log)
                payload = audit_payload(log)
                admin_user = log.get("user_id", "unknown")
                by_admin_stats[admin_user] = by_admin_stats.get(admin_user, 0) + 1
                formatted_logs.append(
                    {
                        "id": normalized.get("id"),
                        "who": normalized.get("user_id"),
                        "role": normalized.get("user_role"),
                        "what": normalized.get("action"),
                        "when": normalized.get(time_col),
                        "where": normalized.get("ip_address"),
                        "resource_type": normalized.get("resource_type"),
                        "resource_id": normalized.get("resource_id"),
                        "before_value": payload.get("before") or normalized.get("old_values"),
                        "after_value": payload.get("after") or normalized.get("new_values"),
                        "outcome": "success",
                        "action_type": normalized.get("action", "unknown"),
                        "admin_id": normalized.get("user_id"),
                        "action": normalized.get("description") or normalized.get("action"),
                    }
                )

            return {
                "admin_actions": formatted_logs,
                "total_actions": len(formatted_logs),
                "by_admin": by_admin_stats,
            }
        except Exception as e:
            logger.error(f"Failed to get admin audit trail: {str(e)}")
            return {"admin_actions": [], "total_actions": 0, "by_admin": {}}

    async def get_strategic_analytics(self, timeframe: str = "week") -> Dict[str, Any]:
        try:
            client = await self._get_client()
            time_col = await self._resolve_audit_time_column(client)
            days = 30 if timeframe == "month" else 7
            start_date = (datetime.now() - timedelta(days=days)).isoformat()

            growth_by_date: Dict[str, int] = {}
            for table_name in ("administrators", "doctors", "patients"):
                result = await (
                    client.table(table_name)
                    .select("created_at")
                    .gte("created_at", start_date)
                    .execute()
                )
                for row in result.data or []:
                    date_key = str(row.get("created_at", ""))[:10]
                    growth_by_date[date_key] = growth_by_date.get(date_key, 0) + 1

            user_growth_trend = [
                {"date": date, "new_users": count}
                for date, count in sorted(growth_by_date.items())
            ]

            error_logs_result = await (
                client.table("audit_logs")
                .select(f"changes, {time_col}")
                .like("action", "api_request:%")
                .gte(time_col, start_date)
                .execute()
            )

            errors_4xx = 0
            errors_5xx = 0
            for row in error_logs_result.data or []:
                status_code = self._extract_status_code(audit_payload(row)) or 0
                if 400 <= status_code < 500:
                    errors_4xx += 1
                elif status_code >= 500:
                    errors_5xx += 1

            return {
                "user_growth_trend": user_growth_trend,
                "error_patterns": [
                    {"pattern": "Client Errors (4xx)", "count": errors_4xx},
                    {"pattern": "Server Errors (5xx)", "count": errors_5xx},
                ],
                "performance_trends": [],
                "timeframe": timeframe,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to get strategic analytics: {str(e)}")
            return {
                "user_growth_trend": [],
                "error_patterns": [],
                "performance_trends": [],
                "error": str(e),
            }
