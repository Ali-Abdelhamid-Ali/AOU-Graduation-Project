"""
WebSocket Manager - Real-time notification delivery

Manages WebSocket connections and broadcasts notifications in real-time.
"""

from typing import Dict, Set
from fastapi import WebSocket
import json
import asyncio

from src.observability.logger import get_logger

logger = get_logger("services.websocket_manager")


class WebSocketManager:
    """Manages WebSocket connections for real-time notifications."""

    def __init__(self):
        # user_id -> Set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user_id: str):
        """
        Register a new WebSocket connection for a user.

        Args:
            websocket: WebSocket connection
            user_id: User ID
        """
        await websocket.accept()

        async with self._lock:
            if user_id not in self.active_connections:
                self.active_connections[user_id] = set()

            self.active_connections[user_id].add(websocket)

        logger.info(
            f"WebSocket connected for user {user_id}. "
            f"Active connections: {len(self.active_connections[user_id])}"
        )

        # Send connection success message
        await self._send_to_websocket(
            websocket, {"type": "connection_established", "user_id": user_id}
        )

    async def disconnect(self, websocket: WebSocket, user_id: str):
        """
        Remove a WebSocket connection.

        Args:
            websocket: WebSocket connection
            user_id: User ID
        """
        async with self._lock:
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)

                # Remove user from dict if no more connections
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]

        logger.info(f"WebSocket disconnected for user {user_id}")

    async def send_notification(self, user_id: str, notification: Dict):
        """
        Send a notification to a specific user via WebSocket.

        Args:
            user_id: User ID to send to
            notification: Notification data
        """
        if user_id not in self.active_connections:
            logger.debug(f"User {user_id} not connected via WebSocket")
            return

        message = {"type": "new_notification", "data": notification}

        # Send to all connections for this user (multiple tabs/devices)
        async with self._lock:
            connections = self.active_connections.get(user_id, set()).copy()

        disconnected = []
        for websocket in connections:
            try:
                await self._send_to_websocket(websocket, message)
            except Exception as e:
                logger.warning(
                    f"Failed to send notification to user {user_id}: {str(e)}"
                )
                disconnected.append(websocket)

        # Clean up dead connections
        if disconnected:
            async with self._lock:
                for ws in disconnected:
                    self.active_connections.get(user_id, set()).discard(ws)

    async def send_notification_update(self, user_id: str, update: Dict):
        """
        Send a notification update (e.g., marked as read) to user.

        Args:
            user_id: User ID
            update: Update data
        """
        if user_id not in self.active_connections:
            return

        message = {"type": "notification_update", "data": update}

        async with self._lock:
            connections = self.active_connections.get(user_id, set()).copy()

        for websocket in connections:
            try:
                await self._send_to_websocket(websocket, message)
            except Exception as e:
                logger.warning(f"Failed to send update to user {user_id}: {str(e)}")

    async def broadcast_to_role(self, role: str, notification: Dict):
        """
        Broadcast a notification to all users with a specific role.

        Args:
            role: User role (e.g., 'doctor', 'admin')
            notification: Notification data
        """
        # This would require tracking user roles in the manager
        # For now, notifications should be created individually per user
        logger.warning("broadcast_to_role not yet implemented")

    async def _send_to_websocket(self, websocket: WebSocket, message: Dict):
        """
        Send a message to a specific WebSocket.

        Args:
            websocket: WebSocket connection
            message: Message data
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {str(e)}")
            raise

    async def get_connection_count(self, user_id: str) -> int:
        """Get number of active connections for a user."""
        return len(self.active_connections.get(user_id, set()))

    async def get_total_connections(self) -> int:
        """Get total number of active WebSocket connections."""
        return sum(len(conns) for conns in self.active_connections.values())

    async def get_connected_users(self) -> Set[str]:
        """Get set of user IDs with active connections."""
        return set(self.active_connections.keys())

    async def is_user_connected(self, user_id: str) -> bool:
        """Check if a user has an active WebSocket connection."""
        return user_id in self.active_connections and bool(
            self.active_connections[user_id]
        )


# Global WebSocket manager instance
websocket_manager = WebSocketManager()

