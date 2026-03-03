"""
WebSocket Routes - Real-time notification connections

Provides WebSocket endpoint for real-time notification delivery.
"""

from collections import defaultdict, deque
import time
from typing import Any, Dict, Optional
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from src.services.websocket_manager import websocket_manager
from src.observability.logger import get_logger
from src.security.auth_middleware import get_current_user_ws

logger = get_logger("routes.websocket")

router = APIRouter(tags=["websocket"])

_WS_CONNECT_WINDOW_SECONDS = 60
_WS_CONNECT_MAX_ATTEMPTS = 20
_ws_attempts: dict[str, deque[float]] = defaultdict(deque)


def _ws_throttle_key(websocket: WebSocket, token: str | None) -> str:
    client_ip = websocket.client.host if websocket.client else "unknown"
    return f"{client_ip}:{(token or '')[:16]}"


def _ws_rate_limited(key: str) -> bool:
    now = time.time()
    queue = _ws_attempts[key]
    while queue and now - queue[0] > _WS_CONNECT_WINDOW_SECONDS:
        queue.popleft()
    queue.append(now)
    return len(queue) > _WS_CONNECT_MAX_ATTEMPTS


@router.websocket("/ws/notifications")
async def websocket_notifications_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(
        None, description="JWT token (deprecated: use Authorization header)"
    ),
):
    """
    WebSocket endpoint for real-time notifications.

    Usage:
        ws://localhost:8000/v1/ws/notifications?token=YOUR_JWT_TOKEN

    Messages sent to client:
        - connection_established: {"type": "connection_established", "user_id": "..."}
        - new_notification: {"type": "new_notification", "data": {...}}
        - notification_update: {"type": "notification_update", "data": {"type": "notification_read", "notification_id": "..."}}
        - all_notifications_read: {"type": "notification_update", "data": {"type": "all_notifications_read"}}
        - ping: {"type": "ping"} (heartbeat)
        - pong: {"type": "pong"} (response to client ping)
    """
    user = None
    try:
        auth_header = websocket.headers.get("authorization", "")
        header_token = None
        if auth_header.lower().startswith("bearer "):
            header_token = auth_header.split(" ", 1)[1].strip()

        selected_token = header_token or token
        if not selected_token:
            await websocket.close(code=1008, reason="Missing authentication token")
            return

        if _ws_rate_limited(_ws_throttle_key(websocket, selected_token)):
            await websocket.close(code=1008, reason="Too many connection attempts")
            return

        # Verify token and get user
        user = await get_current_user_ws(selected_token)
        if not user:
            await websocket.close(code=1008, reason="Unauthorized")
            return

        user_id = user["id"]

        # Register connection
        await websocket_manager.connect(websocket, user_id)

        logger.info(f"WebSocket connection established for user {user_id}")

        # Keep connection alive and listen for client messages
        while True:
            try:
                # Receive messages from client (for ping/pong, etc.)
                data = await websocket.receive_json()

                # Handle client messages
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})

                elif data.get("type") == "get_unread_count":
                    # Client requesting unread count
                    from src.repositories.notifications_repository import (
                        NotificationsRepository,
                    )

                    repo = NotificationsRepository()
                    count = await repo.get_unread_count(user_id)
                    await websocket.send_json(
                        {"type": "unread_count", "data": {"count": count}}
                    )

            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for user {user_id}")
                break

            except Exception as e:
                logger.error(f"Error in WebSocket message loop: {str(e)}")
                # Don't break on message errors, just continue
                continue

    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass

    finally:
        # Always clean up connection
        if user:
            await websocket_manager.disconnect(websocket, user["id"])

