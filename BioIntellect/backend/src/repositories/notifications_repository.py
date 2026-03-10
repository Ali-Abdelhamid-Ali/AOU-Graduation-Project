"""
Notifications Repository - Manage all notification operations

Handles CRUD operations for the notifications system with WebSocket support.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from src.db.supabase.client import SupabaseProvider
from src.observability.logger import get_logger
from src.repositories.schema_compat import (
    build_notification_payload,
    build_preferences_setting,
    map_notification_type,
    normalize_notification_record,
)

logger = get_logger("repository.notifications")


class NotificationsRepository:
    """Repository for managing notifications."""

    def __init__(self):
        pass

    async def _get_client(self):
        """Get Supabase client."""
        return await SupabaseProvider.get_admin()

    # â”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پ
    # CREATE OPERATIONS
    # â”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پ

    async def create_notification(
        self,
        recipient_id: str,
        type: str,
        title: str,
        message: str,
        sender_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        action_url: Optional[str] = None,
        priority: str = "normal",
        expires_at: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Create a new notification.

        Args:
            recipient_id: User ID who will receive the notification
            type: Notification type (message, alert, system, etc.)
            title: Notification title
            message: Notification message body
            sender_id: Optional user ID who sent the notification
            metadata: Optional additional data (JSON)
            action_url: Optional URL to navigate when clicked
            priority: Priority level (low, normal, high, urgent)
            expires_at: Optional expiration datetime

        Returns:
            Created notification dict
        """
        try:
            client = await self._get_client()
            notification_data = build_notification_payload(
                user_id=recipient_id,
                notification_type=type,
                title=title,
                message=message,
                priority=priority,
                metadata=metadata or {},
                action_url=action_url,
                expires_at=expires_at,
                sender_id=sender_id,
            )

            result = (
                await client.table("notifications").insert(notification_data).execute()
            )

            if result.data:
                logger.info(
                    f"Notification created: {result.data[0]['id']} for user {recipient_id}"
                )
                return normalize_notification_record(result.data[0])
            else:
                logger.error("Failed to create notification - no data returned")
                return {}

        except Exception as e:
            logger.error(f"Failed to create notification: {str(e)}")
            raise

    async def create_bulk_notifications(
        self,
        recipient_ids: List[str],
        type: str,
        title: str,
        message: str,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        Create notifications for multiple recipients at once.

        Args:
            recipient_ids: List of user IDs
            type: Notification type
            title: Notification title
            message: Notification message
            **kwargs: Additional notification parameters

        Returns:
            List of created notifications
        """
        try:
            client = await self._get_client()

            notifications_data = [
                build_notification_payload(
                    user_id=recipient_id,
                    notification_type=type,
                    title=title,
                    message=message,
                    priority=kwargs.get("priority", "normal"),
                    metadata=kwargs.get("metadata", {}),
                    action_url=kwargs.get("action_url"),
                    sender_id=kwargs.get("sender_id"),
                )
                for recipient_id in recipient_ids
            ]

            result = (
                await client.table("notifications").insert(notifications_data).execute()
            )

            logger.info(
                f"Bulk notifications created for {len(recipient_ids)} recipients"
            )
            return [
                normalize_notification_record(record) for record in (result.data or [])
            ]

        except Exception as e:
            logger.error(f"Failed to create bulk notifications: {str(e)}")
            raise

    # â”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پ
    # READ OPERATIONS
    # â”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پ

    async def get_user_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 20,
        offset: int = 0,
        notification_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get notifications for a specific user.

        Args:
            user_id: User ID
            unread_only: If True, only return unread notifications
            limit: Maximum number of notifications to return
            offset: Pagination offset
            notification_type: Optional filter by type

        Returns:
            List of notifications
        """
        try:
            client = await self._get_client()

            query = (
                client.table("notifications")
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .range(offset, offset + limit - 1)
            )

            if unread_only:
                query = query.eq("is_read", False)

            if notification_type:
                query = query.eq(
                    "notification_type", map_notification_type(notification_type)
                )

            result = await query.execute()

            return [
                normalize_notification_record(record) for record in (result.data or [])
            ]

        except Exception as e:
            logger.error(f"Failed to get notifications for user {user_id}: {str(e)}")
            return []

    async def get_unread_count(self, user_id: str) -> int:
        """
        Get count of unread notifications for a user.

        Args:
            user_id: User ID

        Returns:
            Count of unread notifications
        """
        try:
            client = await self._get_client()

            result = (
                await client.table("notifications")
                .select("id", count="exact")
                .eq("user_id", user_id)
                .eq("is_read", False)
                .execute()
            )

            return result.count or 0

        except Exception as e:
            logger.error(f"Failed to get unread count for user {user_id}: {str(e)}")
            return 0

    async def get_notification_by_id(
        self, notification_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a single notification by ID."""
        try:
            client = await self._get_client()

            result = (
                await client.table("notifications")
                .select("*")
                .eq("id", notification_id)
                .single()
                .execute()
            )

            return normalize_notification_record(result.data)

        except Exception as e:
            logger.error(f"Failed to get notification {notification_id}: {str(e)}")
            return None

    # â”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پ
    # UPDATE OPERATIONS
    # â”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پ

    async def mark_as_read(self, notification_id: str) -> bool:
        """
        Mark a notification as read.

        Args:
            notification_id: Notification ID

        Returns:
            True if successful
        """
        try:
            client = await self._get_client()

            result = (
                await client.table("notifications")
                .update({"is_read": True, "read_at": datetime.now().isoformat()})
                .eq("id", notification_id)
                .execute()
            )

            if result.data:
                logger.debug(f"Notification {notification_id} marked as read")
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to mark notification as read: {str(e)}")
            return False

    async def mark_all_as_read(self, user_id: str) -> int:
        """
        Mark all notifications for a user as read.

        Args:
            user_id: User ID

        Returns:
            Number of notifications marked as read
        """
        try:
            client = await self._get_client()

            result = (
                await client.table("notifications")
                .update({"is_read": True, "read_at": datetime.now().isoformat()})
                .eq("user_id", user_id)
                .eq("is_read", False)
                .execute()
            )

            count = len(result.data) if result.data else 0
            logger.info(f"Marked {count} notifications as read for user {user_id}")
            return count

        except Exception as e:
            logger.error(f"Failed to mark all notifications as read: {str(e)}")
            return 0

    # â”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پ
    # DELETE OPERATIONS
    # â”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پ

    async def delete_notification(self, notification_id: str) -> bool:
        """Delete a notification."""
        try:
            client = await self._get_client()

            result = (
                await client.table("notifications")
                .delete()
                .eq("id", notification_id)
                .execute()
            )

            if result.data:
                logger.info(f"Notification {notification_id} deleted")
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to delete notification: {str(e)}")
            return False

    async def delete_old_notifications(self, days: int = 30) -> int:
        """
        Delete old read notifications.

        Args:
            days: Delete notifications older than this many days

        Returns:
            Number of notifications deleted
        """
        try:
            client = await self._get_client()

            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            result = (
                await client.table("notifications")
                .delete()
                .eq("is_read", True)
                .lt("read_at", cutoff_date)
                .execute()
            )

            count = len(result.data) if result.data else 0
            logger.info(f"Deleted {count} old notifications")
            return count

        except Exception as e:
            logger.error(f"Failed to delete old notifications: {str(e)}")
            return 0

    # â”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پ
    # PREFERENCES
    # â”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پâ”پ

    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get notification preferences for a user."""
        try:
            client = await self._get_client()

            result = (
                await client.table("system_settings")
                .select("setting_value")
                .eq("scope", "user")
                .eq("scope_id", user_id)
                .eq("setting_key", "notification_preferences")
                .order("updated_at", desc=True)
                .limit(1)
                .single()
                .execute()
            )

            return (result.data or {}).get("setting_value") or {}

        except Exception as e:
            logger.error(f"Failed to get preferences for user {user_id}: {str(e)}")
            return {}

    async def update_user_preferences(
        self, user_id: str, preferences: Dict[str, Any]
    ) -> bool:
        """Update notification preferences for a user."""
        try:
            client = await self._get_client()
            existing = await (
                client.table("system_settings")
                .select("id, setting_value")
                .eq("scope", "user")
                .eq("scope_id", user_id)
                .eq("setting_key", "notification_preferences")
                .order("updated_at", desc=True)
                .limit(1)
                .execute()
            )
            existing_record = (existing.data or [None])[0]
            merged_preferences = dict(
                (existing_record or {}).get("setting_value") or {}
            )
            merged_preferences.update(preferences)
            payload = build_preferences_setting(
                user_id,
                merged_preferences,
                setting_id=(existing_record or {}).get("id"),
            )

            if existing_record:
                result = await (
                    client.table("system_settings")
                    .update(payload)
                    .eq("id", existing_record["id"])
                    .execute()
                )
            else:
                result = await client.table("system_settings").insert(payload).execute()

            if result.data:
                logger.info(f"Updated notification preferences for user {user_id}")
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to update preferences: {str(e)}")
            return False

