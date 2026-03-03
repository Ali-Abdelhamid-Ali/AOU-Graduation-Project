"""Audit Routes - Complete Audit and Notification System API."""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List, Any
from src.repositories.audit_repository import AuditRepository
from src.validators.system_dto import (
    AuditLogCreateDTO,
    AuditLogResponseDTO,
    DataAccessLogCreateDTO,
    DataAccessLogResponseDTO,
    NotificationCreateDTO,
    NotificationResponseDTO,
)
from src.security.auth_middleware import (
    get_current_user,
    require_permission,
    Permission,
)
from src.observability.logger import get_logger

logger = get_logger("routes.audit")

router = APIRouter(prefix="/audit", tags=["audit"])

# â”پâ”پâ”پâ”پ AUDIT LOGS â”پâ”پâ”پâ”پ


@router.get(
    "/logs",
    response_model=List[AuditLogResponseDTO],
    dependencies=[Depends(require_permission(Permission.VIEW_AUDIT_LOGS))],
)
async def list_audit_logs(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    is_sensitive: Optional[bool] = Query(
        None, description="Filter by sensitive data access"
    ),
    is_flagged: Optional[bool] = Query(None, description="Filter by flagged logs"),
    limit: int = Query(50, le=100, description="Number of results to return"),
    offset: int = Query(0, description="Number of results to skip"),
    repo: AuditRepository = Depends(AuditRepository),
):
    """List audit logs with optional filtering."""
    try:
        filters: dict[str, Any] = {}
        if user_id:
            filters["user_id"] = user_id
        if action:
            filters["action"] = action
        if resource_type:
            filters["resource_type"] = resource_type
        if is_sensitive is not None:
            filters["is_sensitive"] = is_sensitive
        if is_flagged is not None:
            filters["is_flagged"] = is_flagged

        logs = await repo.list_audit_logs(filters, limit, offset)
        return logs
    except Exception as e:
        logger.error(f"Failed to list audit logs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve audit logs")


