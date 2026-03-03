"""Statistics API Routes - Real-time dashboard statistics endpoints."""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException

from src.services.domain.statistics_service import get_statistics_service
from src.security.auth_middleware import (
    get_current_user,
    require_permission,
    Permission,
)
from src.observability.logger import get_logger

router = APIRouter(prefix="/statistics", tags=["statistics"])
logger = get_logger("routes.statistics")


@router.get(
    "/dashboard", dependencies=[Depends(require_permission(Permission.VIEW_STATISTICS))]
)
async def get_dashboard_statistics(user: dict[str, Any] = Depends(get_current_user)):
    """Get comprehensive dashboard statistics based on user role."""
    try:
        service = await get_statistics_service()
        stats = await service.get_dashboard_statistics(user["id"], user["role"])

        if not stats.get("success"):
            raise HTTPException(
                status_code=500,
                detail=stats.get("message", "Failed to retrieve statistics"),
            )

        return {
            "success": True,
            "data": stats.get("data", {}),
            "last_updated": stats.get("last_updated"),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dashboard statistics: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve dashboard statistics"
        )


@router.get(
    "/real-time", dependencies=[Depends(require_permission(Permission.VIEW_STATISTICS))]
)
async def get_real_time_updates(user: dict[str, Any] = Depends(get_current_user)):
    """Get real-time statistics updates."""
    try:
        service = await get_statistics_service()
        updates = await service.get_real_time_updates(user["id"], user["role"])

        if not updates.get("success"):
            raise HTTPException(
                status_code=500,
                detail=updates.get("message", "Failed to get real-time updates"),
            )

        return {
            "success": True,
            "data": updates.get("data", {}),
            "timestamp": updates.get("timestamp"),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get real-time updates: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get real-time updates")


@router.get(
    "/system-health",
    dependencies=[Depends(require_permission(Permission.VIEW_DASHBOARD))],
)
async def get_system_health():
    """Get system health metrics."""
    try:
        service = await get_statistics_service()
        health = await service._get_basic_statistics()

        if not health.get("success"):
            raise HTTPException(
                status_code=500,
                detail=health.get("message", "Failed to get system health"),
            )

        return {"success": True, "data": health.get("data", {}).get("system", {})}

    except Exception as e:
        logger.error(f"Failed to get system health: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get system health")


@router.get(
    "/user-activity",
    dependencies=[Depends(require_permission(Permission.VIEW_STATISTICS))],
)
async def get_user_activity(user: dict[str, Any] = Depends(get_current_user)):
    """Get recent activity for the current user."""
    try:
        service = await get_statistics_service()
        activity = await service._get_basic_statistics()

        if not activity.get("success"):
            raise HTTPException(
                status_code=500,
                detail=activity.get("message", "Failed to get user activity"),
            )

        return {
            "success": True,
            "data": activity.get("data", {}).get("user", {}).get("recent_activity", []),
        }

    except Exception as e:
        logger.error(f"Failed to get user activity: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get user activity")


@router.get(
    "/admin/hospital",
    dependencies=[Depends(require_permission(Permission.MANAGE_USERS))],
)
async def get_hospital_statistics(user: dict[str, Any] = Depends(get_current_user)):
    """Get hospital-specific statistics for admins."""
    try:
        # Check if user has hospital context
        if "hospital_id" not in user or not user["hospital_id"]:
            raise HTTPException(
                status_code=403, detail="Hospital context required for this operation"
            )

        service = await get_statistics_service()
        stats = await service._get_admin_statistics(user["hospital_id"])

        if not stats.get("success"):
            raise HTTPException(
                status_code=500,
                detail=stats.get("message", "Failed to get hospital statistics"),
            )

        return {"success": True, "data": stats.get("data", {})}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get hospital statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get hospital statistics")


@router.get(
    "/doctor/patients",
    dependencies=[Depends(require_permission(Permission.MANAGE_PATIENTS))],
)
async def get_doctor_patient_statistics(
    user: dict[str, Any] = Depends(get_current_user),
):
    """Get patient statistics for doctors."""
    try:
        service = await get_statistics_service()
        stats = await service._get_doctor_statistics(user["id"])

        if not stats.get("success"):
            raise HTTPException(
                status_code=500,
                detail=stats.get("message", "Failed to get doctor statistics"),
            )

        return {"success": True, "data": stats.get("data", {}).get("patients", {})}

    except Exception as e:
        logger.error(f"Failed to get doctor patient statistics: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to get doctor patient statistics"
        )


@router.get(
    "/doctor/cases",
    dependencies=[Depends(require_permission(Permission.MANAGE_PATIENTS))],
)
async def get_doctor_case_statistics(user: dict[str, Any] = Depends(get_current_user)):
    """Get case statistics for doctors."""
    try:
        service = await get_statistics_service()
        stats = await service._get_doctor_statistics(user["id"])

        if not stats.get("success"):
            raise HTTPException(
                status_code=500,
                detail=stats.get("message", "Failed to get doctor statistics"),
            )

        return {"success": True, "data": stats.get("data", {}).get("cases", {})}

    except Exception as e:
        logger.error(f"Failed to get doctor case statistics: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to get doctor case statistics"
        )


@router.get(
    "/patient/medical",
    dependencies=[Depends(require_permission(Permission.VIEW_PATIENT))],
)
async def get_patient_medical_statistics(
    user: dict[str, Any] = Depends(get_current_user),
):
    """Get medical statistics for patients."""
    try:
        service = await get_statistics_service()
        stats = await service._get_patient_statistics(user["id"])

        if not stats.get("success"):
            raise HTTPException(
                status_code=500,
                detail=stats.get("message", "Failed to get patient statistics"),
            )

        return {"success": True, "data": stats.get("data", {})}

    except Exception as e:
        logger.error(f"Failed to get patient medical statistics: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to get patient medical statistics"
        )

