"""System Routes - Complete System Settings and Model Version Management API."""

from fastapi import APIRouter, Depends, HTTPException, Query, Response
import json
from typing import Optional, List, Any
from src.repositories.system_repository import SystemRepository
from src.validators.system_dto import (
    SystemSettingCreateDTO,
    SystemSettingUpdateDTO,
    SystemSettingResponseDTO,
    ModelVersionCreateDTO,
    ModelVersionUpdateDTO,
    ModelVersionResponseDTO,
)
from src.security.auth_middleware import (
    get_current_user,
    require_permission,
    Permission,
)
from src.observability.logger import get_logger

from datetime import datetime, timezone
import psutil
import os
import time
import httpx

logger = get_logger("routes.system")

router = APIRouter(prefix="/system", tags=["system"])
_SCHEMA_REFRESH_UNSUPPORTED_DETAIL = (
    'Automatic PostgREST schema refresh is not supported by the current Supabase '
    'setup. Run `NOTIFY pgrst, "reload schema"` manually in the Supabase SQL Editor.'
)


def _is_schema_refresh_unavailable(exc: Exception) -> bool:
    message = str(exc)
    markers = (
        "PGRST202",
        "Could not find the function",
        "pg_notify",
        "notify_schema_reload",
        "schema cache",
        "not supported",
    )
    return any(marker in message for marker in markers)

# â”پâ”پâ”پâ”پ SYSTEM MONITORING â”پâ”پâ”پâ”پ


