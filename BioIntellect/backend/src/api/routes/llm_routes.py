"""LLM Routes - Complete AI Chat System API."""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List, Any
from src.services.domain.llm_service import LLMService
from src.repositories.llm_repository import LLMRepository
from src.services.ai.ai_service import AIService
from src.validators.llm_dto import (
    ConversationCreateDTO,
    ConversationUpdateDTO,
    MessageCreateDTO,
    MessageUpdateDTO,
    ChatAccessRequestCreateDTO,
    ChatAccessRequestUpdateDTO,
    ChatAccessPermissionCreateDTO,
    ChatAccessPermissionUpdateDTO,
    LLMContextConfigCreateDTO,
    LLMContextConfigUpdateDTO,
    NotificationCreateDTO,
    NotificationUpdateDTO,
    ConversationResponseDTO,
    MessageResponseDTO,
    ChatAccessRequestResponseDTO,
    ChatAccessPermissionResponseDTO,
    LLMContextConfigResponseDTO,
    NotificationResponseDTO,
)
from src.security.auth_middleware import (
    get_current_user,
    require_permission,
    Permission,
)
from src.observability.logger import get_logger

logger = get_logger("routes.llm")

router = APIRouter(prefix="/llm", tags=["llm"])


def get_llm_service():
    return LLMService(LLMRepository(), AIService())


def _has_permission(user: dict[str, Any], permission: Permission) -> bool:
    perms = user.get("permissions", set()) or set()
    values = {getattr(p, "value", p) for p in perms}
    return permission in perms or permission.value in values


# â”پâ”پâ”پâ”پ CONVERSATIONS â”پâ”پâ”پâ”پ


