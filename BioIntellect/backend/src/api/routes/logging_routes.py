"""Logging Routes - Audit log endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, Dict, Any
from src.services.domain.logging_service import LoggingService
from src.security.auth_middleware import get_current_user
from src.observability.logger import get_logger

logger = get_logger("routes.logging")

router = APIRouter(prefix="/logs", tags=["audit-logs"])


def get_logging_service():
    return LoggingService()


@router.post("/audit")
async def log_action(
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    user: dict[str, Any] = Depends(get_current_user),
    logging_service: LoggingService = Depends(get_logging_service),
):
    """Log a user action for audit purposes."""
    try:
        result = await logging_service.log_user_action(
            user_id=user["id"],
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=None,  # Would come from request headers
            user_agent=None,  # Would come from request headers
        )

        if result["success"]:
            return {
                "success": True,
                "message": "Action logged successfully",
                "log_id": result.get("log_id"),
            }
        else:
            raise HTTPException(
                status_code=500, detail=result.get("message", "Failed to log action")
            )

    except Exception as e:
        logger.error(f"Error logging action: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error logging action: {str(e)}")


@router.get("/audit")
async def get_audit_logs(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    start_date: Optional[str] = Query(None, description="Start date in ISO format"),
    end_date: Optional[str] = Query(None, description="End date in ISO format"),
    limit: int = Query(50, ge=1, le=100, description="Number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    user: dict[str, Any] = Depends(get_current_user),
    logging_service: LoggingService = Depends(get_logging_service),
):
    """Get audit logs with filtering options."""
    try:
        # Only super admins can view all logs, others can only view their own
        if user["role"] != "super_admin" and not user_id:
            user_id = user["id"]
        elif user["role"] != "super_admin" and user_id and user_id != user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        result = await logging_service.get_audit_logs(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )

        if result["success"]:
            return {
                "success": True,
                "data": result["data"],
                "count": result.get("count", 0),
            }
        else:
            raise HTTPException(
                status_code=500, detail=result.get("message", "Failed to retrieve logs")
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving audit logs: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving audit logs: {str(e)}"
        )


@router.get("/activity/user/{user_id}")
async def get_user_activity(
    user_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    logging_service: LoggingService = Depends(get_logging_service),
):
    """Get activity summary for a specific user."""
    try:
        # Only super admins can view other users' activity
        if user["role"] != "super_admin" and user_id != user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        result = await logging_service.get_user_activity_summary(user_id)

        if result["success"]:
            return {"success": True, "data": result["data"]}
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("message", "Failed to retrieve user activity"),
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user activity: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving user activity: {str(e)}"
        )


@router.get("/activity/system")
async def get_system_activity(
    user: dict[str, Any] = Depends(get_current_user),
    logging_service: LoggingService = Depends(get_logging_service),
):
    """Get system-wide activity summary."""
    try:
        # Only super admins can view system activity
        if user["role"] != "super_admin":
            raise HTTPException(status_code=403, detail="Access denied")

        result = await logging_service.get_system_activity_summary()

        if result["success"]:
            return {"success": True, "data": result["data"]}
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("message", "Failed to retrieve system activity"),
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving system activity: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving system activity: {str(e)}"
        )


@router.delete("/cleanup")
async def cleanup_logs(
    days_to_keep: int = Query(
        90, ge=1, le=365, description="Number of days to keep logs"
    ),
    user: dict[str, Any] = Depends(get_current_user),
    logging_service: LoggingService = Depends(get_logging_service),
):
    """Clean up old audit logs."""
    try:
        # Only super admins can clean up logs
        if user["role"] != "super_admin":
            raise HTTPException(status_code=403, detail="Access denied")

        result = await logging_service.cleanup_old_logs(days_to_keep)

        if result["success"]:
            return {
                "success": True,
                "message": result.get("message", "Logs cleaned up successfully"),
                "deleted_count": result.get("deleted_count", 0),
            }
        else:
            raise HTTPException(
                status_code=500, detail=result.get("message", "Failed to clean up logs")
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cleaning up logs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error cleaning up logs: {str(e)}")


# Convenience endpoints for common logging scenarios
@router.post("/audit/login")
async def log_login(
    user: dict[str, Any] = Depends(get_current_user),
    logging_service: LoggingService = Depends(get_logging_service),
):
    """Log user login action."""
    result = await logging_service.log_user_login(
        user_id=user["id"],
        ip_address=None,  # Would come from request headers
        user_agent=None,  # Would come from request headers
    )

    if result["success"]:
        return {"success": True, "message": "Login logged successfully"}
    else:
        raise HTTPException(
            status_code=500, detail=result.get("message", "Failed to log login")
        )


@router.post("/audit/logout")
async def log_logout(
    user: dict[str, Any] = Depends(get_current_user),
    logging_service: LoggingService = Depends(get_logging_service),
):
    """Log user logout action."""
    result = await logging_service.log_user_logout(
        user_id=user["id"],
        ip_address=None,  # Would come from request headers
        user_agent=None,  # Would come from request headers
    )

    if result["success"]:
        return {"success": True, "message": "Logout logged successfully"}
    else:
        raise HTTPException(
            status_code=500, detail=result.get("message", "Failed to log logout")
        )


@router.post("/audit/patient-create")
async def log_patient_creation(
    patient_id: str,
    details: Optional[Dict[str, Any]] = None,
    user: dict[str, Any] = Depends(get_current_user),
    logging_service: LoggingService = Depends(get_logging_service),
):
    """Log patient creation action."""
    result = await logging_service.log_patient_creation(
        user_id=user["id"], patient_id=patient_id, details=details
    )

    if result["success"]:
        return {"success": True, "message": "Patient creation logged successfully"}
    else:
        raise HTTPException(
            status_code=500,
            detail=result.get("message", "Failed to log patient creation"),
        )


@router.post("/audit/doctor-create")
async def log_doctor_creation(
    doctor_id: str,
    details: Optional[Dict[str, Any]] = None,
    user: dict[str, Any] = Depends(get_current_user),
    logging_service: LoggingService = Depends(get_logging_service),
):
    """Log doctor creation action."""
    result = await logging_service.log_doctor_creation(
        user_id=user["id"], doctor_id=doctor_id, details=details
    )

    if result["success"]:
        return {"success": True, "message": "Doctor creation logged successfully"}
    else:
        raise HTTPException(
            status_code=500,
            detail=result.get("message", "Failed to log doctor creation"),
        )


@router.post("/audit/admin-create")
async def log_admin_creation(
    admin_id: str,
    details: Optional[Dict[str, Any]] = None,
    user: dict[str, Any] = Depends(get_current_user),
    logging_service: LoggingService = Depends(get_logging_service),
):
    """Log admin creation action."""
    result = await logging_service.log_admin_creation(
        user_id=user["id"], admin_id=admin_id, details=details
    )

    if result["success"]:
        return {"success": True, "message": "Admin creation logged successfully"}
    else:
        raise HTTPException(
            status_code=500,
            detail=result.get("message", "Failed to log admin creation"),
        )

