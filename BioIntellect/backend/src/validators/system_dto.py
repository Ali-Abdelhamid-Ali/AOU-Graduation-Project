"""System DTOs - Data Transfer Objects for Audit and Notification System."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class AuditAction(str, Enum):
    """Audit log action types."""

    LOGIN = "login"
    LOGOUT = "logout"
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    ACCESS = "access"
    EXPORT = "export"
    IMPORT = "import"
    SYSTEM = "system"
    CREATE_CONVERSATION = "llm.create_conversation"
    CHAT_LLM = "llm.chat"


class ResourceType(str, Enum):
    """Resource types for audit logs."""

    USER = "user"
    PATIENT = "patient"
    CASE = "case"
    FILE = "file"
    REPORT = "report"
    SYSTEM = "system"
    NOTIFICATION = "notification"
    CONVERSATION = "conversation"
    MESSAGE = "message"
    PERMISSION = "permission"


class AccessType(str, Enum):
    """Data access types."""

    VIEW = "view"
    DOWNLOAD = "download"
    EDIT = "edit"
    DELETE = "delete"
    SHARE = "share"


class NotificationType(str, Enum):
    """Notification types."""

    SYSTEM = "system"
    SECURITY = "security"
    AUDIT = "audit"
    DATA_ACCESS = "data_access"
    USER_ACTION = "user_action"
    ADMIN = "admin"
    MEDICAL = "medical"
    CHAT_ACCESS_REQUEST = "chat_access_request"
    CHAT_ACCESS_APPROVED = "chat_access_approved"
    CHAT_ACCESS_REJECTED = "chat_access_rejected"
    NEW_CASE = "new_case"
    CASE_UPDATE = "case_update"
    NEW_RESULT = "new_result"
    SYSTEM_ALERT = "system_alert"


# =====================================================
# AUDIT LOGS
# =====================================================


class AuditLogCreateDTO(BaseModel):
    """DTO for creating audit logs."""

    user_id: Optional[str] = Field(
        None, description="ID of the user performing the action"
    )
    user_role: Optional[str] = Field(
        None, description="Role of the user performing the action"
    )
    action: str = Field(..., description="Type of action performed")
    resource_type: str = Field(..., description="Type of resource affected")
    resource_id: Optional[str] = Field(None, description="ID of the resource affected")
    hospital_id: Optional[str] = Field(None, description="Hospital ID")
    patient_id: Optional[str] = Field(None, description="Patient ID")
    description: str = Field(..., description="Description of the action")
    old_values: Optional[Dict[str, Any]] = Field(
        None, description="Old values before change"
    )
    new_values: Optional[Dict[str, Any]] = Field(
        None, description="New values after change"
    )
    changes: Optional[Dict[str, Any]] = Field(
        None, description="Diff between old and new values"
    )
    ip_address: Optional[str] = Field(None, description="IP address of the user")
    user_agent: Optional[str] = Field(None, description="User agent string")
    request_id: Optional[str] = Field(None, description="Request ID")
    is_sensitive: bool = Field(
        False, description="Whether this involves sensitive data"
    )
    is_flagged: bool = Field(
        False, description="Whether this log has been flagged for review"
    )
    flag_reason: Optional[str] = Field(None, description="Reason for flagging")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class AuditLogResponseDTO(BaseModel):
    """DTO for audit log responses."""

    id: str = Field(..., description="Unique identifier for the audit log")
    user_id: Optional[str] = Field(
        None, description="ID of the user who performed the action"
    )
    user_role: Optional[str] = Field(
        None, description="Role of the user who performed the action"
    )
    action: str = Field(..., description="Type of action performed")
    resource_type: str = Field(..., description="Type of resource affected")
    resource_id: Optional[str] = Field(None, description="ID of the resource affected")
    hospital_id: Optional[str] = Field(None, description="Hospital ID")
    patient_id: Optional[str] = Field(None, description="Patient ID")
    description: str = Field(..., description="Description of the action")
    old_values: Optional[Dict[str, Any]] = Field(
        None, description="Old values before change"
    )
    new_values: Optional[Dict[str, Any]] = Field(
        None, description="New values after change"
    )
    changes: Optional[Dict[str, Any]] = Field(
        None, description="Diff between old and new values"
    )
    ip_address: Optional[str] = Field(None, description="IP address of the user")
    user_agent: Optional[str] = Field(None, description="User agent string")
    request_id: Optional[str] = Field(None, description="Request ID")
    is_sensitive: bool = Field(..., description="Whether this involves sensitive data")
    is_flagged: bool = Field(
        ..., description="Whether this log has been flagged for review"
    )
    flag_reason: Optional[str] = Field(None, description="Reason for flagging")
    created_at: datetime = Field(..., description="When this log was created")


# =====================================================
# DATA ACCESS LOGS (HIPAA Compliance)
# =====================================================


class DataAccessLogCreateDTO(BaseModel):
    """DTO for creating data access logs."""

    user_id: str = Field(..., description="ID of the user accessing the data")
    user_role: str = Field(..., description="Role of the user accessing the data")
    accessed_table: str = Field(..., description="Name of the database table accessed")
    accessed_record_id: str = Field(..., description="ID of the accessed record")
    patient_id: Optional[str] = Field(
        None, description="ID of the patient whose data is being accessed"
    )
    access_type: AccessType = Field(
        ..., description="Type of access (view, download, etc.)"
    )
    access_reason: Optional[str] = Field(None, description="Reason for data access")
    has_treatment_relationship: bool = Field(
        False, description="Whether user has treatment relationship with patient"
    )
    relationship_type: Optional[str] = Field(
        None, description="Type of relationship (primary_doctor, consulting, emergency)"
    )
    hospital_id: Optional[str] = Field(None, description="Hospital ID")
    case_id: Optional[str] = Field(None, description="Case ID")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")
    ip_address: Optional[str] = Field(None, description="IP address of the user")
    user_agent: Optional[str] = Field(None, description="User agent string")


class DataAccessLogResponseDTO(BaseModel):
    """DTO for data access log responses."""

    id: str = Field(..., description="Unique identifier for the data access log")
    user_id: str = Field(..., description="ID of the user who accessed the data")
    user_role: str = Field(..., description="Role of the user who accessed the data")
    accessed_table: str = Field(..., description="Name of the database table accessed")
    accessed_record_id: str = Field(..., description="ID of the accessed record")
    patient_id: Optional[str] = Field(
        None, description="ID of the patient whose data was accessed"
    )
    access_type: AccessType = Field(
        ..., description="Type of access (view, download, etc.)"
    )
    access_reason: Optional[str] = Field(None, description="Reason for data access")
    has_treatment_relationship: bool = Field(
        ..., description="Whether user has treatment relationship with patient"
    )
    relationship_type: Optional[str] = Field(
        None, description="Type of relationship (primary_doctor, consulting, emergency)"
    )
    hospital_id: Optional[str] = Field(None, description="Hospital ID")
    case_id: Optional[str] = Field(None, description="Case ID")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")
    ip_address: Optional[str] = Field(None, description="IP address of the user")
    user_agent: Optional[str] = Field(None, description="User agent string")
    created_at: datetime = Field(..., description="When this log was created")


# =====================================================
# NOTIFICATIONS
# =====================================================


class NotificationCreateDTO(BaseModel):
    """DTO for creating notifications."""

    user_id: str = Field(..., description="ID of the user to notify")
    notification_type: NotificationType = Field(..., description="Type of notification")
    title: str = Field(..., max_length=255, description="Title of the notification")
    message: str = Field(..., description="Content of the notification")
    resource_type: Optional[str] = Field(None, description="Resource type")
    resource_id: Optional[str] = Field(None, description="Resource ID")
    action_url: Optional[str] = Field(None, description="URL for taking action")
    hospital_id: Optional[str] = Field(None, description="Hospital ID")
    patient_id: Optional[str] = Field(None, description="Patient ID")
    priority: str = Field(
        default="normal", description="Priority level (low, normal, high, urgent)"
    )
    expires_at: Optional[datetime] = Field(
        None, description="Notification expiration date"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default={}, description="Additional metadata"
    )


class NotificationUpdateDTO(BaseModel):
    """DTO for updating notifications."""

    notification_type: Optional[NotificationType] = Field(
        None, description="Type of notification"
    )
    title: Optional[str] = Field(
        None, max_length=255, description="Title of the notification"
    )
    message: Optional[str] = Field(None, description="Content of the notification")
    resource_type: Optional[str] = Field(None, description="Resource type")
    resource_id: Optional[str] = Field(None, description="Resource ID")
    action_url: Optional[str] = Field(None, description="URL for taking action")
    hospital_id: Optional[str] = Field(None, description="Hospital ID")
    patient_id: Optional[str] = Field(None, description="Patient ID")
    priority: Optional[str] = Field(None, description="Priority level")
    expires_at: Optional[datetime] = Field(
        None, description="Notification expiration date"
    )
    is_read: Optional[bool] = Field(
        None, description="Whether the notification has been read"
    )
    read_at: Optional[datetime] = Field(
        None, description="When the notification was read"
    )
    is_archived: Optional[bool] = Field(
        None, description="Whether the notification has been archived"
    )
    archived_at: Optional[datetime] = Field(
        None, description="When the notification was archived"
    )
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class NotificationResponseDTO(BaseModel):
    """DTO for notification responses."""

    id: str = Field(..., description="Unique identifier for the notification")
    user_id: str = Field(..., description="ID of the user being notified")
    notification_type: NotificationType = Field(..., description="Type of notification")
    title: str = Field(..., description="Title of the notification")
    message: str = Field(..., description="Content of the notification")
    resource_type: Optional[str] = Field(None, description="Resource type")
    resource_id: Optional[str] = Field(None, description="Resource ID")
    action_url: Optional[str] = Field(None, description="URL for taking action")
    hospital_id: Optional[str] = Field(None, description="Hospital ID")
    patient_id: Optional[str] = Field(None, description="Patient ID")
    is_read: bool = Field(..., description="Whether the notification has been read")
    read_at: Optional[datetime] = Field(
        None, description="When the notification was read"
    )
    is_archived: bool = Field(
        ..., description="Whether the notification has been archived"
    )
    archived_at: Optional[datetime] = Field(
        None, description="When the notification was archived"
    )
    priority: str = Field(..., description="Priority level (low, normal, high, urgent)")
    expires_at: Optional[datetime] = Field(
        None, description="Notification expiration date"
    )
    metadata: Dict[str, Any] = Field(..., description="Additional metadata")
    created_at: datetime = Field(..., description="When this notification was created")
    updated_at: datetime = Field(
        ..., description="When this notification was last updated"
    )


# =====================================================
# SYSTEM SETTINGS
# =====================================================


class SystemSettingCreateDTO(BaseModel):
    """DTO for creating system settings."""

    scope: str = Field(..., description="Scope of the setting (global, hospital, user)")
    scope_id: Optional[str] = Field(None, description="ID for scoped settings")
    setting_key: str = Field(..., description="Key for the setting")
    setting_value: Any = Field(..., description="Value of the setting")
    setting_type: str = Field(
        ..., description="Type of the setting (string, number, boolean, json)"
    )
    description: Optional[str] = Field(None, description="Description of the setting")
    is_sensitive: bool = Field(False, description="Whether this is a sensitive setting")
    created_by: Optional[str] = Field(None, description="Created by user ID")
    updated_by: Optional[str] = Field(None, description="Updated by user ID")


class SystemSettingUpdateDTO(BaseModel):
    """DTO for updating system settings."""

    scope: Optional[str] = Field(None, description="Scope of the setting")
    scope_id: Optional[str] = Field(None, description="ID for scoped settings")
    setting_key: Optional[str] = Field(None, description="Key for the setting")
    setting_value: Optional[Any] = Field(None, description="Value of the setting")
    setting_type: Optional[str] = Field(None, description="Type of the setting")
    description: Optional[str] = Field(None, description="Description of the setting")
    is_sensitive: Optional[bool] = Field(
        None, description="Whether this is a sensitive setting"
    )
    updated_by: Optional[str] = Field(None, description="Updated by user ID")


class SystemSettingResponseDTO(BaseModel):
    """DTO for system setting responses."""

    id: str = Field(..., description="Unique identifier for the setting")
    scope: str = Field(..., description="Scope of the setting")
    scope_id: Optional[str] = Field(None, description="ID for scoped settings")
    setting_key: str = Field(..., description="Key for the setting")
    setting_value: Any = Field(..., description="Value of the setting")
    setting_type: str = Field(..., description="Type of the setting")
    description: Optional[str] = Field(None, description="Description of the setting")
    is_sensitive: bool = Field(..., description="Whether this is a sensitive setting")
    created_by: Optional[str] = Field(None, description="Created by user ID")
    updated_by: Optional[str] = Field(None, description="Updated by user ID")
    created_at: datetime = Field(..., description="When this setting was created")
    updated_at: datetime = Field(..., description="When this setting was last updated")


# =====================================================
# MODEL VERSIONS (AI Model Registry)
# =====================================================


class ModelVersionCreateDTO(BaseModel):
    """DTO for creating model versions."""

    model_name: str = Field(..., max_length=100, description="Name of the model")
    model_version: str = Field(..., max_length=50, description="Version of the model")
    model_type: str = Field(
        ...,
        max_length=50,
        description="Type of the model (ecg_classifier, mri_segmentation, report_generator, llm)",
    )
    description: Optional[str] = Field(None, description="Description of the model")
    provider: Optional[str] = Field(
        None, max_length=100, description="Provider (openai, anthropic, internal)"
    )

    # Performance Metrics
    accuracy: Optional[float] = Field(None, ge=0.0, le=1.0, description="Accuracy")
    precision_score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Precision"
    )
    recall: Optional[float] = Field(None, ge=0.0, le=1.0, description="Recall")
    f1_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="F1 score")
    validation_dataset: Optional[str] = Field(None, description="Validation dataset")

    # Configuration
    default_config: Optional[Dict[str, Any]] = Field(
        default={}, description="Default configuration"
    )

    # Status
    is_active: bool = Field(
        default=False, description="Whether this model version is active"
    )
    is_production: bool = Field(
        default=False, description="Whether this model version is in production"
    )
    deployed_at: Optional[datetime] = Field(None, description="Deployed at")
    deprecated_at: Optional[datetime] = Field(None, description="Deprecated at")

    created_by: Optional[str] = Field(None, description="Created by user ID")


class ModelVersionUpdateDTO(BaseModel):
    """DTO for updating model versions."""

    model_name: Optional[str] = Field(
        None, max_length=100, description="Name of the model"
    )
    model_version: Optional[str] = Field(
        None, max_length=50, description="Version of the model"
    )
    model_type: Optional[str] = Field(
        None, max_length=50, description="Type of the model"
    )
    description: Optional[str] = Field(None, description="Description of the model")
    provider: Optional[str] = Field(None, max_length=100, description="Provider")

    accuracy: Optional[float] = Field(None, ge=0.0, le=1.0, description="Accuracy")
    precision_score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Precision"
    )
    recall: Optional[float] = Field(None, ge=0.0, le=1.0, description="Recall")
    f1_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="F1 score")
    validation_dataset: Optional[str] = Field(None, description="Validation dataset")

    default_config: Optional[Dict[str, Any]] = Field(
        None, description="Default configuration"
    )

    is_active: Optional[bool] = Field(
        None, description="Whether this model version is active"
    )
    is_production: Optional[bool] = Field(
        None, description="Whether this model version is in production"
    )
    deployed_at: Optional[datetime] = Field(None, description="Deployed at")
    deprecated_at: Optional[datetime] = Field(None, description="Deprecated at")

    updated_by: Optional[str] = Field(None, description="Updated by user ID")


class ModelVersionResponseDTO(BaseModel):
    """DTO for model version responses."""

    id: str = Field(..., description="Unique identifier for the model version")
    model_name: str = Field(..., description="Name of the model")
    model_version: str = Field(..., description="Version of the model")
    model_type: str = Field(..., description="Type of the model")
    description: Optional[str] = Field(None, description="Description of the model")
    provider: Optional[str] = Field(None, description="Provider")

    accuracy: Optional[float] = Field(None, description="Accuracy")
    precision_score: Optional[float] = Field(None, description="Precision")
    recall: Optional[float] = Field(None, description="Recall")
    f1_score: Optional[float] = Field(None, description="F1 score")
    validation_dataset: Optional[str] = Field(None, description="Validation dataset")

    default_config: Dict[str, Any] = Field(..., description="Default configuration")

    is_active: bool = Field(..., description="Whether this model version is active")
    is_production: bool = Field(
        ..., description="Whether this model version is in production"
    )
    deployed_at: Optional[datetime] = Field(None, description="Deployed at")
    deprecated_at: Optional[datetime] = Field(None, description="Deprecated at")

    created_by: Optional[str] = Field(None, description="Created by user ID")
    created_at: datetime = Field(..., description="When this model version was created")
    updated_at: datetime = Field(
        ..., description="When this model version was last updated"
    )


# =====================================================
# RESPONSE DTOs
# =====================================================


class ErrorResponseDTO(BaseModel):
    """DTO for error responses."""

    success: bool = Field(False, description="Indicates failure")
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional error details"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When the error occurred"
    )


class SuccessResponseDTO(BaseModel):
    """DTO for success responses."""

    success: bool = Field(True, description="Indicates success")
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional response data")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When the response was generated"
    )


class AuditSummaryDTO(BaseModel):
    """DTO for audit summary responses."""

    user_id: str = Field(..., description="ID of the user")
    total_logs: int = Field(..., description="Total number of audit logs")
    flagged_logs: int = Field(..., description="Number of flagged logs")
    sensitive_logs: int = Field(..., description="Number of sensitive logs")
    last_activity: Optional[datetime] = Field(
        None, description="Last activity timestamp"
    )


class AccessSummaryDTO(BaseModel):
    """DTO for access summary responses."""

    patient_id: str = Field(..., description="ID of the patient")
    total_accesses: int = Field(..., description="Total number of accesses")
    access_types: Dict[str, int] = Field(
        ..., description="Count of different access types"
    )
    has_treatment_relationship: bool = Field(
        ..., description="Whether there's a treatment relationship"
    )