@router.get(
    "/logs/{log_id}",
    response_model=AuditLogResponseDTO,
    dependencies=[Depends(require_permission(Permission.VIEW_AUDIT_LOGS))],
)
async def get_audit_log(log_id: str, repo: AuditRepository = Depends(AuditRepository)):
    """Get a specific audit log by ID."""
    try:
        log = await repo.get_audit_log(log_id)
        if not log:
            raise HTTPException(status_code=404, detail="Audit log not found")
        return log
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get audit log {log_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve audit log")


@router.post(
    "/logs",
    response_model=AuditLogResponseDTO,
    dependencies=[Depends(require_permission(Permission.MANAGE_AUDIT_LOGS))],
)
async def create_audit_log(
    log_data: AuditLogCreateDTO,
    user: dict = Depends(get_current_user),
    repo: AuditRepository = Depends(AuditRepository),
):
    """Create a new audit log."""
    try:
        log = await repo.create_audit_log(log_data.dict())
        logger.info(f"Audit log created by user {user['id']}: {log['id']}")
        return log
    except Exception as e:
        logger.error(f"Failed to create audit log: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create audit log")


@router.put(
    "/logs/{log_id}/flag",
    dependencies=[Depends(require_permission(Permission.MANAGE_AUDIT_LOGS))],
)
async def flag_audit_log(
    log_id: str,
    flag_reason: str,
    user: dict = Depends(get_current_user),
    repo: AuditRepository = Depends(AuditRepository),
):
    """Flag an audit log for review."""
    try:
        success = await repo.flag_audit_log(log_id, flag_reason, user["id"])
        if not success:
            raise HTTPException(status_code=404, detail="Audit log not found")
        logger.info(f"Audit log flagged by user {user['id']}: {log_id}")
        return {"success": True, "message": "Audit log flagged successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to flag audit log {log_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to flag audit log")


@router.delete(
    "/logs/{log_id}",
    dependencies=[Depends(require_permission(Permission.MANAGE_AUDIT_LOGS))],
)
async def delete_audit_log(
    log_id: str,
    user: dict = Depends(get_current_user),
    repo: AuditRepository = Depends(AuditRepository),
):
    """Delete an audit log."""
    try:
        success = await repo.delete_audit_log(log_id)
        if not success:
            raise HTTPException(status_code=404, detail="Audit log not found")
        logger.info(f"Audit log deleted by user {user['id']}: {log_id}")
        return {"success": True, "message": "Audit log deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete audit log {log_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete audit log")


# â”پâ”پâ”پâ”پ DATA ACCESS LOGS â”پâ”پâ”پâ”پ


@router.get(
    "/data-access",
    response_model=List[DataAccessLogResponseDTO],
    dependencies=[Depends(require_permission(Permission.VIEW_AUDIT_LOGS))],
)
async def list_data_access_logs(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    accessed_table: Optional[str] = Query(None, description="Filter by accessed table"),
    patient_id: Optional[str] = Query(None, description="Filter by patient ID"),
    access_type: Optional[str] = Query(None, description="Filter by access type"),
    has_treatment_relationship: Optional[bool] = Query(
        None, description="Filter by treatment relationship"
    ),
    limit: int = Query(50, le=100, description="Number of results to return"),
    offset: int = Query(0, description="Number of results to skip"),
    repo: AuditRepository = Depends(AuditRepository),
):
    """List data access logs with optional filtering."""
    try:
        filters: dict[str, Any] = {}
        if user_id:
            filters["user_id"] = user_id
        if accessed_table:
            filters["accessed_table"] = accessed_table
        if patient_id:
            filters["patient_id"] = patient_id
        if access_type:
            filters["access_type"] = access_type
        if has_treatment_relationship is not None:
            filters["has_treatment_relationship"] = has_treatment_relationship

        logs = await repo.list_data_access_logs(filters, limit, offset)
        return logs
    except Exception as e:
        logger.error(f"Failed to list data access logs: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve data access logs"
        )


@router.get(
    "/data-access/{log_id}",
    response_model=DataAccessLogResponseDTO,
    dependencies=[Depends(require_permission(Permission.VIEW_AUDIT_LOGS))],
)
async def get_data_access_log(
    log_id: str, repo: AuditRepository = Depends(AuditRepository)
):
    """Get a specific data access log by ID."""
    try:
        log = await repo.get_data_access_log(log_id)
        if not log:
            raise HTTPException(status_code=404, detail="Data access log not found")
        return log
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get data access log {log_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve data access log"
        )


@router.post(
    "/data-access",
    response_model=DataAccessLogResponseDTO,
    dependencies=[Depends(require_permission(Permission.MANAGE_AUDIT_LOGS))],
)
async def create_data_access_log(
    log_data: DataAccessLogCreateDTO,
    user: dict = Depends(get_current_user),
    repo: AuditRepository = Depends(AuditRepository),
):
    """Create a new data access log."""
    try:
        log = await repo.create_data_access_log(log_data.dict())
        logger.info(f"Data access log created by user {user['id']}: {log['id']}")
        return log
    except Exception as e:
        logger.error(f"Failed to create data access log: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create data access log")


# â”پâ”پâ”پâ”پ NOTIFICATIONS â”پâ”پâ”پâ”پ


@router.get(
    "/notifications",
    response_model=List[NotificationResponseDTO],
    dependencies=[Depends(require_permission(Permission.VIEW_NOTIFICATIONS))],
)
async def list_notifications(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    notification_type: Optional[str] = Query(
        None, description="Filter by notification type"
    ),
    is_read: Optional[bool] = Query(None, description="Filter by read status"),
    is_archived: Optional[bool] = Query(None, description="Filter by archived status"),
    limit: int = Query(50, le=100, description="Number of results to return"),
    offset: int = Query(0, description="Number of results to skip"),
    repo: AuditRepository = Depends(AuditRepository),
):
    """List notifications with optional filtering."""
    try:
        filters: dict[str, Any] = {}
        if user_id:
            filters["user_id"] = user_id
        if notification_type:
            filters["notification_type"] = notification_type
        if is_read is not None:
            filters["is_read"] = is_read
        if is_archived is not None:
            filters["is_archived"] = is_archived

        notifications = await repo.list_notifications(filters, limit, offset)
        return notifications
    except Exception as e:
        logger.error(f"Failed to list notifications: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve notifications")


@router.get(
    "/notifications/{notification_id}",
    response_model=NotificationResponseDTO,
    dependencies=[Depends(require_permission(Permission.VIEW_NOTIFICATIONS))],
)
async def get_notification(
    notification_id: str, repo: AuditRepository = Depends(AuditRepository)
):
    """Get a specific notification by ID."""
    try:
        notification = await repo.get_notification(notification_id)
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        return notification
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get notification {notification_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve notification")


@router.post(
    "/notifications",
    response_model=NotificationResponseDTO,
    dependencies=[Depends(require_permission(Permission.MANAGE_NOTIFICATIONS))],
)
async def create_notification(
    notification_data: NotificationCreateDTO,
    user: dict = Depends(get_current_user),
    repo: AuditRepository = Depends(AuditRepository),
):
    """Create a new notification."""
    try:
        notification = await repo.create_notification(notification_data.dict())
        logger.info(f"Notification created by user {user['id']}: {notification['id']}")
        return notification
    except Exception as e:
        logger.error(f"Failed to create notification: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create notification")


@router.put(
    "/notifications/{notification_id}",
    response_model=NotificationResponseDTO,
    dependencies=[Depends(require_permission(Permission.MANAGE_NOTIFICATIONS))],
)
async def update_notification(
    notification_id: str,
    notification_data: dict,
    user: dict = Depends(get_current_user),
    repo: AuditRepository = Depends(AuditRepository),
):
    """Update a notification."""
    try:
        notification = await repo.update_notification(notification_id, notification_data)
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        logger.info(f"Notification updated by user {user['id']}: {notification_id}")
        return notification
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update notification {notification_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update notification")


@router.delete(
    "/notifications/{notification_id}",
    dependencies=[Depends(require_permission(Permission.MANAGE_NOTIFICATIONS))],
)
async def delete_notification(
    notification_id: str,
    user: dict = Depends(get_current_user),
    repo: AuditRepository = Depends(AuditRepository),
):
    """Delete a notification."""
    try:
        success = await repo.delete_notification(notification_id)
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
        logger.info(f"Notification deleted by user {user['id']}: {notification_id}")
        return {"success": True, "message": "Notification deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete notification {notification_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete notification")


# â”پâ”پâ”پâ”پ UTILITY ENDPOINTS â”پâ”پâ”پâ”پ


@router.get(
    "/logs/user/{user_id}/summary",
    dependencies=[Depends(require_permission(Permission.VIEW_AUDIT_LOGS))],
)
async def get_user_audit_summary(
    user_id: str, repo: AuditRepository = Depends(AuditRepository)
):
    """Get audit summary for a specific user."""
    try:
        summary = await repo.get_user_audit_summary(user_id)
        return {"success": True, "data": summary}
    except Exception as e:
        logger.error(f"Failed to get audit summary for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve audit summary")


@router.get(
    "/logs/patient/{patient_id}/access-summary",
    dependencies=[Depends(require_permission(Permission.VIEW_AUDIT_LOGS))],
)
async def get_patient_access_summary(
    patient_id: str, repo: AuditRepository = Depends(AuditRepository)
):
    """Get access summary for a specific patient."""
    try:
        summary = await repo.get_patient_access_summary(patient_id)
        return {"success": True, "data": summary}
    except Exception as e:
        logger.error(f"Failed to get access summary for patient {patient_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve access summary")


@router.get(
    "/notifications/unread-count",
    dependencies=[Depends(require_permission(Permission.VIEW_NOTIFICATIONS))],
)
async def get_unread_notification_count(
    user: dict = Depends(get_current_user),
    repo: AuditRepository = Depends(AuditRepository),
):
    """Get unread notification count for current user."""
    try:
        count = await repo.get_unread_notification_count(user["id"])
        return {"success": True, "count": count}
    except Exception as e:
        logger.error(
            f"Failed to get unread notification count for user {user['id']}: {str(e)}"
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve unread notification count"
        )


@router.post(
    "/notifications/mark-read",
    dependencies=[Depends(require_permission(Permission.VIEW_NOTIFICATIONS))],
)
async def mark_notifications_as_read(
    notification_ids: List[str],
    user: dict = Depends(get_current_user),
    repo: AuditRepository = Depends(AuditRepository),
):
    """Mark multiple notifications as read."""
    try:
        _ = await repo.mark_notifications_as_read(notification_ids, user["id"])
        logger.info(
            f"Notifications marked as read by user {user['id']}: {len(notification_ids)} notifications"
        )
        return {
            "success": True,
            "message": f"{len(notification_ids)} notifications marked as read",
        }
    except Exception as e:
        logger.error(
            f"Failed to mark notifications as read for user {user['id']}: {str(e)}"
        )
        raise HTTPException(
            status_code=500, detail="Failed to mark notifications as read"
        )


@router.post(
    "/notifications/mark-all-read",
    dependencies=[Depends(require_permission(Permission.VIEW_NOTIFICATIONS))],
)
async def mark_all_notifications_as_read(
    user: dict = Depends(get_current_user),
    repo: AuditRepository = Depends(AuditRepository),
):
    """Mark all notifications as read for current user."""
    try:
        count = await repo.mark_all_notifications_as_read(user["id"])
        logger.info(
            f"All notifications marked as read by user {user['id']}: {count} notifications"
        )
        return {"success": True, "message": f"All {count} notifications marked as read"}
    except Exception as e:
        logger.error(
            f"Failed to mark all notifications as read for user {user['id']}: {str(e)}"
        )
        raise HTTPException(
            status_code=500, detail="Failed to mark all notifications as read"
        )


@router.get(
    "/logs/flagged",
    response_model=List[AuditLogResponseDTO],
    dependencies=[Depends(require_permission(Permission.VIEW_AUDIT_LOGS))],
)
async def get_flagged_logs(
    limit: int = Query(50, le=100, description="Number of results to return"),
    offset: int = Query(0, description="Number of results to skip"),
    repo: AuditRepository = Depends(AuditRepository),
):
    """Get all flagged audit logs."""
    try:
        logs = await repo.get_flagged_logs(limit, offset)
        return logs
    except Exception as e:
        logger.error(f"Failed to get flagged logs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve flagged logs")


@router.get(
    "/logs/sensitive",
    response_model=List[AuditLogResponseDTO],
    dependencies=[Depends(require_permission(Permission.VIEW_AUDIT_LOGS))],
)
async def get_sensitive_logs(
    limit: int = Query(50, le=100, description="Number of results to return"),
    offset: int = Query(0, description="Number of results to skip"),
    repo: AuditRepository = Depends(AuditRepository),
):
    """Get all sensitive data access logs."""
    try:
        logs = await repo.get_sensitive_logs(limit, offset)
        return logs
    except Exception as e:
        logger.error(f"Failed to get sensitive logs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve sensitive logs")

