"""
Notification API Routes - Real-time notifications with WebSocket support

Provides REST endpoints for notification management and WebSocket connections.
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

from src.repositories.notifications_repository import NotificationsRepository
from src.security.auth_middleware import (
    get_current_user,
    Permission,
    require_permission,
)
from src.observability.logger import get_logger

logger = get_logger("routes.notifications")

router = APIRouter(prefix="/notifications", tags=["notifications"])


# â”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پ
# REQUEST/RESPONSE MODELS
# â”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پ


class CreateNotificationRequest(BaseModel):
    """Request model for creating a notification."""

    recipient_id: str
    type: str
    title: str
    message: str
    sender_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    action_url: Optional[str] = None
    priority: str = "normal"

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        valid_types = [
            "message",
            "alert",
            "system",
            "reminder",
            "appointment",
            "result",
            "case_assigned",
            "case_updated",
            "report_ready",
        ]
        if v not in valid_types:
            raise ValueError(
                f"Invalid notification type. Must be one of: {valid_types}"
            )
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v):
        valid_priorities = ["low", "normal", "high", "urgent"]
        if v not in valid_priorities:
            raise ValueError(f"Invalid priority. Must be one of: {valid_priorities}")
        return v


class BulkNotificationRequest(BaseModel):
    """Request model for creating bulk notifications."""

    recipient_ids: List[str]
    type: str
    title: str
    message: str
    sender_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    action_url: Optional[str] = None
    priority: str = "normal"


class UpdatePreferencesRequest(BaseModel):
    """Request model for updating notification preferences."""

    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    websocket_notifications: Optional[bool] = None
    sound_enabled: Optional[bool] = None
    desktop_notifications: Optional[bool] = None


# â”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پ
# REST API ENDPOINTS
# â”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پ


@router.get("")
async def get_notifications(
    unread_only: bool = False,
    limit: int = 20,
    offset: int = 0,
    notification_type: Optional[str] = None,
    user: Dict[str, Any] = Depends(get_current_user),
    repo: NotificationsRepository = Depends(NotificationsRepository),
):
    """
    Get notifications for current user.

    Query params:
        - unread_only: Only return unread notifications
        - limit: Maximum number to return (default: 20)
        - offset: Pagination offset (default: 0)
        - notification_type: Filter by type (optional)
    """
    try:
        notifications = await repo.get_user_notifications(
            user_id=user["id"],
            unread_only=unread_only,
            limit=limit,
            offset=offset,
            notification_type=notification_type,
        )

        return {
            "success": True,
            "data": notifications,
            "count": len(notifications),
            "message": "Notifications retrieved successfully",
        }

    except Exception as e:
        logger.error(f"Failed to get notifications for user {user['id']}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve notifications")


@router.get("/unread-count")
async def get_unread_count(
    user: Dict[str, Any] = Depends(get_current_user),
    repo: NotificationsRepository = Depends(NotificationsRepository),
):
    """Get count of unread notifications for current user."""
    try:
        count = await repo.get_unread_count(user["id"])

        return {
            "success": True,
            "data": {"count": count},
            "message": "Unread count retrieved successfully",
        }

    except Exception as e:
        logger.error(f"Failed to get unread count for user {user['id']}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve unread count")


@router.post("/mark-read/{notification_id}")
async def mark_notification_as_read(
    notification_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    repo: NotificationsRepository = Depends(NotificationsRepository),
):
    """Mark a specific notification as read."""
    try:
        # Verify notification belongs to user
        notification = await repo.get_notification_by_id(notification_id)
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")

        if notification["recipient_id"] != user["id"]:
            raise HTTPException(
                status_code=403, detail="Not authorized to modify this notification"
            )

        success = await repo.mark_as_read(notification_id)

        if success:
            # Broadcast to WebSocket that notification was read
            from src.services.websocket_manager import websocket_manager

            await websocket_manager.send_notification_update(
                user["id"],
                {"type": "notification_read", "notification_id": notification_id},
            )

            return {
                "success": True,
                "message": "Notification marked as read",
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to mark as read")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to mark notification as read: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to mark notification as read"
        )


@router.post("/mark-all-read")
async def mark_all_notifications_as_read(
    user: Dict[str, Any] = Depends(get_current_user),
    repo: NotificationsRepository = Depends(NotificationsRepository),
):
    """Mark all notifications as read for current user."""
    try:
        count = await repo.mark_all_as_read(user["id"])

        # Broadcast to WebSocket
        from src.services.websocket_manager import websocket_manager

        await websocket_manager.send_notification_update(
            user["id"], {"type": "all_notifications_read"}
        )

        return {
            "success": True,
            "data": {"count": count},
            "message": f"{count} notifications marked as read",
        }

    except Exception as e:
        logger.error(f"Failed to mark all as read for user {user['id']}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to mark all as read")


@router.post(
    "/create",
    dependencies=[
        Depends(
            require_permission(
                Permission.MANAGE_USERS
            )  # Only admins/doctors can create notifications
        )
    ],
)
async def create_notification(
    request: CreateNotificationRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    repo: NotificationsRepository = Depends(NotificationsRepository),
):
    """
    Create a new notification (admin/doctor only).

    Automatically sends via WebSocket to recipient if connected.
    """
    try:
        # Set sender_id to current user if not provided
        if not request.sender_id:
            request.sender_id = user["id"]

        notification = await repo.create_notification(
            recipient_id=request.recipient_id,
            type=request.type,
            title=request.title,
            message=request.message,
            sender_id=request.sender_id,
            metadata=request.metadata,
            action_url=request.action_url,
            priority=request.priority,
        )

        # Send via WebSocket if recipient is connected
        from src.services.websocket_manager import websocket_manager

        await websocket_manager.send_notification(request.recipient_id, notification)

        return {
            "success": True,
            "data": notification,
            "message": "Notification created and sent successfully",
        }

    except Exception as e:
        logger.error(f"Failed to create notification: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create notification")


@router.post(
    "/create-bulk",
    dependencies=[Depends(require_permission(Permission.MANAGE_USERS))],
)
async def create_bulk_notifications(
    request: BulkNotificationRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    repo: NotificationsRepository = Depends(NotificationsRepository),
):
    """Create notifications for multiple recipients at once."""
    try:
        if not request.sender_id:
            request.sender_id = user["id"]

        notifications = await repo.create_bulk_notifications(
            recipient_ids=request.recipient_ids,
            type=request.type,
            title=request.title,
            message=request.message,
            sender_id=request.sender_id,
            metadata=request.metadata,
            action_url=request.action_url,
            priority=request.priority,
        )

        # Send via WebSocket to all connected recipients
        from src.services.websocket_manager import websocket_manager

        for notification in notifications:
            await websocket_manager.send_notification(
                notification["recipient_id"], notification
            )

        return {
            "success": True,
            "data": {"count": len(notifications), "notifications": notifications},
            "message": f"{len(notifications)} notifications created successfully",
        }

    except Exception as e:
        logger.error(f"Failed to create bulk notifications: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to create bulk notifications"
        )


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    repo: NotificationsRepository = Depends(NotificationsRepository),
):
    """Delete a notification."""
    try:
        # Verify ownership
        notification = await repo.get_notification_by_id(notification_id)
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")

        if notification["recipient_id"] != user["id"]:
            raise HTTPException(
                status_code=403, detail="Not authorized to delete this notification"
            )

        success = await repo.delete_notification(notification_id)

        if success:
            return {
                "success": True,
                "message": "Notification deleted successfully",
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete notification")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete notification: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete notification")


# â”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پ
# PREFERENCES ENDPOINTS
# â”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پ


@router.get("/preferences")
async def get_notification_preferences(
    user: Dict[str, Any] = Depends(get_current_user),
    repo: NotificationsRepository = Depends(NotificationsRepository),
):
    """Get notification preferences for current user."""
    try:
        preferences = await repo.get_user_preferences(user["id"])

        return {
            "success": True,
            "data": preferences,
            "message": "Preferences retrieved successfully",
        }

    except Exception as e:
        logger.error(f"Failed to get preferences for user {user['id']}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve preferences")


@router.put("/preferences")
async def update_notification_preferences(
    request: UpdatePreferencesRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    repo: NotificationsRepository = Depends(NotificationsRepository),
):
    """Update notification preferences for current user."""
    try:
        # Only include non-None values
        updates = {k: v for k, v in request.model_dump().items() if v is not None}

        success = await repo.update_user_preferences(user["id"], updates)

        if success:
            return {
                "success": True,
                "message": "Preferences updated successfully",
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update preferences")

    except Exception as e:
        logger.error(f"Failed to update preferences for user {user['id']}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update preferences")

