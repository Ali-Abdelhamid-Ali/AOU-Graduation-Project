"""LLM Service - Medical AI Conversation Orchestration."""

from typing import Dict, Any

from fastapi import HTTPException

from src.observability.audit import log_audit, AuditAction
from src.repositories.llm_repository import LLMRepository
from src.security.permission_map import Permission
from src.services.ai.ai_service import AIService


class LLMService:
    def __init__(self, repository: LLMRepository, ai_service: AIService):
        self.repo = repository
        self.ai_service = ai_service

    @staticmethod
    def _has_permission(user: Dict[str, Any], permission: Permission) -> bool:
        permissions = user.get("permissions", set()) or set()
        normalized = {getattr(p, "value", p) for p in permissions}
        return permission in permissions or permission.value in normalized

    @classmethod
    def _is_privileged(cls, user: Dict[str, Any]) -> bool:
        return user.get("role") == "super_admin" or cls._has_permission(
            user, Permission.MANAGE_SYSTEM
        )

    async def assert_conversation_access(
        self, user: Dict[str, Any], conversation_id: str
    ) -> Dict[str, Any]:
        """Enforce object-level access for a conversation."""
        conversation = await self.repo.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        if self._is_privileged(user):
            return conversation

        user_id = user.get("id")
        owns_conversation = conversation.get("created_by") == user_id
        assigned_doctor = conversation.get("doctor_id") == user_id
        same_patient = conversation.get("patient_id") == user_id

        if not (owns_conversation or assigned_doctor or same_patient):
            raise HTTPException(status_code=403, detail="Access denied")
        return conversation

    async def assert_message_access(
        self, user: Dict[str, Any], message_id: str
    ) -> Dict[str, Any]:
        """Enforce object-level access for a message via its conversation."""
        message = await self.repo.get_message(message_id)
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")

        conversation_id = message.get("conversation_id")
        if not conversation_id:
            raise HTTPException(status_code=404, detail="Conversation not found")

        await self.assert_conversation_access(user, conversation_id)
        return message

    async def assert_notification_access(
        self, user: Dict[str, Any], notification_id: str
    ) -> Dict[str, Any]:
        """Enforce object-level access for LLM notifications."""
        notification = await self.repo.get_notification(notification_id)
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")

        if self._has_permission(user, Permission.MANAGE_NOTIFICATIONS):
            return notification

        if notification.get("user_id") != user.get("id"):
            raise HTTPException(status_code=403, detail="Access denied")
        return notification

    async def assert_patient_access(self, user: Dict[str, Any], patient_id: str) -> None:
        """Conservative patient-level access check for LLM objects."""
        if self._is_privileged(user):
            return

        if user.get("role") == "patient" and patient_id != user.get("id"):
            raise HTTPException(status_code=403, detail="Access denied")

    async def create_conversation(self, user_id: str, data: Any) -> Dict[str, Any]:
        """Initiates a new medical AI consultation with proper validation."""
        if hasattr(data, "dict") and callable(getattr(data, "dict")):
            data = data.dict()

        if not data.get("patient_id"):
            raise Exception("Patient ID is required for conversation creation")

        conversation_data = {
            "title": data.get("title", "Medical Consultation"),
            "patient_id": data["patient_id"],
            "doctor_id": data.get("doctor_id", user_id),
            "is_active": True,
        }
        result = await self.repo.create(conversation_data)
        if not result:
            raise ValueError("Failed to create conversation record")

        log_audit(
            AuditAction.CREATE_CONVERSATION,
            user_id=user_id,
            details={
                "conversation_id": result.get("id")
                if isinstance(result, dict)
                else getattr(result, "id", None)
            },
        )
        return result

    async def send_message(
        self, user_id: str, conversation_id: str, content: str
    ) -> Dict[str, Any]:
        """Processes a user message and generates an AI response."""
        conv = await self.repo.get_by_id(conversation_id)
        if not conv:
            raise Exception("Conversation not found")

        context = await self.repo.get_patient_metadata(conv["patient_id"])

        await self.repo.create_message(
            {
                "conversation_id": conversation_id,
                "sender_type": "user",
                "message_content": content,
            }
        )

        ai_response = await self.ai_service.chat_medical_llm(content, context=str(context))

        ai_msg = await self.repo.create_message(
            {
                "conversation_id": conversation_id,
                "sender_type": "llm",
                "message_content": ai_response,
            }
        )

        log_audit(
            AuditAction.CHAT_LLM,
            user_id=user_id,
            details={"conversation_id": conversation_id},
        )
        return ai_msg
