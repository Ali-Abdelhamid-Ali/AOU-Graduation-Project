"""LLM Repository - Data Access for AI Conversations."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.observability.logger import get_logger
from src.repositories.base_repository import BaseRepository
from src.repositories.schema_compat import (
    build_notification_payload,
    normalize_notification_record,
    sanitize_for_table,
)

logger = get_logger(__name__)


class LLMRepository(BaseRepository):
    def __init__(self):
        super().__init__("llm_conversations")

    async def create_message(self, data: dict):
        client = await self._get_client()
        payload = sanitize_for_table("llm_messages", data)
        try:
            result = await client.table("llm_messages").insert(payload).execute()
            if result.data and len(result.data) > 0:
                return result.data[0]
            # Return a minimal record if insert didn't return data (shouldn't happen, but safe fallback)
            logger.warning(f"Insert returned no data for message in conversation {data.get('conversation_id')}")
            return {
                "id": None,
                "conversation_id": data.get("conversation_id"),
                "message_content": data.get("message_content", ""),
                "sender_type": data.get("sender_type"),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to create message: {str(e)}")
            # Return a safe fallback object instead of None
            return {
                "id": None,
                "conversation_id": data.get("conversation_id"),
                "message_content": data.get("message_content", ""),
                "sender_type": data.get("sender_type"),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

    async def get_messages(self, conversation_id: str, limit: int, offset: int):
        client = await self._get_client()
        return await (
            client.table("llm_messages")
            .select(
                "id, conversation_id, sender_type, sender_id, message_content, message_type, llm_model_used, tokens_used, prompt_tokens, completion_tokens, llm_context_snapshot, attachments, is_edited, edited_at, is_deleted, deleted_at, metadata, created_at"
            )
            .eq("conversation_id", conversation_id)
            .order("created_at", desc=False)
            .range(offset, offset + limit - 1)
            .execute()
        )

    async def get_patient_metadata(self, patient_id: str):
        """Unified patient context fetcher for AI prompt engineering."""
        client = await self._get_client()
        import asyncio

        results = await asyncio.gather(
            client.table("patients")
            .select("id, mrn, first_name, last_name, date_of_birth, gender")
            .eq("id", patient_id)
            .limit(1)
            .execute(),
            client.table("medical_cases")
            .select("id, case_number, status, priority, created_at")
            .eq("patient_id", patient_id)
            .order("created_at", desc=True)
            .limit(5)
            .execute(),
            return_exceptions=True,
        )

        patient_data = (
            results[0].data[0]
            if not isinstance(results[0], Exception) and results[0].data
            else {}
        )
        cases_data = (
            results[1].data
            if not isinstance(results[1], Exception) and results[1].data
            else []
        )

        return {
            "profile": patient_data,
            "history": cases_data,
        }

    async def list_conversations(
        self, filters: Dict[str, Any], limit: int, offset: int
    ) -> List[Dict[str, Any]]:
        """List conversations with filtering."""
        client = await self._get_client()
        query = client.table(self.table_name).select("*")

        if filters.get("patient_id"):
            query = query.eq("patient_id", filters["patient_id"])
        if filters.get("doctor_id"):
            query = query.eq("doctor_id", filters["doctor_id"])
        if filters.get("conversation_type"):
            query = query.eq("conversation_type", filters["conversation_type"])
        if filters.get("status"):
            query = query.eq("status", filters["status"])
        if filters.get("is_active") is not None:
            query = query.eq("is_active", filters["is_active"])
        if filters.get("is_archived") is not None:
            query = query.eq("is_archived", filters["is_archived"])
        if filters.get("user_id"):
            query = query.or_(
                f"patient_id.eq.{filters['user_id']},doctor_id.eq.{filters['user_id']}"
            )

        query = query.range(offset, offset + limit - 1)
        query = query.order("created_at", desc=True)

        response = await query.execute()
        return response.data if response.data else []

    async def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific conversation by ID."""
        client = await self._get_client()
        response = await (
            client.table(self.table_name)
            .select("*")
            .eq("id", conversation_id)
            .single()
            .execute()
        )
        return response.data if response.data else None

    async def update_conversation(
        self, conversation_id: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update a conversation."""
        client = await self._get_client()
        payload = sanitize_for_table(self.table_name, data)
        response = await (
            client.table(self.table_name)
            .update(payload)
            .eq("id", conversation_id)
            .execute()
        )
        return response.data[0] if response.data else None

    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation (soft delete)."""
        client = await self._get_client()
        try:
            response = await (
                client.table(self.table_name)
                .update(
                    {
                        "is_archived": True,
                        "is_active": False,
                        "archived_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
                .eq("id", conversation_id)
                .execute()
            )
            return bool(response.data)
        except Exception as e:
            logger.error(f"Failed to delete conversation {conversation_id}: {e}")
            return False

    async def archive_conversation(
        self, conversation_id: str, user_id: str, reason: Optional[str] = None
    ) -> bool:
        """Archive a conversation with reason."""
        client = await self._get_client()
        try:
            conversation = await self.get_conversation(conversation_id)
            metadata = dict((conversation or {}).get("metadata") or {})
            metadata["archived_by"] = user_id
            if reason:
                metadata["archive_reason"] = reason
            response = await (
                client.table(self.table_name)
                .update(
                    {
                        "is_archived": True,
                        "is_active": False,
                        "archived_at": datetime.now(timezone.utc).isoformat(),
                        "metadata": metadata,
                    }
                )
                .eq("id", conversation_id)
                .execute()
            )
            return bool(response.data)
        except Exception as e:
            logger.error(f"Failed to archive conversation {conversation_id}: {e}")
            return False

    async def list_messages(
        self, conversation_or_filters: str | Dict[str, Any], limit: int, offset: int
    ) -> List[Dict[str, Any]]:
        """List messages with backward-compatible filters."""
        client = await self._get_client()
        query = client.table("llm_messages").select("*")

        if isinstance(conversation_or_filters, dict):
            filters = conversation_or_filters
            conversation_id = filters.get("conversation_id")
            if conversation_id:
                query = query.eq("conversation_id", conversation_id)
            if filters.get("sender_type"):
                query = query.eq("sender_type", filters["sender_type"])
            if filters.get("message_type"):
                query = query.eq("message_type", filters["message_type"])
            if filters.get("is_deleted") is not None:
                query = query.eq("is_deleted", filters["is_deleted"])
        else:
            query = query.eq("conversation_id", conversation_or_filters)

        response = await (
            query.order("created_at", desc=False)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return response.data if response.data else []

    async def get_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific message by ID."""
        client = await self._get_client()
        response = await (
            client.table("llm_messages")
            .select("*")
            .eq("id", message_id)
            .single()
            .execute()
        )
        return response.data if response.data else None

    async def update_message(
        self, message_id: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update a message."""
        client = await self._get_client()
        payload = sanitize_for_table("llm_messages", data)
        response = await (
            client.table("llm_messages").update(payload).eq("id", message_id).execute()
        )
        return response.data[0] if response.data else None

    async def delete_message(
        self,
        message_id: str,
        user_id: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> bool:
        """Delete a message."""
        client = await self._get_client()
        try:
            response = await (
                client.table("llm_messages")
                .update(
                    {
                        "is_deleted": True,
                        "deleted_at": datetime.now(timezone.utc).isoformat(),
                        "metadata": {"deleted_by": user_id, "delete_reason": reason},
                    }
                )
                .eq("id", message_id)
                .execute()
            )
            return bool(response.data)
        except Exception as e:
            logger.error(f"Failed to delete message {message_id}: {e}")
            return False

    async def list_access_requests(
        self, filters: Dict[str, Any], limit: int, offset: int
    ) -> List[Dict[str, Any]]:
        """List chat access requests."""
        client = await self._get_client()
        query = client.table("chat_access_requests").select("*")

        if filters.get("conversation_id"):
            query = query.eq("conversation_id", filters["conversation_id"])
        if filters.get("patient_id"):
            query = query.eq("patient_id", filters["patient_id"])
        if filters.get("doctor_id"):
            query = query.eq("doctor_id", filters["doctor_id"])
        if filters.get("request_status"):
            query = query.eq("request_status", filters["request_status"])

        query = query.range(offset, offset + limit - 1)
        query = query.order("created_at", desc=True)

        response = await query.execute()
        return response.data if response.data else []

    async def get_conversation_history(
        self, conversation_id: str, limit: int, offset: int
    ) -> List[Dict[str, Any]]:
        """Get message history for a conversation."""
        client = await self._get_client()
        response = await (
            client.table("llm_messages")
            .select("*")
            .eq("conversation_id", conversation_id)
            .order("created_at", desc=False)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return response.data if response.data else []

    async def get_user_conversation_history(
        self, user_id: str, limit: int, offset: int
    ) -> List[Dict[str, Any]]:
        """Get conversation list history for a user (legacy helper)."""
        client = await self._get_client()
        response = await (
            client.table(self.table_name)
            .select("*")
            .or_(f"patient_id.eq.{user_id},doctor_id.eq.{user_id}")
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return response.data if response.data else []

    async def approve_access_request(self, request_id: str, user_id: str) -> bool:
        """Approve a chat access request."""
        client = await self._get_client()
        try:
            response = await (
                client.table("chat_access_requests")
                .update(
                    {
                        "request_status": "approved",
                        "responded_at": datetime.now(timezone.utc).isoformat(),
                        "response_notes": f"Approved by {user_id}",
                    }
                )
                .eq("id", request_id)
                .execute()
            )
            return bool(response.data)
        except Exception as e:
            logger.error(f"Failed to approve access request {request_id}: {e}")
            return False

    async def delete_context_config(self, config_id: str) -> bool:
        """Delete a context config."""
        client = await self._get_client()
        try:
            response = await (
                client.table("llm_context_configs")
                .delete()
                .eq("id", config_id)
                .execute()
            )
            return bool(response.data)
        except Exception as e:
            logger.error(f"Failed to delete context config {config_id}: {e}")
            return False

    async def delete_notification(self, notification_id: str) -> bool:
        """Delete a notification."""
        client = await self._get_client()
        try:
            response = await (
                client.table("notifications")
                .delete()
                .eq("id", notification_id)
                .execute()
            )
            return bool(response.data)
        except Exception as e:
            logger.error(f"Failed to delete notification {notification_id}: {e}")
            return False

    async def get_access_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific access request by ID."""
        client = await self._get_client()
        response = await (
            client.table("chat_access_requests")
            .select("*")
            .eq("id", request_id)
            .single()
            .execute()
        )
        return response.data if response.data else None

    async def create_access_request(
        self, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Create a new access request."""
        client = await self._get_client()
        payload = sanitize_for_table("chat_access_requests", data)
        response = await client.table("chat_access_requests").insert(payload).execute()
        return response.data[0] if response.data else None

    async def update_access_request(
        self, request_id: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update an access request."""
        client = await self._get_client()
        payload = sanitize_for_table("chat_access_requests", data)
        response = await (
            client.table("chat_access_requests")
            .update(payload)
            .eq("id", request_id)
            .execute()
        )
        return response.data[0] if response.data else None

    async def list_access_permissions(
        self, filters: Dict[str, Any], limit: int, offset: int
    ) -> List[Dict[str, Any]]:
        """List access permissions."""
        client = await self._get_client()
        query = client.table("chat_access_permissions").select("*")

        if filters.get("patient_id"):
            query = query.eq("patient_id", filters["patient_id"])
        if filters.get("conversation_id"):
            query = query.eq("conversation_id", filters["conversation_id"])
        if filters.get("is_active") is not None:
            query = query.eq("is_active", filters["is_active"])

        query = query.range(offset, offset + limit - 1)
        query = query.order("created_at", desc=True)

        response = await query.execute()
        return response.data if response.data else []

    async def get_access_permission(
        self, permission_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a specific access permission by ID."""
        client = await self._get_client()
        response = await (
            client.table("chat_access_permissions")
            .select("*")
            .eq("id", permission_id)
            .single()
            .execute()
        )
        return response.data if response.data else None

    async def create_access_permission(
        self, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Create a new access permission."""
        client = await self._get_client()
        payload = sanitize_for_table("chat_access_permissions", data)
        response = await client.table("chat_access_permissions").insert(payload).execute()
        return response.data[0] if response.data else None

    async def update_access_permission(
        self, permission_id: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update an access permission."""
        client = await self._get_client()
        payload = sanitize_for_table("chat_access_permissions", data)
        response = await (
            client.table("chat_access_permissions")
            .update(payload)
            .eq("id", permission_id)
            .execute()
        )
        return response.data[0] if response.data else None

    async def revoke_access_permission(
        self, permission_id: str, user_id: str, reason: Optional[str] = None
    ) -> bool:
        """Revoke an access permission."""
        client = await self._get_client()
        try:
            response = await (
                client.table("chat_access_permissions")
                .update(
                    {
                        "is_active": False,
                        "revoked_at": datetime.now(timezone.utc).isoformat(),
                        "revoked_by": user_id,
                        "revoke_reason": reason,
                    }
                )
                .eq("id", permission_id)
                .execute()
            )
            return bool(response.data)
        except Exception as e:
            logger.error(f"Failed to revoke permission {permission_id}: {e}")
            return False

    async def list_context_configs(
        self, filters: Dict[str, Any], limit: int, offset: int
    ) -> List[Dict[str, Any]]:
        """List context configurations."""
        client = await self._get_client()
        query = client.table("llm_context_configs").select("*")

        if filters.get("context_type"):
            query = query.eq("context_type", filters["context_type"])
        if filters.get("is_active") is not None:
            query = query.eq("is_active", filters["is_active"])

        query = query.range(offset, offset + limit - 1)
        query = query.order("created_at", desc=True)

        response = await query.execute()
        return response.data if response.data else []

    async def get_context_config(self, config_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific context config by ID."""
        client = await self._get_client()
        response = await (
            client.table("llm_context_configs")
            .select("*")
            .eq("id", config_id)
            .single()
            .execute()
        )
        return response.data if response.data else None

    async def create_context_config(
        self, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Create a new context config."""
        client = await self._get_client()
        payload = sanitize_for_table("llm_context_configs", data)
        response = await client.table("llm_context_configs").insert(payload).execute()
        return response.data[0] if response.data else None

    async def update_context_config(
        self, config_id: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update a context config."""
        client = await self._get_client()
        payload = sanitize_for_table("llm_context_configs", data)
        response = await (
            client.table("llm_context_configs")
            .update(payload)
            .eq("id", config_id)
            .execute()
        )
        return response.data[0] if response.data else None

    async def list_notifications(
        self, filters: Dict[str, Any], limit: int, offset: int
    ) -> List[Dict[str, Any]]:
        """List notifications."""
        client = await self._get_client()
        query = client.table("notifications").select("*")

        if filters.get("user_id"):
            query = query.eq("user_id", filters["user_id"])
        if filters.get("notification_type"):
            query = query.eq("notification_type", filters["notification_type"])
        if filters.get("is_read") is not None:
            query = query.eq("is_read", filters["is_read"])
        if filters.get("is_archived") is not None:
            query = query.eq("is_archived", filters["is_archived"])

        query = query.range(offset, offset + limit - 1)
        query = query.order("created_at", desc=True)

        response = await query.execute()
        return [
            normalize_notification_record(record) for record in (response.data or [])
        ]

    async def get_notification(self, notification_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific notification by ID."""
        client = await self._get_client()
        response = await (
            client.table("notifications")
            .select("*")
            .eq("id", notification_id)
            .single()
            .execute()
        )
        return normalize_notification_record(response.data)

    async def create_notification(
        self, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Create a new notification."""
        client = await self._get_client()
        payload = build_notification_payload(
            user_id=str(data.get("user_id")),
            notification_type=str(data.get("notification_type") or "system_alert"),
            title=str(data.get("title") or "Notification"),
            message=str(data.get("content") or data.get("message") or ""),
            priority=str(data.get("priority") or "normal"),
            metadata=data.get("metadata") or {},
            action_url=data.get("action_url"),
            resource_type=str(data.get("resource_type") or "llm_conversation"),
            resource_id=data.get("resource_id"),
            hospital_id=data.get("hospital_id"),
            patient_id=data.get("patient_id"),
        )
        response = await client.table("notifications").insert(payload).execute()
        return normalize_notification_record((response.data or [None])[0])

    async def update_notification(
        self, notification_id: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update a notification."""
        client = await self._get_client()
        payload = dict(data)
        if "content" in payload and "message" not in payload:
            payload["message"] = payload.pop("content")
        payload = sanitize_for_table("notifications", payload)
        response = await (
            client.table("notifications")
            .update(payload)
            .eq("id", notification_id)
            .execute()
        )
        return normalize_notification_record((response.data or [None])[0])

    async def get_active_permissions_for_patient(
        self, patient_id: str
    ) -> List[Dict[str, Any]]:
        """Get all active permissions for a patient."""
        client = await self._get_client()
        response = await (
            client.table("chat_access_permissions")
            .select("*")
            .eq("patient_id", patient_id)
            .eq("is_active", True)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data if response.data else []

    async def count_active_conversations(self, doctor_id: str) -> int:
        """Count active (non-archived) conversations for a doctor."""
        client = await self._get_client()
        response = await (
            client.table(self.table_name)
            .select("id", count="exact")
            .eq("doctor_id", doctor_id)
            .eq("is_archived", False)
            .execute()
        )
        return response.count if response.count is not None else 0

    async def get_unread_notification_count(self, user_id: str) -> int:
        """Get count of unread notifications for a user."""
        client = await self._get_client()
        response = await (
            client.table("notifications")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .eq("is_read", False)
            .execute()
        )
        return response.count if response.count is not None else 0

