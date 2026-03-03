"""Audit Trail - Immutable Logging of Sensitive Operations."""

from enum import Enum
from typing import Any, Dict, Optional
from src.observability.logger import get_logger, get_correlation_id


class AuditAction(str, Enum):
    LOGIN = "auth.login"
    SIGNUP = "auth.signup"
    PASSWORD_CHANGE = "auth.password_change"
    PASSWORD_RESET_REQUEST = "auth.password_reset_request"
    LOGOUT = "auth.logout"
    ROLE_CHANGE = "admin.role_change"
    ACCESS_MEDICAL_DATA = "clinical.access_data"
    ANALYZE_IMAGE = "clinical.analyze_image"
    DELETE_MEDICAL_DATA = "clinical.delete_data"
    REPORT_SIGN = "clinical.report_sign"
    CHAT_LLM = "llm.chat"
    CREATE_CONVERSATION = "llm.create_conversation"
    ACCESS_RESOURCE = "system.access_resource"
    CREATE_RESOURCE = "system.create_resource"
    UPDATE_RESOURCE = "system.update_resource"
    DELETE_RESOURCE = "system.delete_resource"
    VIEW_HISTORY = "clinical.view_history"


audit_logger = get_logger("audit.trail")


def log_audit(
    action: AuditAction,
    user_id: Optional[str] = None,
    email: Optional[str] = None,
    success: bool = True,
    details: Optional[Dict[str, Any]] = None,
):
    """
    Logs a sensitive action to the audit trail.
    STRICT RULE: Audit logs must be append-only and contain the correlation_id.
    """
    log_data: Dict[str, Any] = {
        "action": action.value,
        "user_id": user_id,
        "email": email,
        "success": success,
        "correlation_id": get_correlation_id(),
        "audit": True,  # Flag for easier filtering in log aggregators
    }

    if details:
        log_data["details"] = details

    if success:
        audit_logger.info(f"Audit: {action.value} - SUCCESS", extra=log_data)
    else:
        audit_logger.warning(f"Audit: {action.value} - FAILED", extra=log_data)

