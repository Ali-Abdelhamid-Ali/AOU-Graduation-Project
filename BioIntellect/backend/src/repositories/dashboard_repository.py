"""
Dashboard Repository - Advanced metrics and analytics for Admin/Super Admin dashboards.

Based on SRE and Observability principles:
- System Health Monitoring
- User Activity Tracking
- Security Metrics
- Business Intelligence
- Audit Trail Management
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import psutil
from src.db.supabase.client import SupabaseProvider
from src.services.infrastructure.memory_cache import global_cache
from src.observability.logger import get_logger

logger = get_logger("repository.dashboard")


class DashboardRepository:
    """
    Repository for dashboard metrics and analytics.
    Implements caching and optimized queries for real-time monitoring.
    """

    def __init__(self):
        self.cache = global_cache
        self.cache_ttl = 35  # 35 seconds cache - Balanced for performance/freshness
        self._audit_time_column: Optional[str] = None

    async def _get_client(self):
        """Get Supabase admin client."""
        return await SupabaseProvider.get_admin()

    async def _resolve_audit_time_column(self, client) -> str:
        """Resolve audit log time column across schema variants."""
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
                # Any non-schema error: still try next candidate.
                continue

        # Safe fallback for older/newer schemas.
        self._audit_time_column = "created_at"
        return self._audit_time_column

    @staticmethod
    def _extract_status_code(details: Any) -> Optional[int]:
        if not isinstance(details, dict):
            return None
        try:
            code = details.get("status_code")
            return int(code) if code is not None else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _extract_response_time_ms(details: Any) -> Optional[float]:
        if not isinstance(details, dict):
            return None
        try:
            value = details.get("response_time_ms")
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    # â”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پ
    # SYSTEM HEALTH METRICS
    # â”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پ

    async def get_system_health_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive system health metrics.
        """
        # Implement caching with 10s TTL
        cache_key = (
            f"dashboard:system_health:{datetime.now().strftime('%Y-%m-%d_%H:%M')}"
        )

        try:
            # Try to get from cache first
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                return cached_data
        except Exception as cache_err:
            logger.warning(
                f"Cache retrieval failed: {str(cache_err)}, fetching fresh data"
            )

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

            # Collect api_request logs from audit_logs.
            # This is the only reliable real source currently available.
            one_hour_res = await (
                client.table("audit_logs")
                .select(f"id, details, {time_col}")
                .like("action", "api_request:%")
                .gte(time_col, one_hour_ago)
                .order(time_col, desc=True)
                .limit(5000)
                .execute()
            )
            one_day_res = await (
                client.table("audit_logs")
                .select(f"id, details, {time_col}")
                .like("action", "api_request:%")
                .gte(time_col, one_day_ago)
                .order(time_col, desc=True)
                .limit(10000)
                .execute()
            )
            seven_days_res = await (
                client.table("audit_logs")
                .select(f"id, details, {time_col}")
                .like("action", "api_request:%")
                .gte(time_col, seven_days_ago)
                .order(time_col, desc=True)
                .limit(30000)
                .execute()
            )

            hour_logs = one_hour_res.data or []
            day_logs = one_day_res.data or []
            seven_days_logs = seven_days_res.data or []

            active_requests_count = sum(
                1 for row in hour_logs if str(row.get(time_col, "")) >= one_min_ago
            )
            total_requests_last_hour = len(hour_logs)

            hour_statuses = [
                self._extract_status_code(row.get("details")) for row in hour_logs
            ]
            hour_statuses = [s for s in hour_statuses if s is not None]
            error_count = sum(1 for s in hour_statuses if s >= 400)
            error_rate = (
                round((error_count / len(hour_statuses)) * 100, 2)
                if hour_statuses
                else 0.0
            )

            response_times = [
                self._extract_response_time_ms(row.get("details")) for row in hour_logs
            ]
            response_times = [v for v in response_times if v is not None]
            response_time_avg = (
                round(sum(response_times) / len(response_times), 2)
                if response_times
                else 0.0
            )

            day_statuses = [
                self._extract_status_code(row.get("details")) for row in day_logs
            ]
            day_statuses = [s for s in day_statuses if s is not None]
            uptime_24h = (
                round((sum(1 for s in day_statuses if s < 500) / len(day_statuses)) * 100, 2)
                if day_statuses
                else 0.0
            )

            week_statuses = [
                self._extract_status_code(row.get("details")) for row in seven_days_logs
            ]
            week_statuses = [s for s in week_statuses if s is not None]
            uptime_7d = (
                round((sum(1 for s in week_statuses if s < 500) / len(week_statuses)) * 100, 2)
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

            # Cache the result
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

    # â”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پ
    # USER ACTIVITY METRICS
    # â”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پ

    async def get_user_activity_metrics(self) -> Dict[str, Any]:
        """
        Get user activity metrics for operational monitoring.
        Aggregates from patients, doctors, and administrators tables.
        """
        try:
            client = await self._get_client()
            time_col = await self._resolve_audit_time_column(client)
            import asyncio

            fifteen_min_ago = (datetime.now() - timedelta(minutes=15)).isoformat()
            one_day_ago = (datetime.now() - timedelta(hours=24)).isoformat()

            results = await asyncio.gather(
                client.table("audit_logs")
                .select(f"user_id, details, {time_col}")
                .like("action", "api_request:%")
                .gte(time_col, one_day_ago)
                .order(time_col, desc=True)
                .limit(10000)
                .execute(),
                client.table("audit_logs")
                .select(f"user_id, ip_address, action, details, {time_col}")
                .eq("action", "USER_LOGIN")
                .order(time_col, desc=True)
                .limit(50)
                .execute(),
                client.table("administrators").select("id", count="exact").execute(),
                client.table("doctors").select("id", count="exact").execute(),
                client.table("patients").select("id", count="exact").execute(),
                return_exceptions=True,
            )

            api_logs_res = results[0] if not isinstance(results[0], BaseException) else None
            recent_logins_res = results[1] if not isinstance(results[1], BaseException) else None
            admin_res = results[2] if not isinstance(results[2], BaseException) else None
            doctor_res = results[3] if not isinstance(results[3], BaseException) else None
            patient_res = results[4] if not isinstance(results[4], BaseException) else None

            api_logs = api_logs_res.data if api_logs_res else []

            active_users_now = {
                log.get("user_id")
                for log in api_logs
                if log.get("user_id") and str(log.get(time_col, "")) >= fifteen_min_ago
            }
            active_users_24h = {
                log.get("user_id")
                for log in api_logs
                if log.get("user_id")
            }

            failed_login_attempts = []
            for log in api_logs:
                details = log.get("details") or {}
                endpoint = details.get("endpoint")
                status_code = self._extract_status_code(details)
                if endpoint == "/v1/auth/signin" and status_code in (401, 429):
                    failed_login_attempts.append(
                        {
                            "user_id": log.get("user_id"),
                            "ip_address": log.get("ip_address"),
                            "status_code": status_code,
                            "timestamp": log.get(time_col),
                            "endpoint": endpoint,
                        }
                    )

            total_users = (
                (admin_res.count if admin_res else 0)
                + (doctor_res.count if doctor_res else 0)
                + (patient_res.count if patient_res else 0)
            )

            return {
                "active_users_now": len(active_users_now),
                "active_users_24h": len(active_users_24h),
                "total_users": total_users,
                "recent_logins": recent_logins_res.data if recent_logins_res else [],
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

    # â”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پ
    # BUSINESS METRICS
    # â”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پ

    async def get_business_metrics(self) -> Dict[str, Any]:
        """
        Get business/clinical operations metrics.
        Uses medical_cases table.
        """
        try:
            client = await self._get_client()
            import asyncio

            # Try to query medical_cases (fallback from clinical_cases)
            try:
                cases_result = (
                    await client.table("medical_cases")
                    .select("status", count="exact")
                    .execute()
                )
            except Exception:
                # If medical_cases also fails, return 0
                cases_result = None

            # Parallel query for other metrics if tables exist
            # Assuming ecg_results and mri_segmentation_results might exist or fail
            results = await asyncio.gather(
                client.table("ecg_results").select("id", count="exact").execute(),
                client.table("mri_segmentation_results")
                .select("id", count="exact")
                .execute(),
                return_exceptions=True,
            )

            ecg_result = (
                results[0] if not isinstance(results[0], BaseException) else None
            )
            mri_result = (
                results[1] if not isinstance(results[1], BaseException) else None
            )

            # Process cases by status
            cases_data = (
                cases_result.data
                if cases_result and hasattr(cases_result, "data")
                else []
            )
            cases_by_status: Dict[str, int] = {}
            for case in cases_data:
                status = case.get("status", "unknown")
                cases_by_status[status] = cases_by_status.get(status, 0) + 1

            return {
                "total_cases": cases_result.count if cases_result else 0,
                "cases_by_status": cases_by_status,
                "ecg_analysis_count": ecg_result.count if ecg_result else 0,
                "mri_analysis_count": mri_result.count if mri_result else 0,
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

    # â”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پ
    # SECURITY METRICS (Super Admin)
    # â”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پ

    async def get_security_metrics(self) -> Dict[str, Any]:
        """
        Get security-related metrics for threat detection.
        """
        try:
            client = await self._get_client()
            time_col = await self._resolve_audit_time_column(client)

            seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
            api_logs_result = await (
                client.table("audit_logs")
                .select(f"id, user_id, ip_address, action, details, {time_col}")
                .like("action", "api_request:%")
                .gte(time_col, seven_days_ago)
                .order(time_col, desc=True)
                .limit(30000)
                .execute()
            )
            api_logs = api_logs_result.data or []

            failed_logins = []
            rate_limit_violations = 0
            escalation_events = []
            for event in api_logs:
                details = event.get("details") or {}
                endpoint = details.get("endpoint", "")
                status_code = self._extract_status_code(details)

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

            # Group by IP to find suspicious IPs
            ip_failures: Dict[str, int] = {}
            for login in failed_logins:
                ip = login.get("ip_address", "unknown")
                ip_failures[ip] = ip_failures.get(ip, 0) + 1

            # Suspicious IPs (more than 5 failed attempts)
            suspicious_ips = [
                {"ip": ip, "failure_count": count}
                for ip, count in ip_failures.items()
                if count > 5
            ]

            # Group failed logins by date for trend chart
            login_trends: Dict[str, int] = {}
            for login in failed_logins:
                date = str(login.get(time_col, ""))[:10]
                login_trends[date] = login_trends.get(date, 0) + 1

            # Sort trends by date
            sorted_trends = [
                {"date": date, "count": count}
                for date, count in sorted(login_trends.items())
            ]

            alerts = []
            for event in escalation_events[:10]:
                user_id = event.get("user_id") or "unknown"
                details = event.get("details") or {}
                alerts.append(
                    {
                        "id": event.get("id"),
                        "type": "unauthorized_access",
                        "severity": "high",
                        "message": f"Unauthorized access attempt by user {str(user_id)[:8]}",
                        "timestamp": event.get(time_col),
                        "details": details,
                    }
                )

            return {
                "failed_login_trends": sorted_trends,
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

    # â”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پ
    # ADMIN AUDIT TRAIL (Super Admin)
    # â”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پ

    async def get_admin_audit_trail(
        self, limit: int = 50, admin_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get admin activity audit trail with statistics.
        """
        try:
            client = await self._get_client()
            time_col = await self._resolve_audit_time_column(client)

            # Query audit_logs for admin activities
            query = (
                client.table("audit_logs")
                .select("*")
                .limit(limit)
                .order(time_col, desc=True)
            )

            # Filter by specific admin if requested
            if admin_id:
                query = query.eq("user_id", admin_id)

            result = await query.execute()
            audit_logs = result.data or []

            # Format logs
            formatted_logs = []
            by_admin_stats = {}

            for log in audit_logs:
                details = log.get("details") or {}
                # Format entry
                formatted_logs.append(
                    {
                        "id": log.get("id"),
                        "who": log.get("user_id"),
                        "role": log.get("user_role"),
                        "what": log.get("action"),
                        "when": log.get(time_col),
                        "where": log.get("ip_address"),
                        "resource_type": log.get("resource_type"),
                        "resource_id": log.get("resource_id"),
                        "before_value": details.get("before"),
                        "after_value": details.get("after"),
                        "outcome": log.get("outcome", "success"),
                        "action_type": log.get("action", "unknown"),
                        "admin_id": log.get("user_id"),
                        "action": log.get("description") or log.get("action"),
                    }
                )

                # Update stats
                admin_user = log.get("user_id", "unknown")
                by_admin_stats[admin_user] = by_admin_stats.get(admin_user, 0) + 1

            return {
                "admin_actions": formatted_logs,
                "total_actions": len(formatted_logs),
                "by_admin": by_admin_stats,
            }

        except Exception as e:
            logger.error(f"Failed to get admin audit trail: {str(e)}")
            return {"admin_actions": [], "total_actions": 0, "by_admin": {}}

    # â”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پ
    # STRATEGIC ANALYTICS (Super Admin)
    # â”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پ

    async def get_strategic_analytics(self, timeframe: str = "week") -> Dict[str, Any]:
        """
        Get long-term strategic analytics.
        """
        try:
            client = await self._get_client()
            time_col = await self._resolve_audit_time_column(client)

            # Determine time range
            if timeframe == "month":
                days = 30
            else:  # week
                days = 7

            start_date = (datetime.now() - timedelta(days=days)).isoformat()

            # User growth trend - Use administrators as proxy if created_at is available
            # Or try querying all three tables

            # For simplicity in this fix, we'll try just administrators
            user_growth_result = (
                await client.table("administrators")
                .select("created_at")
                .gte("created_at", start_date)
                .execute()
            )

            users_data = user_growth_result.data or []

            # Group by date
            growth_by_date: Dict[str, int] = {}
            for user in users_data:
                date = user.get("created_at", "")[:10]
                growth_by_date[date] = growth_by_date.get(date, 0) + 1

            user_growth_trend = [
                {"date": date, "new_users": count}
                for date, count in sorted(growth_by_date.items())
            ]

            error_logs_result = (
                await client.table("audit_logs")
                .select(f"details, {time_col}")
                .like("action", "api_request:%")
                .gte(time_col, start_date)
                .execute()
            )

            errors_4xx = 0
            errors_5xx = 0
            for row in error_logs_result.data or []:
                status_code = self._extract_status_code(row.get("details")) or 0
                if 400 <= status_code < 500:
                    errors_4xx += 1
                elif status_code >= 500:
                    errors_5xx += 1

            error_pattern_list = [
                {"pattern": "Client Errors (4xx)", "count": errors_4xx},
                {"pattern": "Server Errors (5xx)", "count": errors_5xx},
            ]

            return {
                "user_growth_trend": user_growth_trend,
                "error_patterns": error_pattern_list,
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

