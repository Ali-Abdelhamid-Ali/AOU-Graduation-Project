"""LLM Chat DTOs for request validation."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


# =====================================================
# LLM CONVERSATIONS
# =====================================================


class ConversationCreateDTO(BaseModel):
    """DTO for creating conversations."""

    conversation_type: str = Field(..., description="Conversation type")
    patient_id: str = Field(..., description="Patient ID")
    doctor_id: Optional[str] = Field(None, description="Doctor ID")
    case_id: Optional[str] = Field(None, description="Case ID")
    hospital_id: str = Field(..., description="Hospital ID")
    title: Optional[str] = Field(None, max_length=255, description="Conversation title")
    system_prompt: Optional[str] = Field(None, description="Custom system prompt")
    llm_model: str = Field(default="gpt-4", description="LLM model")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="Temperature")
    max_tokens: int = Field(default=4096, ge=1, description="Max tokens")


class ConversationUpdateDTO(BaseModel):
    """DTO for updating conversations."""

    conversation_type: Optional[str] = Field(None, description="Conversation type")
    doctor_id: Optional[str] = Field(None, description="Doctor ID")
    case_id: Optional[str] = Field(None, description="Case ID")
    title: Optional[str] = Field(None, max_length=255, description="Conversation title")
    system_prompt: Optional[str] = Field(None, description="Custom system prompt")
    llm_model: Optional[str] = Field(None, description="LLM model")
    temperature: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Temperature"
    )
    max_tokens: Optional[int] = Field(None, ge=1, description="Max tokens")
    is_active: Optional[bool] = Field(
        None, description="Whether conversation is active"
    )
    is_archived: Optional[bool] = Field(
        None, description="Whether conversation is archived"
    )
    archived_at: Optional[datetime] = Field(None, description="Archived at")


class ConversationResponseDTO(BaseModel):
    """DTO for conversation responses."""

    id: str
    conversation_type: str
    patient_id: str
    doctor_id: Optional[str]
    case_id: Optional[str]
    hospital_id: str
    title: Optional[str]
    system_prompt: Optional[str]
    llm_model: str
    temperature: float
    max_tokens: int
    is_active: bool
    is_archived: bool
    archived_at: Optional[datetime]
    message_count: int
    total_tokens_used: int
    last_message_at: Optional[datetime]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


# =====================================================
# LLM MESSAGES
# =====================================================


class MessageCreateDTO(BaseModel):
    """DTO for creating messages."""

    conversation_id: str = Field(..., description="Conversation ID")
    sender_type: str = Field(..., description="Sender type")
    sender_id: Optional[str] = Field(None, description="Sender ID")
    message_content: str = Field(..., min_length=1, description="Message content")
    message_type: str = Field(default="text", description="Message type")
    llm_model_used: Optional[str] = Field(None, description="LLM model used")
    tokens_used: Optional[int] = Field(None, ge=0, description="Tokens used")
    prompt_tokens: Optional[int] = Field(None, ge=0, description="Prompt tokens")
    completion_tokens: Optional[int] = Field(
        None, ge=0, description="Completion tokens"
    )
    llm_context_snapshot: Optional[Dict[str, Any]] = Field(
        None, description="LLM context snapshot"
    )
    attachments: Optional[List[Dict[str, Any]]] = Field(
        default=[], description="Attachments"
    )
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Metadata")


class MessageUpdateDTO(BaseModel):
    """DTO for updating messages."""

    message_content: Optional[str] = Field(
        None, min_length=1, description="Message content"
    )
    message_type: Optional[str] = Field(None, description="Message type")
    llm_model_used: Optional[str] = Field(None, description="LLM model used")
    tokens_used: Optional[int] = Field(None, ge=0, description="Tokens used")
    prompt_tokens: Optional[int] = Field(None, ge=0, description="Prompt tokens")
    completion_tokens: Optional[int] = Field(
        None, ge=0, description="Completion tokens"
    )
    llm_context_snapshot: Optional[Dict[str, Any]] = Field(
        None, description="LLM context snapshot"
    )
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="Attachments")
    is_edited: Optional[bool] = Field(None, description="Whether message is edited")
    edited_at: Optional[datetime] = Field(None, description="Edited at")
    is_deleted: Optional[bool] = Field(None, description="Whether message is deleted")
    deleted_at: Optional[datetime] = Field(None, description="Deleted at")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata")


class MessageResponseDTO(BaseModel):
    """DTO for message responses."""

    id: str
    conversation_id: str
    sender_type: str
    sender_id: Optional[str]
    message_content: str
    message_type: str
    llm_model_used: Optional[str]
    tokens_used: Optional[int]
    prompt_tokens: Optional[int]
    completion_tokens: Optional[int]
    llm_context_snapshot: Optional[Dict[str, Any]]
    attachments: List[Dict[str, Any]]
    is_edited: bool
    edited_at: Optional[datetime]
    is_deleted: bool
    deleted_at: Optional[datetime]
    metadata: Dict[str, Any]
    created_at: datetime


# =====================================================
# CHAT ACCESS REQUESTS
# =====================================================


class ChatAccessRequestCreateDTO(BaseModel):
    """DTO for creating chat access requests."""

    patient_id: str = Field(..., description="Patient ID")
    conversation_id: str = Field(..., description="Conversation ID")
    doctor_id: str = Field(..., description="Doctor ID")
    request_reason: Optional[str] = Field(None, description="Request reason")
    requested_duration_hours: int = Field(
        default=24, ge=1, le=168, description="Requested duration in hours"
    )


class ChatAccessRequestUpdateDTO(BaseModel):
    """DTO for updating chat access requests."""

    request_status: str = Field(..., description="Request status")
    response_notes: Optional[str] = Field(None, description="Response notes")
    granted_duration_hours: Optional[int] = Field(
        None, ge=1, le=168, description="Granted duration in hours"
    )
    expires_at: Optional[datetime] = Field(None, description="Expires at")
    responded_at: Optional[datetime] = Field(None, description="Responded at")


class ChatAccessRequestResponseDTO(BaseModel):
    """DTO for chat access request responses."""

    id: str
    patient_id: str
    conversation_id: str
    doctor_id: str
    request_reason: Optional[str]
    request_status: str
    response_notes: Optional[str]
    requested_duration_hours: int
    granted_duration_hours: Optional[int]
    expires_at: Optional[datetime]
    requested_at: datetime
    responded_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


# =====================================================
# CHAT ACCESS PERMISSIONS
# =====================================================


class ChatAccessPermissionCreateDTO(BaseModel):
    """DTO for creating chat access permissions."""

    patient_id: str = Field(..., description="Patient ID")
    conversation_id: str = Field(..., description="Conversation ID")
    granted_by_doctor_id: str = Field(
        ..., description="Doctor ID who granted permission"
    )
    request_id: Optional[str] = Field(None, description="Request ID")
    access_level: str = Field(default="read_only", description="Access level")
    valid_from: datetime = Field(
        default_factory=datetime.utcnow, description="Valid from"
    )
    valid_until: datetime = Field(..., description="Valid until")
    is_active: bool = Field(default=True, description="Whether permission is active")


class ChatAccessPermissionUpdateDTO(BaseModel):
    """DTO for updating chat access permissions."""

    access_level: Optional[str] = Field(None, description="Access level")
    valid_from: Optional[datetime] = Field(None, description="Valid from")
    valid_until: Optional[datetime] = Field(None, description="Valid until")
    is_active: Optional[bool] = Field(None, description="Whether permission is active")
    revoked_at: Optional[datetime] = Field(None, description="Revoked at")
    revoked_by: Optional[str] = Field(None, description="Revoked by user ID")
    revoke_reason: Optional[str] = Field(None, description="Revoke reason")
    last_accessed_at: Optional[datetime] = Field(None, description="Last accessed at")
    access_count: Optional[int] = Field(None, ge=0, description="Access count")


class ChatAccessPermissionResponseDTO(BaseModel):
    """DTO for chat access permission responses."""

    id: str
    patient_id: str
    conversation_id: str
    granted_by_doctor_id: str
    request_id: Optional[str]
    access_level: str
    valid_from: datetime
    valid_until: datetime
    is_active: bool
    revoked_at: Optional[datetime]
    revoked_by: Optional[str]
    revoke_reason: Optional[str]
    last_accessed_at: Optional[datetime]
    access_count: int
    created_at: datetime


# =====================================================
# LLM CONTEXT CONFIGURATIONS
# =====================================================


class LLMContextConfigCreateDTO(BaseModel):
    """DTO for creating LLM context configs."""

    config_name: str = Field(..., max_length=100, description="Config name")
    context_type: str = Field(..., max_length=50, description="Context type")

    # What data to include
    include_patient_info: bool = Field(default=True, description="Include patient info")
    include_medical_history: bool = Field(
        default=True, description="Include medical history"
    )
    include_allergies: bool = Field(default=True, description="Include allergies")
    include_medications: bool = Field(default=True, description="Include medications")
    include_recent_cases: int = Field(
        default=5, ge=1, description="Number of recent cases to include"
    )
    include_ecg_results: int = Field(
        default=3, ge=0, description="Number of ECG results to include"
    )
    include_mri_results: int = Field(
        default=3, ge=0, description="Number of MRI results to include"
    )
    include_doctor_info: bool = Field(default=True, description="Include doctor info")

    # Data Restrictions
    data_sources: Optional[List[str]] = Field(default=[], description="Data sources")
    excluded_fields: Optional[List[str]] = Field(
        default=[], description="Excluded fields"
    )
    max_history_days: int = Field(default=365, ge=1, description="Max history days")

    # Access Rules
    access_rules: Optional[Dict[str, Any]] = Field(
        default={}, description="Access rules"
    )

    # Template
    system_prompt_template: Optional[str] = Field(
        None, description="System prompt template"
    )

    is_active: bool = Field(default=True, description="Whether config is active")


class LLMContextConfigUpdateDTO(BaseModel):
    """DTO for updating LLM context configs."""

    config_name: Optional[str] = Field(None, max_length=100, description="Config name")
    context_type: Optional[str] = Field(None, max_length=50, description="Context type")

    include_patient_info: Optional[bool] = Field(
        None, description="Include patient info"
    )
    include_medical_history: Optional[bool] = Field(
        None, description="Include medical history"
    )
    include_allergies: Optional[bool] = Field(None, description="Include allergies")
    include_medications: Optional[bool] = Field(None, description="Include medications")
    include_recent_cases: Optional[int] = Field(
        None, ge=1, description="Number of recent cases to include"
    )
    include_ecg_results: Optional[int] = Field(
        None, ge=0, description="Number of ECG results to include"
    )
    include_mri_results: Optional[int] = Field(
        None, ge=0, description="Number of MRI results to include"
    )
    include_doctor_info: Optional[bool] = Field(None, description="Include doctor info")

    data_sources: Optional[List[str]] = Field(None, description="Data sources")
    excluded_fields: Optional[List[str]] = Field(None, description="Excluded fields")
    max_history_days: Optional[int] = Field(None, ge=1, description="Max history days")

    access_rules: Optional[Dict[str, Any]] = Field(None, description="Access rules")

    system_prompt_template: Optional[str] = Field(
        None, description="System prompt template"
    )

    is_active: Optional[bool] = Field(None, description="Whether config is active")


class LLMContextConfigResponseDTO(BaseModel):
    """DTO for LLM context config responses."""

    id: str
    config_name: str
    context_type: str

    include_patient_info: bool
    include_medical_history: bool
    include_allergies: bool
    include_medications: bool
    include_recent_cases: int
    include_ecg_results: int
    include_mri_results: int
    include_doctor_info: bool

    data_sources: List[str]
    excluded_fields: List[str]
    max_history_days: int

    access_rules: Dict[str, Any]

    system_prompt_template: Optional[str]

    is_active: bool
    created_at: datetime
    updated_at: datetime


# =====================================================
# LLM NOTIFICATIONS
# =====================================================


class NotificationCreateDTO(BaseModel):
    """DTO for creating notifications."""

    user_id: str = Field(..., description="User ID to notify")
    notification_type: str = Field(..., description="Notification type")
    title: str = Field(..., max_length=255, description="Notification title")
    content: str = Field(..., description="Notification content")
    priority: str = Field(default="medium", description="Notification priority")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Metadata")


class NotificationUpdateDTO(BaseModel):
    """DTO for updating notifications."""

    is_read: Optional[bool] = Field(None, description="Whether notification is read")
    is_archived: Optional[bool] = Field(
        None, description="Whether notification is archived"
    )
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata")


class NotificationResponseDTO(BaseModel):
    """DTO for notification responses."""

    id: str
    user_id: str
    notification_type: str
    title: str
    content: str
    priority: str
    is_read: bool
    is_archived: bool
    read_at: Optional[datetime]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
