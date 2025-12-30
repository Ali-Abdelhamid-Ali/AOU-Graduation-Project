"""Notifications API endpoints."""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import logging

from app.db.supabase_client import supabase_admin
from app.api.v1.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

# ============== SCHEMAS ==============

class NotificationCreateRequest(BaseModel):
    user_id: str
    notification_type: str
    title: str
    message: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    action_url: Optional[str] = None
    priority: Optional[str] = "normal"  # low, normal, high, urgent
    expires_at: Optional[str] = None

class NotificationUpdateRequest(BaseModel):
    is_read: Optional[bool] = None
    is_archived: Optional[bool] = None

# ============== ENDPOINTS ==============

@router.get("")
async def list_notifications(
    is_read: Optional[bool] = None,
    is_archived: bool = False,
    notification_type: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """List notifications for current user."""
    try:
        query = supabase_admin.table("notifications").select(
            "*"
        ).eq("user_id", current_user["id"]).eq("is_archived", is_archived)
        
        if is_read is not None:
            query = query.eq("is_read", is_read)
        if notification_type:
            query = query.eq("notification_type", notification_type)
        if priority:
            query = query.eq("priority", priority)
        
        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
        result = query.execute()
        
        return {"success": True, "data": result.data, "count": len(result.data)}
    except Exception as e:
        logger.error(f"List notifications error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/unread-count")
async def get_unread_count(
    current_user: dict = Depends(get_current_user)
):
    """Get count of unread notifications."""
    try:
        result = supabase_admin.table("notifications").select(
            "id", count="exact"
        ).eq("user_id", current_user["id"]).eq("is_read", False).eq(
            "is_archived", False
        ).execute()
        
        return {"success": True, "count": result.count or 0}
    except Exception as e:
        logger.error(f"Get unread count error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{notification_id}")
async def get_notification(
    notification_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get notification by ID."""
    try:
        result = supabase_admin.table("notifications").select(
            "*"
        ).eq("id", notification_id).eq("user_id", current_user["id"]).single().execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"success": True, "data": result.data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get notification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("")
async def create_notification(
    request: NotificationCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a notification (admin/system use)."""
    try:
        notification_data = request.dict()
        notification_data["is_read"] = False
        notification_data["is_archived"] = False
        
        result = supabase_admin.table("notifications").insert(notification_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create notification")
        
        return {"success": True, "data": result.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create notification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{notification_id}")
async def update_notification(
    notification_id: str,
    request: NotificationUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update notification (mark as read/archive)."""
    try:
        update_data = {k: v for k, v in request.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        if update_data.get("is_read"):
            update_data["read_at"] = datetime.utcnow().isoformat()
        if update_data.get("is_archived"):
            update_data["archived_at"] = datetime.utcnow().isoformat()
        
        result = supabase_admin.table("notifications").update(update_data).eq(
            "id", notification_id
        ).eq("user_id", current_user["id"]).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"success": True, "data": result.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update notification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mark-all-read")
async def mark_all_read(
    current_user: dict = Depends(get_current_user)
):
    """Mark all notifications as read."""
    try:
        result = supabase_admin.table("notifications").update({
            "is_read": True,
            "read_at": datetime.utcnow().isoformat()
        }).eq("user_id", current_user["id"]).eq("is_read", False).execute()
        
        return {"success": True, "message": "All notifications marked as read"}
    except Exception as e:
        logger.error(f"Mark all read error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Archive (soft delete) notification."""
    try:
        result = supabase_admin.table("notifications").update({
            "is_archived": True,
            "archived_at": datetime.utcnow().isoformat()
        }).eq("id", notification_id).eq("user_id", current_user["id"]).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"success": True, "message": "Notification archived"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete notification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