@router.get(
    "/metrics",
    dependencies=[Depends(require_permission(Permission.VIEW_SYSTEM_METRICS))],
)
async def get_system_metrics():
    """Get real-time system hardware metrics."""
    try:
        # Get CPU, RAM, and Disk metrics pulse (interval=0.1 to get accurate immediate reading)
        cpu_percent = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        return {
            "success": True,
            "data": {
                "cpu": {
                    "usage_percent": cpu_percent,
                    "cores": psutil.cpu_count(logical=True),
                },
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "free_gb": round(memory.available / (1024**3), 2),
                    "usage_percent": memory.percent,
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "usage_percent": disk.percent,
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }
    except Exception as e:
        logger.error(f"Failed to fetch system metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch system metrics")


@router.get(
    "/db-health",
    dependencies=[Depends(require_permission(Permission.VIEW_SYSTEM_METRICS))],
)
async def get_db_health(repo: SystemRepository = Depends(SystemRepository)):
    """Get real-time database health and statistics."""
    try:
        return {
            "success": True,
            "data": await repo.get_db_health_summary(),
        }
    except Exception as e:
        logger.error(f"Failed to fetch DB health: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch database health")


# â”پâ”پâ”پâ”پ SECURITY POLICIES â”پâ”پâ”پâ”پ


@router.get(
    "/security/policies",
    dependencies=[Depends(require_permission(Permission.MANAGE_SYSTEM_SECURITY))],
)
async def get_security_policies(repo: SystemRepository = Depends(SystemRepository)):
    """Get security policy configurations."""
    try:
        # Fetch security scope settings
        policies = await repo.get_settings_by_scope("security", "global")
        return {"success": True, "data": policies}
    except Exception as e:
        logger.error(f"Failed to fetch security policies: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch security policies")


@router.post(
    "/security/policies",
    dependencies=[Depends(require_permission(Permission.MANAGE_SYSTEM_SECURITY))],
)
async def update_security_policy(
    policy_data: dict,
    user: dict[str, Any] = Depends(get_current_user),
    repo: SystemRepository = Depends(SystemRepository),
):
    """Update or create a security policy."""
    try:
        # Expecting { key, value }
        policy_data["scope"] = "security"
        policy_data["scope_id"] = "global"
        policy_data["updated_by"] = user["id"]

        # Check if exists
        existing = await repo.list_system_settings(
            {"scope": "security", "setting_key": policy_data["setting_key"]}
        )

        if existing:
            result = await repo.update_system_setting(existing[0]["id"], policy_data)
        else:
            result = await repo.create_system_setting(policy_data)

        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Failed to update security policy: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update security policy")


# Alert configuration for internal health checks (not public endpoint side effects)
ALERT_THRESHOLD = 3
failure_count = 0


async def send_health_alert(issue: str, checks: dict):
    """
    Send high-priority alert via Slack when system health degrades.
    """
    logger.critical(f"ًںڑ¨ HEALTH CHECK ALERT: {issue}")

    slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
    if slack_webhook:
        try:
            timeout = httpx.Timeout(5.0, connect=2.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                # Prepare fields for the attachment
                attachment_fields = [
                    {
                        "title": k.replace("_", " ").title(),
                        "value": f"`{v}`",
                        "short": True,
                    }
                    for k, v in checks.items()
                ]

                payload = {
                    "text": f"ًںڑ¨ *BioIntellect System Health Alert*\n*Issue:* {issue}",
                    "attachments": [
                        {
                            "color": "danger",
                            "fields": attachment_fields,
                            "footer": "BioIntellect Health Monitoring Service",
                            "ts": int(time.time()),
                        }
                    ],
                }

                response = await client.post(slack_webhook, json=payload)
                if response.status_code == 200:
                    logger.info("Successfully sent Slack health alert")
                else:
                    logger.error(
                        f"Failed to send Slack alert. Status: {response.status_code}"
                    )
        except Exception as e:
            logger.error(f"Error while sending Slack notification: {str(e)}")


@router.get("/health", tags=["system"])
async def health_check(repo: SystemRepository = Depends(SystemRepository)):
    """
    Comprehensive health check testing DB, Auth, and Logging stability.
    """
    global failure_count

    checks: dict[str, str] = {}

    # 1. Database connectivity check (read-only)
    try:
        await repo.check_admin_connection()
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {str(e)}"

    # 2. Auth service connectivity check
    try:
        await repo.check_auth_service_connection()
        checks["auth_service"] = "healthy"
    except Exception as e:
        checks["auth_service"] = f"unhealthy: {str(e)}"

    all_healthy = all(v == "healthy" for v in checks.values())

    status_code = 200 if all_healthy else 503
    return Response(
        content=json.dumps(
            {
                "status": "healthy" if all_healthy else "degraded",
                "checks": checks,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ),
        status_code=status_code,
        media_type="application/json",
    )


@router.get("/health/ready", tags=["system"])
async def readiness_check(repo: SystemRepository = Depends(SystemRepository)):
    """Readiness check for database connectivity."""
    try:
        await repo.check_system_settings_connection()
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        raise HTTPException(
            status_code=503, detail="System not ready: Database unreachable"
        )


# â”پâ”پâ”پâ”پ SYSTEM SETTINGS â”پâ”پâ”پâ”پ


@router.get(
    "/settings",
    response_model=List[SystemSettingResponseDTO],
    dependencies=[Depends(require_permission(Permission.MANAGE_SYSTEM))],
)
async def list_system_settings(
    scope: Optional[str] = Query(
        None, description="Filter by scope (global, hospital, user)"
    ),
    scope_id: Optional[str] = Query(None, description="Filter by scope ID"),
    setting_key: Optional[str] = Query(None, description="Filter by setting key"),
    is_sensitive: Optional[bool] = Query(
        None, description="Filter by sensitive settings"
    ),
    limit: int = Query(50, le=100, description="Number of results to return"),
    offset: int = Query(0, description="Number of results to skip"),
    repo: SystemRepository = Depends(SystemRepository),
):
    """List system settings with optional filtering."""
    try:
        filters: dict[str, Any] = {}
        if scope:
            filters["scope"] = scope
        if scope_id:
            filters["scope_id"] = scope_id
        if setting_key:
            filters["setting_key"] = setting_key
        if is_sensitive is not None:
            filters["is_sensitive"] = is_sensitive

        settings = await repo.list_system_settings(filters, limit, offset)
        return settings
    except Exception as e:
        logger.error(f"Failed to list system settings: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve system settings"
        )


@router.get(
    "/settings/{setting_id}",
    response_model=SystemSettingResponseDTO,
    dependencies=[Depends(require_permission(Permission.MANAGE_SYSTEM))],
)
async def get_system_setting(
    setting_id: str, repo: SystemRepository = Depends(SystemRepository)
):
    """Get a specific system setting by ID."""
    try:
        setting = await repo.get_system_setting(setting_id)
        if not setting:
            raise HTTPException(status_code=404, detail="System setting not found")
        return setting
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get system setting {setting_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system setting")


@router.get(
    "/settings/scope/{scope}/{scope_id}",
    response_model=List[SystemSettingResponseDTO],
    dependencies=[Depends(require_permission(Permission.MANAGE_SYSTEM))],
)
async def get_settings_by_scope(
    scope: str, scope_id: str, repo: SystemRepository = Depends(SystemRepository)
):
    """Get all settings for a specific scope."""
    try:
        settings = await repo.get_settings_by_scope(scope, scope_id)
        return settings
    except Exception as e:
        logger.error(f"Failed to get settings for scope {scope}/{scope_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve settings")


@router.post(
    "/settings",
    response_model=SystemSettingResponseDTO,
    dependencies=[Depends(require_permission(Permission.MANAGE_SYSTEM))],
)
async def create_system_setting(
    setting_data: SystemSettingCreateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    repo: SystemRepository = Depends(SystemRepository),
):
    """Create a new system setting."""
    try:
        setting = await repo.create_system_setting(setting_data.model_dump())
        logger.info(f"System setting created by user {user['id']}: {setting['id']}")
        return setting
    except Exception as e:
        logger.error(f"Failed to create system setting: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create system setting")


@router.put(
    "/settings/{setting_id}",
    response_model=SystemSettingResponseDTO,
    dependencies=[Depends(require_permission(Permission.MANAGE_SYSTEM))],
)
async def update_system_setting(
    setting_id: str,
    setting_data: SystemSettingUpdateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    repo: SystemRepository = Depends(SystemRepository),
):
    """Update a system setting."""
    try:
        setting = await repo.update_system_setting(
            setting_id, setting_data.model_dump(exclude_unset=True)
        )
        if not setting:
            raise HTTPException(status_code=404, detail="System setting not found")
        logger.info(f"System setting updated by user {user['id']}: {setting_id}")
        return setting
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update system setting {setting_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update system setting")


@router.delete(
    "/settings/{setting_id}",
    dependencies=[Depends(require_permission(Permission.MANAGE_SYSTEM))],
)
async def delete_system_setting(
    setting_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    repo: SystemRepository = Depends(SystemRepository),
):
    """Delete a system setting."""
    try:
        success = await repo.delete_system_setting(setting_id)
        if not success:
            raise HTTPException(status_code=404, detail="System setting not found")
        logger.info(f"System setting deleted by user {user['id']}: {setting_id}")
        return {"success": True, "message": "System setting deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete system setting {setting_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete system setting")


# â”پâ”پâ”پâ”پ MODEL VERSIONS â”پâ”پâ”پâ”پ


@router.get(
    "/models",
    response_model=List[ModelVersionResponseDTO],
    dependencies=[Depends(require_permission(Permission.MANAGE_SYSTEM))],
)
async def list_model_versions(
    model_name: Optional[str] = Query(None, description="Filter by model name"),
    model_type: Optional[str] = Query(None, description="Filter by model type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_production: Optional[bool] = Query(
        None, description="Filter by production status"
    ),
    limit: int = Query(50, le=100, description="Number of results to return"),
    offset: int = Query(0, description="Number of results to skip"),
    repo: SystemRepository = Depends(SystemRepository),
):
    """List model versions with optional filtering."""
    try:
        filters: dict[str, Any] = {}
        if model_name:
            filters["model_name"] = model_name
        if model_type:
            filters["model_type"] = model_type
        if is_active is not None:
            filters["is_active"] = is_active
        if is_production is not None:
            filters["is_production"] = is_production

        models = await repo.list_model_versions(filters, limit, offset)
        return models
    except Exception as e:
        logger.error(f"Failed to list model versions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve model versions")


@router.get(
    "/models/{model_id}",
    response_model=ModelVersionResponseDTO,
    dependencies=[Depends(require_permission(Permission.MANAGE_SYSTEM))],
)
async def get_model_version(
    model_id: str, repo: SystemRepository = Depends(SystemRepository)
):
    """Get a specific model version by ID."""
    try:
        model = await repo.get_model_version(model_id)
        if not model:
            raise HTTPException(status_code=404, detail="Model version not found")
        return model
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get model version {model_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve model version")


@router.get(
    "/models/name/{model_name}/version/{model_version}",
    response_model=ModelVersionResponseDTO,
    dependencies=[Depends(require_permission(Permission.MANAGE_SYSTEM))],
)
async def get_model_by_name_and_version(
    model_name: str,
    model_version: str,
    repo: SystemRepository = Depends(SystemRepository),
):
    """Get a specific model version by name and version."""
    try:
        model = await repo.get_model_by_name_and_version(model_name, model_version)
        if not model:
            raise HTTPException(status_code=404, detail="Model version not found")
        return model
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get model {model_name}/{model_version}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve model version")


@router.post(
    "/models",
    response_model=ModelVersionResponseDTO,
    dependencies=[Depends(require_permission(Permission.MANAGE_SYSTEM))],
)
async def create_model_version(
    model_data: ModelVersionCreateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    repo: SystemRepository = Depends(SystemRepository),
):
    """Create a new model version."""
    try:
        model = await repo.create_model_version(model_data.model_dump())
        logger.info(f"Model version created by user {user['id']}: {model['id']}")
        return model
    except Exception as e:
        logger.error(f"Failed to create model version: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create model version")


@router.put(
    "/models/{model_id}",
    response_model=ModelVersionResponseDTO,
    dependencies=[Depends(require_permission(Permission.MANAGE_SYSTEM))],
)
async def update_model_version(
    model_id: str,
    model_data: ModelVersionUpdateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    repo: SystemRepository = Depends(SystemRepository),
):
    """Update a model version."""
    try:
        model = await repo.update_model_version(
            model_id, model_data.model_dump(exclude_unset=True)
        )
        if not model:
            raise HTTPException(status_code=404, detail="Model version not found")
        logger.info(f"Model version updated by user {user['id']}: {model_id}")
        return model
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update model version {model_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update model version")


@router.delete(
    "/models/{model_id}",
    dependencies=[Depends(require_permission(Permission.MANAGE_SYSTEM))],
)
async def delete_model_version(
    model_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    repo: SystemRepository = Depends(SystemRepository),
):
    """Delete a model version."""
    try:
        success = await repo.delete_model_version(model_id)
        if not success:
            raise HTTPException(status_code=404, detail="Model version not found")
        logger.info(f"Model version deleted by user {user['id']}: {model_id}")
        return {"success": True, "message": "Model version deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete model version {model_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete model version")


@router.post(
    "/models/{model_id}/activate",
    dependencies=[Depends(require_permission(Permission.MANAGE_SYSTEM))],
)
async def activate_model_version(
    model_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    repo: SystemRepository = Depends(SystemRepository),
):
    """Activate a model version."""
    try:
        success = await repo.activate_model_version(model_id, user["id"])
        if not success:
            raise HTTPException(status_code=404, detail="Model version not found")
        logger.info(f"Model version activated by user {user['id']}: {model_id}")
        return {"success": True, "message": "Model version activated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to activate model version {model_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to activate model version")


@router.post(
    "/models/{model_id}/deactivate",
    dependencies=[Depends(require_permission(Permission.MANAGE_SYSTEM))],
)
async def deactivate_model_version(
    model_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    repo: SystemRepository = Depends(SystemRepository),
):
    """Deactivate a model version."""
    try:
        success = await repo.deactivate_model_version(model_id)
        if not success:
            raise HTTPException(status_code=404, detail="Model version not found")
        logger.info(f"Model version deactivated by user {user['id']}: {model_id}")
        return {"success": True, "message": "Model version deactivated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deactivate model version {model_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to deactivate model version"
        )


@router.post(
    "/models/{model_id}/promote-to-production",
    dependencies=[Depends(require_permission(Permission.MANAGE_SYSTEM))],
)
async def promote_model_to_production(
    model_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    repo: SystemRepository = Depends(SystemRepository),
):
    """Promote a model version to production."""
    try:
        success = await repo.promote_model_to_production(model_id, user["id"])
        if not success:
            raise HTTPException(status_code=404, detail="Model version not found")
        logger.info(
            f"Model version promoted to production by user {user['id']}: {model_id}"
        )
        return {
            "success": True,
            "message": "Model version promoted to production successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to promote model version {model_id} to production: {str(e)}"
        )
        raise HTTPException(
            status_code=500, detail="Failed to promote model version to production"
        )


@router.post(
    "/models/{model_id}/deprecate",
    dependencies=[Depends(require_permission(Permission.MANAGE_SYSTEM))],
)
async def deprecate_model_version(
    model_id: str,
    reason: Optional[str] = None,
    user: dict[str, Any] = Depends(get_current_user),
    repo: SystemRepository = Depends(SystemRepository),
):
    """Deprecate a model version."""
    try:
        success = await repo.deprecate_model_version(model_id, user["id"], reason)
        if not success:
            raise HTTPException(status_code=404, detail="Model version not found")
        logger.info(f"Model version deprecated by user {user['id']}: {model_id}")
        return {"success": True, "message": "Model version deprecated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deprecate model version {model_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to deprecate model version")


# â”پâ”پâ”پâ”پ UTILITY ENDPOINTS â”پâ”پâ”پâ”پ


@router.get(
    "/settings/global",
    response_model=List[SystemSettingResponseDTO],
    dependencies=[Depends(require_permission(Permission.VIEW_SYSTEM_SETTINGS))],
)
async def get_global_settings(repo: SystemRepository = Depends(SystemRepository)):
    """Get all global system settings."""
    try:
        settings = await repo.get_global_settings()
        return settings
    except Exception as e:
        logger.error(f"Failed to get global settings: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve global settings"
        )


@router.get(
    "/models/active",
    response_model=List[ModelVersionResponseDTO],
    dependencies=[Depends(require_permission(Permission.VIEW_SYSTEM_SETTINGS))],
)
async def get_active_models(repo: SystemRepository = Depends(SystemRepository)):
    """Get all active model versions."""
    try:
        models = await repo.get_active_models()
        return models
    except Exception as e:
        logger.error(f"Failed to get active models: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve active models")


@router.get(
    "/models/production",
    response_model=List[ModelVersionResponseDTO],
    dependencies=[Depends(require_permission(Permission.VIEW_SYSTEM_SETTINGS))],
)
async def get_production_models(repo: SystemRepository = Depends(SystemRepository)):
    """Get all production model versions."""
    try:
        models = await repo.get_production_models()
        return models
    except Exception as e:
        logger.error(f"Failed to get production models: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve production models"
        )


@router.get(
    "/models/types",
    dependencies=[Depends(require_permission(Permission.VIEW_SYSTEM_SETTINGS))],
)
async def get_model_types(repo: SystemRepository = Depends(SystemRepository)):
    """Get all available model types."""
    try:
        types = await repo.get_model_types()
        return {"success": True, "data": types}
    except Exception as e:
        logger.error(f"Failed to get model types: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve model types")


@router.get(
    "/settings/keys",
    dependencies=[Depends(require_permission(Permission.VIEW_SYSTEM_SETTINGS))],
)
async def get_setting_keys(repo: SystemRepository = Depends(SystemRepository)):
    """Get all available setting keys."""
    try:
        keys = await repo.get_setting_keys()
        return {"success": True, "data": keys}
    except Exception as e:
        logger.error(f"Failed to get setting keys: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve setting keys")


@router.get(
    "/models/{model_name}/versions",
    response_model=List[ModelVersionResponseDTO],
    dependencies=[Depends(require_permission(Permission.VIEW_SYSTEM_SETTINGS))],
)
async def get_model_versions_by_name(
    model_name: str, repo: SystemRepository = Depends(SystemRepository)
):
    """Get all versions of a specific model."""
    try:
        models = await repo.get_model_versions_by_name(model_name)
        return models
    except Exception as e:
        logger.error(f"Failed to get model versions for {model_name}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve model versions")


@router.get(
    "/settings/sensitive",
    response_model=List[SystemSettingResponseDTO],
    dependencies=[Depends(require_permission(Permission.MANAGE_SYSTEM))],
)
async def get_sensitive_settings(repo: SystemRepository = Depends(SystemRepository)):
    """Get all sensitive system settings."""
    try:
        settings = await repo.get_sensitive_settings()
        return settings
    except Exception as e:
        logger.error(f"Failed to get sensitive settings: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve sensitive settings"
        )


# â”پâ”پâ”پâ”پ SCHEMA CACHE MANAGEMENT â”پâ”پâ”پâ”پ


@router.post(
    "/refresh-schema",
    dependencies=[Depends(require_permission(Permission.MANAGE_SYSTEM))],
)
async def refresh_postgrest_schema(
    user: dict[str, Any] = Depends(get_current_user),
    repo: SystemRepository = Depends(SystemRepository),
):
    """
    Refresh PostgREST schema cache.

    This is useful when database schema changes (new columns, tables) are not
    immediately visible via the API due to PostgREST caching.
    """
    try:
        client = await repo._get_client()
        # Execute the NOTIFY command to reload PostgREST schema cache
        await client.rpc(
            "pg_notify", {"channel": "pgrst", "payload": "reload schema"}
        ).execute()

        logger.info(f"PostgREST schema cache refreshed by user {user['id']}")
        return {
            "success": True,
            "message": "Schema cache refresh signal sent successfully. Changes should be visible shortly.",
        }
    except Exception as e:
        logger.warning(
            f"Schema cache refresh unavailable for user {user['id']}: {str(e)}"
        )
        if _is_schema_refresh_unavailable(e):
            raise HTTPException(
                status_code=501,
                detail=_SCHEMA_REFRESH_UNSUPPORTED_DETAIL,
            )
        raise HTTPException(
            status_code=502,
            detail="Failed to refresh schema cache via the backend.",
        )

