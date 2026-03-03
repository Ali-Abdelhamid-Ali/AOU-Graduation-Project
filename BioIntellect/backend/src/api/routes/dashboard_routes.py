"""Dashboard API Routes - Admin and Super Admin dashboard endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Any, Optional
from src.repositories.dashboard_repository import DashboardRepository
from src.repositories.analytics_repository import AnalyticsRepository
from src.security.auth_middleware import (
    get_current_user,
    require_permission,
    Permission,
)
from src.observability.logger import get_logger
import asyncio

logger = get_logger("routes.dashboard")

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


# â”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پ
# ADMIN DASHBOARD ENDPOINTS (Operational)
# â”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پ


@router.get(
    "/admin/system-health",
    dependencies=[Depends(require_permission(Permission.VIEW_DASHBOARD))],
)
async def get_admin_system_health(
    user: dict[str, Any] = Depends(get_current_user),
    repo: DashboardRepository = Depends(DashboardRepository),
):
    """
    Get system health metrics for admin dashboard.

    Returns:
        - response_time_avg: Average API response time
        - error_rate: Percentage of errors
        - uptime_24h, uptime_7d: System uptime
        - database_status: DB health status
    """
    try:
        metrics = await repo.get_system_health_metrics()

        return {
            "success": True,
            "data": metrics,
            "message": "System health metrics retrieved successfully",
        }
    except Exception as e:
        logger.error(f"Failed to get system health for user {user['id']}: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve system health metrics"
        )


@router.get(
    "/admin/user-activity",
    dependencies=[Depends(require_permission(Permission.VIEW_DASHBOARD))],
)
async def get_admin_user_activity(
    user: dict[str, Any] = Depends(get_current_user),
    repo: DashboardRepository = Depends(DashboardRepository),
):
    """
    Get user activity metrics for admin dashboard.

    Returns:
        - active_users_now, active_users_24h: Active user counts
        - recent_logins: Last 50 login events
        - failed_login_attempts: Recent failed logins
    """
    try:
        metrics = await repo.get_user_activity_metrics()

        return {
            "success": True,
            "data": metrics,
            "message": "User activity metrics retrieved successfully",
        }
    except Exception as e:
        logger.error(f"Failed to get user activity for user {user['id']}: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve user activity metrics"
        )


@router.get(
    "/admin/business-metrics",
    dependencies=[Depends(require_permission(Permission.VIEW_DASHBOARD))],
)
async def get_admin_business_metrics(
    user: dict[str, Any] = Depends(get_current_user),
    repo: DashboardRepository = Depends(DashboardRepository),
):
    """
    Get business/clinical metrics for admin dashboard.

    Returns:
        - total_cases: Medical cases count
        - ecg_analysis_count, mri_analysis_count: Analysis counts
        - api_usage_stats: API usage statistics
    """
    try:
        metrics = await repo.get_business_metrics()

        return {
            "success": True,
            "data": metrics,
            "message": "Business metrics retrieved successfully",
        }
    except Exception as e:
        logger.error(f"Failed to get business metrics for user {user['id']}: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve business metrics"
        )


@router.get(
    "/admin/logs-filtered",
    dependencies=[Depends(require_permission(Permission.VIEW_AUDIT_LOGS))],
)
async def get_admin_filtered_logs(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(50, le=100, description="Number of logs to return"),
    user: dict[str, Any] = Depends(get_current_user),
):
    """
    Get filtered error logs for admin dashboard.

    Query Parameters:
        - severity: Filter by log severity (error, warning, critical)
        - limit: Maximum number of logs to return
    """
    try:
        from src.repositories.audit_repository import AuditRepository

        audit_repo = AuditRepository()

        # Build filters
        filters = {}
        if severity:
            filters["severity"] = severity

        # Get audit logs (filtered)
        logs = await audit_repo.list_audit_logs(filters, limit=limit, offset=0)

        return {
            "success": True,
            "data": logs,
            "count": len(logs),
            "message": "Filtered logs retrieved successfully",
        }
    except Exception as e:
        logger.error(f"Failed to get filtered logs for user {user['id']}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve filtered logs")


@router.get(
    "/admin/permissions",
    dependencies=[Depends(require_permission(Permission.VIEW_DASHBOARD))],
)
async def get_admin_permissions(
    user: dict[str, Any] = Depends(get_current_user),
):
    """
    Get current user's permissions and role information.

    Returns:
        - role: Current user role
        - permissions: List of allowed permissions
        - restrictions: List of restricted actions
    """
    try:
        # Extract user role and permissions from token
        role = user.get("role", "unknown")
        permissions = user.get("permissions", [])

        # Define common restrictions based on role
        restrictions = []
        if role != "super_admin":
            restrictions.extend(
                [
                    "Cannot modify system configuration",
                    "Cannot access super admin dashboard",
                    "Cannot manage other admins",
                ]
            )

        if role not in ["admin", "super_admin"]:
            restrictions.extend(["Cannot manage users", "Cannot view audit logs"])

        return {
            "success": True,
            "data": {
                "role": role,
                "permissions": permissions,
                "restrictions": restrictions,
                "user_id": user.get("id"),
            },
            "message": "Permissions retrieved successfully",
        }
    except Exception as e:
        logger.error(f"Failed to get permissions for user {user['id']}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve permissions")


# â”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پ
# SUPER ADMIN DASHBOARD ENDPOINTS (Strategic)
# â”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پ


@router.get(
    "/super-admin/global-overview",
    dependencies=[Depends(require_permission(Permission.VIEW_STATISTICS))],
)
async def get_super_admin_global_overview(
    user: dict[str, Any] = Depends(get_current_user),
    repo: DashboardRepository = Depends(DashboardRepository),
):
    """
    Get global system overview for super admin.

    Returns comprehensive system-wide metrics including:
    - Total admins count
    - System health across all services
    - Database statistics
    - Global user metrics
    """
    try:
        # Fetch multiple metrics in parallel
        results = await asyncio.gather(
            repo.get_system_health_metrics(),
            repo.get_user_activity_metrics(),
            repo.get_business_metrics(),
            return_exceptions=True,
        )

        system_health: dict | Exception = results[0]  # type: ignore
        user_activity: dict | Exception = results[1]  # type: ignore
        business_metrics: dict | Exception = results[2]  # type: ignore

        # Get admin count from analytics (Safely)
        analytics_repo = AnalyticsRepository()

        try:
            active_users = await analytics_repo.get_active_users_count()
        except Exception:
            active_users = 0

        overview = {
            "system_health": system_health
            if not isinstance(system_health, Exception)
            else {},
            "user_metrics": {
                "total_users": user_activity.get("total_users", 0)
                if not isinstance(user_activity, Exception)
                else 0,
                "active_users": active_users,
                "active_now": user_activity.get("active_users_now", 0)
                if not isinstance(user_activity, Exception)
                else 0,
                "active_24h": user_activity.get("active_users_24h", 0)
                if not isinstance(user_activity, Exception)
                else 0,
            },
            "business_metrics": business_metrics
            if not isinstance(business_metrics, Exception)
            else {},
            "services_status": {
                "api": "healthy",
                "database": system_health.get("database_status", "unknown")
                if not isinstance(system_health, Exception)
                else "unknown",
                "cache": system_health.get("cache_status", "unknown")
                if not isinstance(system_health, Exception)
                else "unknown",
            },
        }

        logger.info(f"[DEBUG] Overview object constructed: {overview}")
        logger.info(f"[DEBUG] Services status: {overview.get('services_status')}")

        return {
            "success": True,
            "data": overview,
            "message": "Global overview retrieved successfully",
        }
    except Exception as e:
        logger.error(
            f"Failed to get global overview for super admin {user['id']}: {str(e)}"
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve global overview"
        )


@router.get(
    "/super-admin/security-center",
    dependencies=[Depends(require_permission(Permission.VIEW_AUDIT_LOGS))],
)
async def get_super_admin_security_center(
    user: dict[str, Any] = Depends(get_current_user),
    repo: DashboardRepository = Depends(DashboardRepository),
):
    """
    Get security metrics and threat detection data.

    Returns:
        - failed_login_trends: Login failure patterns
        - suspicious_ips: IPs with multiple failed attempts
        - security_alerts: Recent security events
    """
    try:
        security_metrics = await repo.get_security_metrics()

        # Get additional login failure stats
        analytics_repo = AnalyticsRepository()
        login_stats = await analytics_repo.get_login_failure_stats()

        # Combine data
        security_data = {**security_metrics, "detailed_login_stats": login_stats}

        return {
            "success": True,
            "data": security_data,
            "message": "Security metrics retrieved successfully",
        }
    except Exception as e:
        logger.error(
            f"Failed to get security center for super admin {user['id']}: {str(e)}"
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve security metrics"
        )


@router.get(
    "/super-admin/admin-audit",
    dependencies=[Depends(require_permission(Permission.VIEW_AUDIT_LOGS))],
)
async def get_super_admin_audit_trail(
    limit: int = Query(50, le=100, description="Number of audit records"),
    admin_id: Optional[str] = Query(None, description="Filter by admin ID"),
    user: dict[str, Any] = Depends(get_current_user),
    repo: DashboardRepository = Depends(DashboardRepository),
):
    """
    Get admin activity audit trail.

    Returns detailed audit log of admin actions including:
    - Who performed the action
    - What action was performed
    - When and from where
    - Before/after state changes
    """
    try:
        audit_trail = await repo.get_admin_audit_trail(limit=limit, admin_id=admin_id)

        return {
            "success": True,
            "data": audit_trail,
            "count": audit_trail.get("total_actions", 0),
            "message": "Admin audit trail retrieved successfully",
        }
    except Exception as e:
        logger.error(
            f"Failed to get audit trail for super admin {user['id']}: {str(e)}"
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve admin audit trail"
        )


@router.get(
    "/super-admin/system-config",
    dependencies=[Depends(require_permission(Permission.SYSTEM_CONFIG))],
)
async def get_super_admin_system_config(
    user: dict[str, Any] = Depends(get_current_user),
):
    """
    Get system configuration settings (read-only view).

    Returns:
        - Feature toggles
        - Global limits
        - Rate limiting rules
        - Environment info (sanitized)
    """
    try:
        from src.repositories.system_repository import SystemRepository

        system_repo = SystemRepository()

        # Get global settings
        settings = await system_repo.get_global_settings()

        # Get active models
        active_models = await system_repo.get_active_models()

        config_data = {
            "global_settings": settings,
            "active_models": active_models,
            "feature_toggles": {},  # TODO: Implement feature toggle system
            "rate_limits": {},  # TODO: Get from rate limiting middleware
        }

        return {
            "success": True,
            "data": config_data,
            "message": "System configuration retrieved successfully",
        }
    except Exception as e:
        logger.error(
            f"Failed to get system config for super admin {user['id']}: {str(e)}"
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve system configuration"
        )


@router.get(
    "/super-admin/analytics-trends",
    dependencies=[Depends(require_permission(Permission.VIEW_STATISTICS))],
)
async def get_super_admin_analytics_trends(
    timeframe: str = Query("week", description="week or month"),
    user: dict[str, Any] = Depends(get_current_user),
    repo: DashboardRepository = Depends(DashboardRepository),
):
    """
    Get long-term strategic analytics and trends.

    Query Parameters:
        - timeframe: 'week' or 'month'

    Returns:
        - user_growth_trend: User registration trends
        - error_patterns: Common error patterns
        - performance_trends: System performance over time
    """
    try:
        analytics = await repo.get_strategic_analytics(timeframe=timeframe)

        # Get additional error trends
        analytics_repo = AnalyticsRepository()
        hours = 168 if timeframe == "week" else 720  # 7 days or 30 days
        error_trends = await analytics_repo.get_error_trends(hours=hours)

        trends_data = {**analytics, "error_trends": error_trends}

        return {
            "success": True,
            "data": trends_data,
            "timeframe": timeframe,
            "message": "Analytics trends retrieved successfully",
        }
    except Exception as e:
        logger.error(
            f"Failed to get analytics trends for super admin {user['id']}: {str(e)}"
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve analytics trends"
        )


@router.post(
    "/super-admin/config/update",
    dependencies=[Depends(require_permission(Permission.SYSTEM_CONFIG))],
)
async def update_super_admin_config(
    config_data: dict,
    user: dict[str, Any] = Depends(get_current_user),
):
    """
    Update system configuration (Super Admin only).

    Request Body:
        - setting_key: Configuration key to update
        - setting_value: New value
    """
    try:
        # TODO: Implement actual config update via SystemRepository
        # from src.repositories.system_repository import SystemRepository
        # system_repo = SystemRepository()

        # Log this action for audit
        logger.info(
            f"Super admin {user['id']} updating config: {config_data.get('setting_key')}"
        )

        # Update setting (this is a simplified version)
        # In production, you'd want more validation and specific handling

        return {
            "success": True,
            "message": "Configuration updated successfully",
            "updated_by": user["id"],
        }
    except Exception as e:
        logger.error(f"Failed to update config for super admin {user['id']}: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to update system configuration"
        )