@router.get(
    "/conversations",
    response_model=List[ConversationResponseDTO],
    dependencies=[Depends(require_permission(Permission.CHAT_LLM))],
)
async def list_conversations(
    patient_id: Optional[str] = Query(None, description="Filter by patient ID"),
    doctor_id: Optional[str] = Query(None, description="Filter by doctor ID"),
    conversation_type: Optional[str] = Query(
        None, description="Filter by conversation type"
    ),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_archived: Optional[bool] = Query(None, description="Filter by archived status"),
    limit: int = Query(50, le=100, description="Number of results to return"),
    offset: int = Query(0, description="Number of results to skip"),
    repo: LLMRepository = Depends(LLMRepository),
):
    """List conversations with optional filtering."""
    try:
        filters: dict[str, Any] = {}
        if patient_id:
            filters["patient_id"] = patient_id
        if doctor_id:
            filters["doctor_id"] = doctor_id
        if conversation_type:
            filters["conversation_type"] = conversation_type
        if is_active is not None:
            filters["is_active"] = is_active
        if is_archived is not None:
            filters["is_archived"] = is_archived

        conversations = await repo.list_conversations(filters, limit, offset)
        return conversations
    except Exception as e:
        logger.error(f"Failed to list conversations: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve conversations")


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationResponseDTO,
    dependencies=[Depends(require_permission(Permission.CHAT_LLM))],
)
async def get_conversation(
    conversation_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    service: LLMService = Depends(get_llm_service),
):
    """Get a specific conversation by ID."""
    try:
        conversation = await service.assert_conversation_access(user, conversation_id)
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation {conversation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve conversation")


@router.post(
    "/conversations",
    response_model=ConversationResponseDTO,
    dependencies=[Depends(require_permission(Permission.CHAT_LLM))],
)
async def create_conversation(
    conversation_data: ConversationCreateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    service: LLMService = Depends(get_llm_service),
):
    """Create a new conversation."""
    try:
        # Validate patient exists and user has access
        if not conversation_data.patient_id:
            raise HTTPException(status_code=400, detail="Patient ID is required")

        conversation = await service.create_conversation(
            user["id"], conversation_data.dict()
        )
        logger.info(f"Conversation created by user {user['id']}: {conversation['id']}")
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create conversation: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create conversation")


@router.put(
    "/conversations/{conversation_id}",
    response_model=ConversationResponseDTO,
    dependencies=[Depends(require_permission(Permission.CHAT_LLM))],
)
async def update_conversation(
    conversation_id: str,
    conversation_data: ConversationUpdateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    service: LLMService = Depends(get_llm_service),
    repo: LLMRepository = Depends(LLMRepository),
):
    """Update a conversation."""
    try:
        await service.assert_conversation_access(user, conversation_id)
        conversation = await repo.update_conversation(
            conversation_id, conversation_data.dict(exclude_unset=True)
        )
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        logger.info(f"Conversation updated by user {user['id']}: {conversation_id}")
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update conversation {conversation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update conversation")


@router.delete(
    "/conversations/{conversation_id}",
    dependencies=[Depends(require_permission(Permission.CHAT_LLM))],
)
async def delete_conversation(
    conversation_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    service: LLMService = Depends(get_llm_service),
    repo: LLMRepository = Depends(LLMRepository),
):
    """Delete a conversation."""
    try:
        await service.assert_conversation_access(user, conversation_id)
        success = await repo.delete_conversation(conversation_id)
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        logger.info(f"Conversation deleted by user {user['id']}: {conversation_id}")
        return {"success": True, "message": "Conversation deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete conversation {conversation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete conversation")


@router.post(
    "/conversations/{conversation_id}/archive",
    dependencies=[Depends(require_permission(Permission.CHAT_LLM))],
)
async def archive_conversation(
    conversation_id: str,
    reason: Optional[str] = None,
    user: dict[str, Any] = Depends(get_current_user),
    service: LLMService = Depends(get_llm_service),
    repo: LLMRepository = Depends(LLMRepository),
):
    """Archive a conversation."""
    try:
        await service.assert_conversation_access(user, conversation_id)
        success = await repo.archive_conversation(conversation_id, user["id"], reason)
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        logger.info(f"Conversation archived by user {user['id']}: {conversation_id}")
        return {"success": True, "message": "Conversation archived successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to archive conversation {conversation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to archive conversation")


# â”پâ”پâ”پâ”پ MESSAGES â”پâ”پâ”پâ”پ


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=List[MessageResponseDTO],
    dependencies=[Depends(require_permission(Permission.CHAT_LLM))],
)
async def list_messages(
    conversation_id: str,
    sender_type: Optional[str] = Query(None, description="Filter by sender type"),
    message_type: Optional[str] = Query(None, description="Filter by message type"),
    is_deleted: Optional[bool] = Query(None, description="Filter by deleted status"),
    limit: int = Query(50, le=100, description="Number of results to return"),
    offset: int = Query(0, description="Number of results to skip"),
    user: dict[str, Any] = Depends(get_current_user),
    service: LLMService = Depends(get_llm_service),
    repo: LLMRepository = Depends(LLMRepository),
):
    """List messages in a conversation with optional filtering."""
    try:
        await service.assert_conversation_access(user, conversation_id)
        filters: dict[str, Any] = {"conversation_id": conversation_id}
        if sender_type:
            filters["sender_type"] = sender_type
        if message_type:
            filters["message_type"] = message_type
        if is_deleted is not None:
            filters["is_deleted"] = is_deleted

        messages = await repo.list_messages(filters, limit, offset)
        return messages
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to list messages for conversation {conversation_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve messages")


@router.get(
    "/messages/{message_id}",
    response_model=MessageResponseDTO,
    dependencies=[Depends(require_permission(Permission.CHAT_LLM))],
)
async def get_message(
    message_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    service: LLMService = Depends(get_llm_service),
):
    """Get a specific message by ID."""
    try:
        message = await service.assert_message_access(user, message_id)
        return message
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get message {message_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve message")


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageResponseDTO,
    dependencies=[Depends(require_permission(Permission.CHAT_LLM))],
)
async def send_message(
    conversation_id: str,
    message_data: MessageCreateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    service: LLMService = Depends(get_llm_service),
):
    """Send a message in a conversation."""
    try:
        await service.assert_conversation_access(user, conversation_id)
        message = await service.send_message(
            user["id"], conversation_id, message_data.message_content
        )
        logger.info(
            f"Message sent by user {user['id']} in conversation {conversation_id}"
        )
        return message
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to send message in conversation {conversation_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Failed to send message")


@router.put(
    "/messages/{message_id}",
    response_model=MessageResponseDTO,
    dependencies=[Depends(require_permission(Permission.CHAT_LLM))],
)
async def update_message(
    message_id: str,
    message_data: MessageUpdateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    service: LLMService = Depends(get_llm_service),
    repo: LLMRepository = Depends(LLMRepository),
):
    """Update a message (edit)."""
    try:
        await service.assert_message_access(user, message_id)
        message = await repo.update_message(
            message_id, message_data.dict(exclude_unset=True)
        )
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        logger.info(f"Message updated by user {user['id']}: {message_id}")
        return message
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update message {message_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update message")


@router.delete(
    "/messages/{message_id}",
    dependencies=[Depends(require_permission(Permission.CHAT_LLM))],
)
async def delete_message(
    message_id: str,
    reason: Optional[str] = None,
    user: dict[str, Any] = Depends(get_current_user),
    service: LLMService = Depends(get_llm_service),
    repo: LLMRepository = Depends(LLMRepository),
):
    """Delete a message."""
    try:
        await service.assert_message_access(user, message_id)
        success = await repo.delete_message(message_id, user["id"], reason)
        if not success:
            raise HTTPException(status_code=404, detail="Message not found")
        logger.info(f"Message deleted by user {user['id']}: {message_id}")
        return {"success": True, "message": "Message deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete message {message_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete message")


# â”پâ”پâ”پâ”پ CHAT ACCESS REQUESTS â”پâ”پâ”پâ”پ


@router.get(
    "/access-requests",
    response_model=List[ChatAccessRequestResponseDTO],
    dependencies=[Depends(require_permission(Permission.CHAT_LLM))],
)
async def list_access_requests(
    patient_id: Optional[str] = Query(None, description="Filter by patient ID"),
    doctor_id: Optional[str] = Query(None, description="Filter by doctor ID"),
    request_status: Optional[str] = Query(None, description="Filter by request status"),
    limit: int = Query(50, le=100, description="Number of results to return"),
    offset: int = Query(0, description="Number of results to skip"),
    repo: LLMRepository = Depends(LLMRepository),
):
    """List chat access requests with optional filtering."""
    try:
        filters: dict[str, Any] = {}
        if patient_id:
            filters["patient_id"] = patient_id
        if doctor_id:
            filters["doctor_id"] = doctor_id
        if request_status:
            filters["request_status"] = request_status

        requests = await repo.list_access_requests(filters, limit, offset)
        return requests
    except Exception as e:
        logger.error(f"Failed to list access requests: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve access requests"
        )


@router.get(
    "/access-requests/{request_id}",
    response_model=ChatAccessRequestResponseDTO,
    dependencies=[Depends(require_permission(Permission.CHAT_LLM))],
)
async def get_access_request(
    request_id: str, repo: LLMRepository = Depends(LLMRepository)
):
    """Get a specific access request by ID."""
    try:
        request = await repo.get_access_request(request_id)
        if not request:
            raise HTTPException(status_code=404, detail="Access request not found")
        return request
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get access request {request_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve access request")


@router.post(
    "/access-requests",
    response_model=ChatAccessRequestResponseDTO,
    dependencies=[Depends(require_permission(Permission.CHAT_LLM))],
)
async def create_access_request(
    request_data: ChatAccessRequestCreateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    repo: LLMRepository = Depends(LLMRepository),
):
    """Create a new chat access request."""
    try:
        # Validate patient exists and user has access
        if not request_data.patient_id:
            raise HTTPException(status_code=400, detail="Patient ID is required")

        request = await repo.create_access_request(request_data.dict())
        logger.info(f"Access request created by user {user['id']}: {request['id']}")
        return request
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create access request: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create access request")


@router.put(
    "/access-requests/{request_id}",
    response_model=ChatAccessRequestResponseDTO,
    dependencies=[Depends(require_permission(Permission.CHAT_LLM))],
)
async def update_access_request(
    request_id: str,
    request_data: ChatAccessRequestUpdateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    repo: LLMRepository = Depends(LLMRepository),
):
    """Update an access request (approve/reject)."""
    try:
        request = await repo.update_access_request(
            request_id, request_data.dict(exclude_unset=True)
        )
        if not request:
            raise HTTPException(status_code=404, detail="Access request not found")
        logger.info(f"Access request updated by user {user['id']}: {request_id}")
        return request
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update access request {request_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update access request")


# â”پâ”پâ”پâ”پ CHAT ACCESS PERMISSIONS â”پâ”پâ”پâ”پ


@router.get(
    "/access-permissions",
    response_model=List[ChatAccessPermissionResponseDTO],
    dependencies=[Depends(require_permission(Permission.CHAT_LLM))],
)
async def list_access_permissions(
    patient_id: Optional[str] = Query(None, description="Filter by patient ID"),
    conversation_id: Optional[str] = Query(
        None, description="Filter by conversation ID"
    ),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(50, le=100, description="Number of results to return"),
    offset: int = Query(0, description="Number of results to skip"),
    repo: LLMRepository = Depends(LLMRepository),
):
    """List chat access permissions with optional filtering."""
    try:
        filters: dict[str, Any] = {}
        if patient_id:
            filters["patient_id"] = patient_id
        if conversation_id:
            filters["conversation_id"] = conversation_id
        if is_active is not None:
            filters["is_active"] = is_active

        permissions = await repo.list_access_permissions(filters, limit, offset)
        return permissions
    except Exception as e:
        logger.error(f"Failed to list access permissions: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve access permissions"
        )


@router.get(
    "/access-permissions/{permission_id}",
    response_model=ChatAccessPermissionResponseDTO,
    dependencies=[Depends(require_permission(Permission.CHAT_LLM))],
)
async def get_access_permission(
    permission_id: str, repo: LLMRepository = Depends(LLMRepository)
):
    """Get a specific access permission by ID."""
    try:
        permission = await repo.get_access_permission(permission_id)
        if not permission:
            raise HTTPException(status_code=404, detail="Access permission not found")
        return permission
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get access permission {permission_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve access permission"
        )


@router.post(
    "/access-permissions",
    response_model=ChatAccessPermissionResponseDTO,
    dependencies=[Depends(require_permission(Permission.CHAT_LLM))],
)
async def create_access_permission(
    permission_data: ChatAccessPermissionCreateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    repo: LLMRepository = Depends(LLMRepository),
):
    """Create a new access permission."""
    try:
        permission = await repo.create_access_permission(permission_data.dict())
        logger.info(
            f"Access permission created by user {user['id']}: {permission['id']}"
        )
        return permission
    except Exception as e:
        logger.error(f"Failed to create access permission: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to create access permission"
        )


@router.put(
    "/access-permissions/{permission_id}",
    response_model=ChatAccessPermissionResponseDTO,
    dependencies=[Depends(require_permission(Permission.CHAT_LLM))],
)
async def update_access_permission(
    permission_id: str,
    permission_data: ChatAccessPermissionUpdateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    repo: LLMRepository = Depends(LLMRepository),
):
    """Update an access permission."""
    try:
        permission = await repo.update_access_permission(
            permission_id, permission_data.dict(exclude_unset=True)
        )
        if not permission:
            raise HTTPException(status_code=404, detail="Access permission not found")
        logger.info(f"Access permission updated by user {user['id']}: {permission_id}")
        return permission
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update access permission {permission_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to update access permission"
        )


@router.delete(
    "/access-permissions/{permission_id}",
    dependencies=[Depends(require_permission(Permission.CHAT_LLM))],
)
async def delete_access_permission(
    permission_id: str,
    reason: Optional[str] = None,
    user: dict[str, Any] = Depends(get_current_user),
    repo: LLMRepository = Depends(LLMRepository),
):
    """Revoke an access permission."""
    try:
        success = await repo.revoke_access_permission(permission_id, user["id"], reason)
        if not success:
            raise HTTPException(status_code=404, detail="Access permission not found")
        logger.info(f"Access permission revoked by user {user['id']}: {permission_id}")
        return {"success": True, "message": "Access permission revoked successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to revoke access permission {permission_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to revoke access permission"
        )


# â”پâ”پâ”پâ”پ LLM CONTEXT CONFIGS â”پâ”پâ”پâ”پ


@router.get(
    "/context-configs",
    response_model=List[LLMContextConfigResponseDTO],
    dependencies=[Depends(require_permission(Permission.MANAGE_SYSTEM))],
)
async def list_context_configs(
    context_type: Optional[str] = Query(None, description="Filter by context type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(50, le=100, description="Number of results to return"),
    offset: int = Query(0, description="Number of results to skip"),
    repo: LLMRepository = Depends(LLMRepository),
):
    """List LLM context configurations with optional filtering."""
    try:
        filters: dict[str, Any] = {}
        if context_type:
            filters["context_type"] = context_type
        if is_active is not None:
            filters["is_active"] = is_active

        configs = await repo.list_context_configs(filters, limit, offset)
        return configs
    except Exception as e:
        logger.error(f"Failed to list context configs: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve context configs"
        )


@router.get(
    "/context-configs/{config_id}",
    response_model=LLMContextConfigResponseDTO,
    dependencies=[Depends(require_permission(Permission.MANAGE_SYSTEM))],
)
async def get_context_config(
    config_id: str, repo: LLMRepository = Depends(LLMRepository)
):
    """Get a specific context config by ID."""
    try:
        config = await repo.get_context_config(config_id)
        if not config:
            raise HTTPException(status_code=404, detail="Context config not found")
        return config
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get context config {config_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve context config")


@router.post(
    "/context-configs",
    response_model=LLMContextConfigResponseDTO,
    dependencies=[Depends(require_permission(Permission.MANAGE_SYSTEM))],
)
async def create_context_config(
    config_data: LLMContextConfigCreateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    repo: LLMRepository = Depends(LLMRepository),
):
    """Create a new context config."""
    try:
        config = await repo.create_context_config(config_data.dict())
        logger.info(f"Context config created by user {user['id']}: {config['id']}")
        return config
    except Exception as e:
        logger.error(f"Failed to create context config: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create context config")


@router.put(
    "/context-configs/{config_id}",
    response_model=LLMContextConfigResponseDTO,
    dependencies=[Depends(require_permission(Permission.MANAGE_SYSTEM))],
)
async def update_context_config(
    config_id: str,
    config_data: LLMContextConfigUpdateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    repo: LLMRepository = Depends(LLMRepository),
):
    """Update a context config."""
    try:
        config = await repo.update_context_config(
            config_id, config_data.dict(exclude_unset=True)
        )
        if not config:
            raise HTTPException(status_code=404, detail="Context config not found")
        logger.info(f"Context config updated by user {user['id']}: {config_id}")
        return config
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update context config {config_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update context config")


@router.delete(
    "/context-configs/{config_id}",
    dependencies=[Depends(require_permission(Permission.MANAGE_SYSTEM))],
)
async def delete_context_config(
    config_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    repo: LLMRepository = Depends(LLMRepository),
):
    """Delete a context config."""
    try:
        success = await repo.delete_context_config(config_id)
        if not success:
            raise HTTPException(status_code=404, detail="Context config not found")
        logger.info(f"Context config deleted by user {user['id']}: {config_id}")
        return {"success": True, "message": "Context config deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete context config {config_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete context config")


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
    user: dict[str, Any] = Depends(get_current_user),
    repo: LLMRepository = Depends(LLMRepository),
):
    """List notifications with optional filtering."""
    try:
        if user_id and user_id != user.get("id") and not _has_permission(
            user, Permission.MANAGE_NOTIFICATIONS
        ):
            raise HTTPException(status_code=403, detail="Access denied")

        filters: dict[str, Any] = {}
        if user_id:
            filters["user_id"] = user_id
        if notification_type:
            filters["notification_type"] = notification_type
        if is_read is not None:
            filters["is_read"] = is_read
        if is_archived is not None:
            filters["is_archived"] = is_archived

        if not user_id and not _has_permission(user, Permission.MANAGE_NOTIFICATIONS):
            filters["user_id"] = user.get("id")

        notifications = await repo.list_notifications(filters, limit, offset)
        return notifications
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list notifications: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve notifications")


@router.get(
    "/notifications/{notification_id}",
    response_model=NotificationResponseDTO,
    dependencies=[Depends(require_permission(Permission.VIEW_NOTIFICATIONS))],
)
async def get_notification(
    notification_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    service: LLMService = Depends(get_llm_service),
):
    """Get a specific notification by ID."""
    try:
        notification = await service.assert_notification_access(user, notification_id)
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
    user: dict[str, Any] = Depends(get_current_user),
    repo: LLMRepository = Depends(LLMRepository),
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
    notification_data: NotificationUpdateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    repo: LLMRepository = Depends(LLMRepository),
):
    """Update a notification."""
    try:
        notification = await repo.update_notification(
            notification_id, notification_data.dict(exclude_unset=True)
        )
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
    service: LLMService = Depends(get_llm_service),
    repo: LLMRepository = Depends(LLMRepository),
):
    """Delete a notification."""
    try:
        await service.assert_notification_access(user, notification_id)
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
    "/conversations/{conversation_id}/history",
    dependencies=[Depends(require_permission(Permission.CHAT_LLM))],
)
async def get_conversation_history(
    conversation_id: str,
    limit: int = Query(50, le=100, description="Number of messages to return"),
    offset: int = Query(0, description="Number of messages to skip"),
    user: dict[str, Any] = Depends(get_current_user),
    service: LLMService = Depends(get_llm_service),
    repo: LLMRepository = Depends(LLMRepository),
):
    """Get conversation history with messages."""
    try:
        await service.assert_conversation_access(user, conversation_id)
        messages = await repo.get_conversation_history(conversation_id, limit, offset)
        return {"success": True, "data": messages}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to get conversation history for {conversation_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve conversation history"
        )


@router.get(
    "/access-permissions/patient/{patient_id}/active",
    dependencies=[Depends(require_permission(Permission.CHAT_LLM))],
)
async def get_active_permissions_for_patient(
    patient_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    service: LLMService = Depends(get_llm_service),
    repo: LLMRepository = Depends(LLMRepository),
):
    """Get all active permissions for a patient."""
    try:
        await service.assert_patient_access(user, patient_id)
        permissions = await repo.get_active_permissions_for_patient(patient_id)
        return {"success": True, "data": permissions}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to get active permissions for patient {patient_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve active permissions"
        )


@router.get(
    "/notifications/unread-count",
    dependencies=[Depends(require_permission(Permission.VIEW_NOTIFICATIONS))],
)
async def get_unread_notification_count(
    user: dict = Depends(get_current_user), repo: LLMRepository = Depends(LLMRepository)
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

