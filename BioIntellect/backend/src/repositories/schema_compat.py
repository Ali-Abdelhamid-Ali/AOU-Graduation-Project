"""Helpers for the current Supabase schema compatibility layer."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Mapping

_TABLE_COLUMNS: dict[str, set[str]] = {
    "administrators": {
        "id",
        "user_id",
        "hospital_id",
        "employee_id",
        "first_name",
        "last_name",
        "email",
        "phone",
        "department",
        "is_active",
        "created_at",
        "updated_at",
        "role",
        "country_id",
        "region_id",
        "city",
        "address",
        "avatar_url",
    },
    "audit_logs": {
        "id",
        "user_id",
        "user_role",
        "action",
        "resource_type",
        "resource_id",
        "hospital_id",
        "patient_id",
        "description",
        "old_values",
        "new_values",
        "changes",
        "ip_address",
        "user_agent",
        "request_id",
        "is_sensitive",
        "is_flagged",
        "flag_reason",
        "created_at",
    },
    "chat_access_permissions": {
        "id",
        "patient_id",
        "conversation_id",
        "granted_by_doctor_id",
        "request_id",
        "access_level",
        "valid_from",
        "valid_until",
        "is_active",
        "revoked_at",
        "revoked_by",
        "revoke_reason",
        "last_accessed_at",
        "access_count",
        "created_at",
    },
    "chat_access_requests": {
        "id",
        "patient_id",
        "conversation_id",
        "doctor_id",
        "request_reason",
        "request_status",
        "responded_at",
        "response_notes",
        "requested_duration_hours",
        "granted_duration_hours",
        "expires_at",
        "requested_at",
        "created_at",
        "updated_at",
    },
    "data_access_logs": {
        "id",
        "user_id",
        "user_role",
        "accessed_table",
        "accessed_record_id",
        "patient_id",
        "access_type",
        "access_reason",
        "has_treatment_relationship",
        "relationship_type",
        "hospital_id",
        "case_id",
        "conversation_id",
        "ip_address",
        "user_agent",
        "created_at",
    },
    "countries": {
        "id",
        "country_code",
        "country_name_en",
        "country_name_ar",
        "phone_code",
        "is_active",
        "created_at",
        "updated_at",
    },
    "doctor_specialties": {
        "id",
        "doctor_id",
        "specialty_id",
        "is_primary",
        "certification_number",
        "certification_date",
        "expiry_date",
        "created_at",
    },
    "doctors": {
        "id",
        "user_id",
        "hospital_id",
        "employee_id",
        "first_name",
        "last_name",
        "first_name_ar",
        "last_name_ar",
        "email",
        "phone",
        "gender",
        "date_of_birth",
        "license_number",
        "license_expiry",
        "qualification",
        "years_of_experience",
        "bio",
        "avatar_url",
        "is_active",
        "is_verified",
        "verified_at",
        "verified_by",
        "settings",
        "created_at",
        "updated_at",
        "country_id",
        "region_id",
        "city",
        "address",
        "specialty",
    },
    "ecg_results": {
        "id",
        "signal_id",
        "patient_id",
        "case_id",
        "analyzed_by_model",
        "model_version",
        "analysis_status",
        "heart_rate",
        "heart_rate_variability",
        "rhythm_classification",
        "rhythm_confidence",
        "detected_conditions",
        "enriched_conditions",
        "clinical_report",
        "pr_interval",
        "qrs_duration",
        "qt_interval",
        "qtc_interval",
        "ai_interpretation",
        "ai_recommendations",
        "risk_score",
        "is_reviewed",
        "reviewed_by_doctor_id",
        "reviewed_at",
        "doctor_notes",
        "doctor_agrees_with_ai",
        "processing_time_ms",
        "raw_output",
        "error_message",
        "created_at",
        "updated_at",
    },
    "ecg_signals": {
        "id",
        "file_id",
        "patient_id",
        "case_id",
        "signal_data",
        "sampling_rate",
        "duration_seconds",
        "lead_count",
        "leads_available",
        "recording_date",
        "device_info",
        "quality_score",
        "metadata",
        "created_at",
    },
    "generated_reports": {
        "id",
        "report_number",
        "patient_id",
        "case_id",
        "doctor_id",
        "report_type",
        "ecg_result_id",
        "mri_result_id",
        "title",
        "summary",
        "content",
        "generated_by_model",
        "model_version",
        "template_used",
        "status",
        "approved_by_doctor_id",
        "approved_at",
        "approval_notes",
        "digital_signature",
        "signature_timestamp",
        "signed_by_doctor_id",
        "pdf_path",
        "pdf_generated_at",
        "is_final",
        "version",
        "previous_version_id",
        "metadata",
        "created_at",
        "updated_at",
    },
    "hospitals": {
        "id",
        "region_id",
        "hospital_code",
        "hospital_name_en",
        "hospital_name_ar",
        "address",
        "phone",
        "email",
        "license_number",
        "is_active",
        "settings",
        "created_at",
        "updated_at",
    },
    "llm_context_configs": {
        "id",
        "config_name",
        "context_type",
        "include_patient_info",
        "include_medical_history",
        "include_allergies",
        "include_medications",
        "include_recent_cases",
        "include_ecg_results",
        "include_mri_results",
        "include_doctor_info",
        "data_sources",
        "excluded_fields",
        "max_history_days",
        "access_rules",
        "system_prompt_template",
        "is_active",
        "created_at",
        "updated_at",
    },
    "llm_conversations": {
        "id",
        "conversation_type",
        "patient_id",
        "doctor_id",
        "case_id",
        "hospital_id",
        "title",
        "system_prompt",
        "llm_model",
        "temperature",
        "max_tokens",
        "is_active",
        "is_archived",
        "archived_at",
        "message_count",
        "total_tokens_used",
        "last_message_at",
        "metadata",
        "created_at",
        "updated_at",
    },
    "llm_messages": {
        "id",
        "conversation_id",
        "sender_type",
        "sender_id",
        "message_content",
        "message_type",
        "llm_model_used",
        "tokens_used",
        "prompt_tokens",
        "completion_tokens",
        "llm_context_snapshot",
        "attachments",
        "is_edited",
        "edited_at",
        "is_deleted",
        "deleted_at",
        "metadata",
        "created_at",
    },
    "medical_cases": {
        "id",
        "case_number",
        "patient_id",
        "hospital_id",
        "assigned_doctor_id",
        "created_by_doctor_id",
        "status",
        "priority",
        "chief_complaint",
        "diagnosis",
        "diagnosis_icd10",
        "treatment_plan",
        "notes",
        "admission_date",
        "discharge_date",
        "follow_up_date",
        "tags",
        "metadata",
        "is_archived",
        "archived_at",
        "archived_by",
        "created_at",
        "updated_at",
    },
    "medical_files": {
        "id",
        "case_id",
        "patient_id",
        "uploaded_by",
        "file_type",
        "file_name",
        "file_path",
        "file_size",
        "mime_type",
        "storage_bucket",
        "description",
        "metadata",
        "is_analyzed",
        "analyzed_at",
        "is_deleted",
        "deleted_at",
        "deleted_by",
        "created_at",
        "updated_at",
    },
    "model_versions": {
        "id",
        "model_name",
        "model_version",
        "model_type",
        "description",
        "provider",
        "accuracy",
        "precision_score",
        "recall",
        "f1_score",
        "validation_dataset",
        "default_config",
        "is_active",
        "is_production",
        "deployed_at",
        "deprecated_at",
        "created_by",
        "created_at",
        "updated_at",
    },
    "mri_segmentation_results": {
        "id",
        "scan_id",
        "patient_id",
        "case_id",
        "analyzed_by_model",
        "model_version",
        "analysis_status",
        "segmentation_mask_path",
        "segmented_regions",
        "detected_abnormalities",
        "measurements",
        "ai_interpretation",
        "ai_recommendations",
        "severity_score",
        "is_reviewed",
        "reviewed_by_doctor_id",
        "reviewed_at",
        "doctor_notes",
        "doctor_agrees_with_ai",
        "processing_time_ms",
        "raw_output",
        "error_message",
        "created_at",
        "updated_at",
    },
    "mri_scans": {
        "id",
        "file_id",
        "patient_id",
        "case_id",
        "scan_type",
        "sequence_type",
        "body_part",
        "slice_count",
        "slice_thickness_mm",
        "field_strength",
        "scan_date",
        "device_info",
        "dicom_metadata",
        "created_at",
    },
    "nurses": {
        "id",
        "user_id",
        "hospital_id",
        "employee_id",
        "first_name",
        "last_name",
        "email",
        "phone",
        "license_number",
        "department",
        "is_active",
        "created_at",
        "updated_at",
        "country_id",
        "region_id",
        "city",
        "address",
        "avatar_url",
    },
    "notifications": {
        "id",
        "user_id",
        "notification_type",
        "title",
        "message",
        "resource_type",
        "resource_id",
        "action_url",
        "hospital_id",
        "patient_id",
        "is_read",
        "read_at",
        "is_archived",
        "archived_at",
        "priority",
        "expires_at",
        "metadata",
        "created_at",
    },
    "patients": {
        "id",
        "user_id",
        "hospital_id",
        "mrn",
        "first_name",
        "last_name",
        "first_name_ar",
        "last_name_ar",
        "email",
        "phone",
        "gender",
        "date_of_birth",
        "blood_type",
        "national_id",
        "passport_number",
        "address",
        "city",
        "region_id",
        "country_id",
        "avatar_url",
        "emergency_contact_name",
        "emergency_contact_phone",
        "emergency_contact_relation",
        "allergies",
        "chronic_conditions",
        "current_medications",
        "insurance_provider",
        "insurance_number",
        "primary_doctor_id",
        "is_active",
        "notes",
        "settings",
        "created_at",
        "updated_at",
    },
    "regions": {
        "id",
        "country_id",
        "region_code",
        "region_name_en",
        "region_name_ar",
        "is_active",
        "created_at",
        "updated_at",
    },
    "specialty_types": {
        "id",
        "specialty_code",
        "specialty_name_en",
        "specialty_name_ar",
        "specialty_category",
        "parent_specialty_id",
        "description",
        "is_active",
        "created_at",
        "updated_at",
    },
    "system_settings": {
        "id",
        "scope",
        "scope_id",
        "setting_key",
        "setting_value",
        "setting_type",
        "description",
        "is_sensitive",
        "created_by",
        "updated_by",
        "created_at",
        "updated_at",
    },
    "user_roles": {
        "id",
        "user_id",
        "role",
        "hospital_id",
        "granted_by",
        "granted_at",
        "expires_at",
        "is_active",
        "created_at",
    },
}

_VALID_APP_ROLES = {"super_admin", "admin", "doctor", "nurse", "patient"}
_EXECUTION_LOG_ACTION = "execution_log"

_NOTIFICATION_TYPE_TO_SCHEMA = {
    "message": "system_alert",
    "alert": "system_alert",
    "system": "system_alert",
    "reminder": "system_alert",
    "appointment": "case_update",
    "result": "new_result",
    "case_assigned": "new_case",
    "case_updated": "case_update",
    "report_ready": "new_result",
    "chat_access_request": "chat_access_request",
    "chat_access_approved": "chat_access_approved",
    "chat_access_rejected": "chat_access_rejected",
    "new_case": "new_case",
    "case_update": "case_update",
    "new_result": "new_result",
    "system_alert": "system_alert",
}

_SCHEMA_TYPE_TO_NOTIFICATION = {
    "chat_access_request": "chat_access_request",
    "chat_access_approved": "chat_access_approved",
    "chat_access_rejected": "chat_access_rejected",
    "new_case": "case_assigned",
    "case_update": "case_updated",
    "new_result": "report_ready",
    "system_alert": "system",
}


def sanitize_for_table(table_name: str, data: Mapping[str, Any] | None) -> dict[str, Any]:
    """Drop keys that do not exist in the current schema."""
    if not data:
        return {}
    allowed = _TABLE_COLUMNS.get(table_name)
    if not allowed:
        return dict(data)
    return {key: value for key, value in data.items() if key in allowed}


def select_columns_for_table(table_name: str, columns: list[str] | tuple[str, ...]) -> str:
    """Keep only columns that exist in the active schema before building a select list."""
    allowed = _TABLE_COLUMNS.get(table_name)
    normalized_columns = [column.strip() for column in columns if str(column).strip()]

    if not allowed:
        return ", ".join(normalized_columns)

    return ", ".join(column for column in normalized_columns if column in allowed)


def map_notification_type(value: str | None) -> str:
    """Translate legacy notification labels into schema enum values."""
    if not value:
        return "system_alert"
    if hasattr(value, "value"):
        value = value.value
    if not value:
        return "system_alert"
    return _NOTIFICATION_TYPE_TO_SCHEMA.get(str(value), "system_alert")


def normalize_audit_log(record: Mapping[str, Any] | None) -> dict[str, Any]:
    """Expose backward-compatible aliases expected by older services."""
    if not record:
        return {}
    normalized = dict(record)
    payload = audit_payload(record)
    normalized.setdefault("details", payload)
    normalized.setdefault("timestamp", normalized.get("created_at"))
    return normalized


def audit_payload(record: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return the structured payload stored in audit-style rows."""
    if not record:
        return {}
    for key in ("changes", "new_values", "old_values", "details"):
        value = record.get(key)
        if isinstance(value, dict):
            return value
    return {}


def build_audit_log_payload(data: Mapping[str, Any] | None) -> dict[str, Any]:
    """Map legacy audit payloads to the active audit_logs schema."""
    payload = dict(data or {})
    details = payload.pop("details", None)
    timestamp = payload.pop("timestamp", None)
    payload.pop("updated_at", None)
    payload.pop("flagged_at", None)
    payload.pop("flagged_by", None)
    payload.pop("success", None)
    payload.pop("email", None)
    payload.pop("correlation_id", None)
    payload.pop("audit", None)
    payload.pop("outcome", None)
    if details is not None and "changes" not in payload:
        payload["changes"] = details
    if timestamp and "created_at" not in payload:
        payload["created_at"] = timestamp
    return sanitize_for_table("audit_logs", payload)


def normalize_data_access_log(record: Mapping[str, Any] | None) -> dict[str, Any]:
    """Expose stable aliases for data access rows."""
    if not record:
        return {}
    normalized = dict(record)
    normalized.setdefault("accessed_at", normalized.get("created_at"))
    normalized.setdefault(
        "details",
        {
            "access_reason": normalized.get("access_reason"),
            "relationship_type": normalized.get("relationship_type"),
            "has_treatment_relationship": normalized.get("has_treatment_relationship"),
        },
    )
    return normalized


def build_data_access_log_payload(data: Mapping[str, Any] | None) -> dict[str, Any]:
    """Map legacy access-log payloads into the current schema."""
    payload = dict(data or {})
    details = payload.pop("details", None)
    accessed_at = payload.pop("accessed_at", None)
    payload.pop("updated_at", None)

    if isinstance(details, dict):
        payload.setdefault(
            "access_reason",
            details.get("access_reason") or details.get("reason"),
        )
        payload.setdefault("relationship_type", details.get("relationship_type"))
        if (
            "has_treatment_relationship" not in payload
            and "has_treatment_relationship" in details
        ):
            payload["has_treatment_relationship"] = details[
                "has_treatment_relationship"
            ]

    if accessed_at and "created_at" not in payload:
        payload["created_at"] = accessed_at

    return sanitize_for_table("data_access_logs", payload)


def normalize_notification_record(record: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return notification records in the legacy API shape."""
    if not record:
        return {}
    normalized = dict(record)
    metadata = normalized.get("metadata")
    metadata = metadata if isinstance(metadata, dict) else {}
    normalized["metadata"] = metadata
    schema_type = str(normalized.get("notification_type") or "system_alert")
    legacy_type = metadata.get("legacy_type") or _SCHEMA_TYPE_TO_NOTIFICATION.get(
        schema_type, schema_type
    )
    normalized.setdefault("recipient_id", normalized.get("user_id"))
    normalized.setdefault("type", legacy_type)
    normalized.setdefault("content", normalized.get("message"))
    normalized.setdefault(
        "updated_at",
        normalized.get("archived_at")
        or normalized.get("read_at")
        or normalized.get("created_at"),
    )
    if metadata.get("sender_id") and "sender_id" not in normalized:
        normalized["sender_id"] = metadata["sender_id"]
    return normalized


def build_notification_payload(
    *,
    user_id: str,
    notification_type: str,
    title: str,
    message: str,
    priority: str = "normal",
    metadata: Mapping[str, Any] | None = None,
    action_url: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    hospital_id: str | None = None,
    patient_id: str | None = None,
    expires_at: str | datetime | None = None,
    sender_id: str | None = None,
) -> dict[str, Any]:
    """Map legacy notification inputs to the active notifications schema."""
    normalized_type = _NOTIFICATION_TYPE_TO_SCHEMA.get(notification_type, "system_alert")
    merged_metadata = dict(metadata or {})
    merged_metadata.setdefault("legacy_type", notification_type)
    if sender_id:
        merged_metadata.setdefault("sender_id", sender_id)
    payload = {
        "user_id": user_id,
        "notification_type": normalized_type,
        "title": title,
        "message": message,
        "priority": priority,
        "metadata": merged_metadata,
        "action_url": action_url,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "hospital_id": hospital_id,
        "patient_id": patient_id,
        "expires_at": expires_at.isoformat()
        if isinstance(expires_at, datetime)
        else expires_at,
    }
    return sanitize_for_table("notifications", payload)


def coerce_notification_payload(data: Mapping[str, Any] | None) -> dict[str, Any]:
    """Translate legacy notification fields into the active schema."""
    payload = dict(data or {})
    recipient_id = payload.pop("recipient_id", None)
    legacy_type = payload.pop("type", None)
    content = payload.pop("content", None)
    updated_at = payload.pop("updated_at", None)

    if recipient_id and "user_id" not in payload:
        payload["user_id"] = recipient_id
    if legacy_type and "notification_type" not in payload:
        payload["notification_type"] = map_notification_type(legacy_type)
    elif payload.get("notification_type"):
        payload["notification_type"] = map_notification_type(
            str(payload.get("notification_type"))
        )
    if content is not None and "message" not in payload:
        payload["message"] = content
    if payload.get("is_read") and updated_at and "read_at" not in payload:
        payload["read_at"] = updated_at
    if payload.get("is_archived") and updated_at and "archived_at" not in payload:
        payload["archived_at"] = updated_at

    metadata = payload.get("metadata")
    metadata = dict(metadata) if isinstance(metadata, dict) else {}
    if legacy_type:
        metadata.setdefault("legacy_type", legacy_type)
    if metadata:
        payload["metadata"] = metadata

    return sanitize_for_table("notifications", payload)


def build_follow_up_appointment(
    case_record: Mapping[str, Any],
    *,
    patient: Mapping[str, Any] | None = None,
    doctor: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Represent medical_cases.follow_up_date as a lightweight appointment."""
    metadata = case_record.get("metadata")
    metadata = metadata if isinstance(metadata, dict) else {}
    follow_up_date = case_record.get("follow_up_date")
    appointment_date = _iso_date(follow_up_date)
    if not appointment_date:
        return {}

    status = metadata.get("appointment_status")
    if not status:
        case_status = str(case_record.get("status") or "").lower()
        status = "completed" if case_status in {"completed", "archived"} else "scheduled"
    status = " ".join(
        fragment.capitalize()
        for fragment in str(status or "scheduled").replace("_", " ").split()
    ) or "Scheduled"
    appointment_type = str(metadata.get("appointment_type") or "Follow-up").strip() or "Follow-up"

    appointment = {
        "id": str(case_record.get("id") or ""),
        "case_id": case_record.get("id"),
        "case_number": case_record.get("case_number"),
        "patient_id": case_record.get("patient_id"),
        "doctor_id": case_record.get("assigned_doctor_id"),
        "appointment_date": appointment_date,
        "appointment_time": metadata.get("appointment_time"),
        "status": status,
        "appointment_type": appointment_type,
        "notes": metadata.get("appointment_notes") or case_record.get("notes"),
        "reason": metadata.get("appointment_reason")
        or case_record.get("chief_complaint"),
        "department": metadata.get("department")
        or (doctor or {}).get("specialty"),
        "patients": dict(patient) if patient else None,
        "doctors": dict(doctor) if doctor else None,
    }
    return appointment


def normalize_mri_result_record(record: Mapping[str, Any] | None) -> dict[str, Any]:
    """Expose compatibility fields expected by the current API DTOs."""
    if not record:
        return {}
    normalized = dict(record)
    measurements = normalized.get("measurements")
    measurements = measurements if isinstance(measurements, dict) else {}
    compat = measurements.get("_compat")
    compat = compat if isinstance(compat, dict) else {}
    abnormalities = normalized.get("detected_abnormalities")
    abnormalities = abnormalities if isinstance(abnormalities, list) else []
    normalized["detected_abnormalities"] = abnormalities
    normalized.setdefault("segmented_regions", normalized.get("segmented_regions") or [])
    normalized.setdefault("ai_recommendations", normalized.get("ai_recommendations") or [])
    normalized.setdefault("measurements", measurements)
    normalized.setdefault(
        "tumor_detected",
        compat.get("tumor_detected")
        if "tumor_detected" in compat
        else bool(abnormalities or normalized.get("severity_score")),
    )
    normalized.setdefault(
        "confidence_score",
        compat.get("confidence_score")
        if "confidence_score" in compat
        else compat.get("confidence")
        if "confidence" in compat
        else normalized.get("severity_score"),
    )
    return normalized


def normalize_ecg_result_record(record: Mapping[str, Any] | None) -> dict[str, Any]:
    """Expose compatibility fields for legacy ECG consumers."""
    if not record:
        return {}
    normalized = dict(record)
    normalized.setdefault("confidence_score", normalized.get("rhythm_confidence"))
    normalized.setdefault("primary_diagnosis", normalized.get("rhythm_classification"))
    normalized.setdefault("details", normalized.get("raw_output") or {})
    normalized.setdefault("enriched_conditions", normalized.get("enriched_conditions") or [])
    normalized.setdefault("clinical_report", normalized.get("clinical_report"))
    return normalized


def build_mri_result_payload(data: Mapping[str, Any] | None) -> dict[str, Any]:
    """Map legacy MRI payload keys into supported schema fields."""
    payload = dict(data or {})
    measurements = payload.get("measurements")
    measurements = dict(measurements) if isinstance(measurements, dict) else {}
    compat: dict[str, Any] = {}

    for legacy_key in ("tumor_detected", "confidence_score", "performed_by"):
        if legacy_key in payload:
            compat[legacy_key] = payload.pop(legacy_key)

    if compat:
        measurements["_compat"] = {**measurements.get("_compat", {}), **compat}
        payload["measurements"] = measurements

    return sanitize_for_table("mri_segmentation_results", payload)


def build_execution_log_payload(log_entry: Mapping[str, Any] | None) -> dict[str, Any]:
    """Persist execution monitoring rows inside audit_logs."""
    entry = dict(log_entry or {})
    request = entry.get("request")
    request = dict(request) if isinstance(request, dict) else {}
    response = entry.get("response")
    response = dict(response) if isinstance(response, dict) else {}
    performance = entry.get("performance")
    performance = dict(performance) if isinstance(performance, dict) else {}
    error = entry.get("error")
    error = dict(error) if isinstance(error, dict) else {}

    user_role = entry.get("user_role")
    if user_role not in _VALID_APP_ROLES:
        user_role = None

    payload = {
        "user_id": entry.get("user_id"),
        "user_role": user_role,
        "action": _EXECUTION_LOG_ACTION,
        "resource_type": "execution_request",
        "description": " ".join(
            part for part in [request.get("method"), request.get("path")] if part
        )
        or "execution request",
        "ip_address": request.get("client_ip"),
        "user_agent": request.get("user_agent"),
        "created_at": entry.get("timestamp"),
        "changes": {
            "correlation_id": entry.get("correlation_id"),
            "request_method": request.get("method"),
            "request_path": request.get("path"),
            "request_headers": request.get("headers"),
            "request_query_params": request.get("query_params"),
            "status_code": response.get("status_code"),
            "response_headers": response.get("headers"),
            "duration_ms": performance.get("total_duration_ms"),
            "memory_usage_mb": performance.get("memory_usage_mb"),
            "cpu_percent": performance.get("cpu_percent"),
            "success": performance.get("success"),
            "error_type": error.get("type"),
            "error_message": error.get("message"),
            "error_category": error.get("category")
            or performance.get("error_category"),
            "error_priority": error.get("priority")
            or performance.get("error_priority"),
            "error_stack_trace": error.get("stack_trace"),
            "client_ip": request.get("client_ip"),
            "user_agent": request.get("user_agent"),
            "raw_data": entry,
        },
    }
    return sanitize_for_table("audit_logs", payload)


def normalize_execution_log_record(record: Mapping[str, Any] | None) -> dict[str, Any]:
    """Expose audit-backed execution logs in the legacy monitoring shape."""
    if not record:
        return {}
    normalized = dict(record)
    payload = audit_payload(record)
    status_code = payload.get("status_code")
    success = payload.get("success")
    if success is None:
        try:
            success = int(status_code) < 400 if status_code is not None else True
        except (TypeError, ValueError):
            success = True

    normalized.update(
        {
            "timestamp": normalized.get("created_at"),
            "correlation_id": payload.get("correlation_id"),
            "request_method": payload.get("request_method"),
            "request_path": payload.get("request_path"),
            "status_code": status_code,
            "duration_ms": payload.get("duration_ms"),
            "memory_usage_mb": payload.get("memory_usage_mb"),
            "cpu_percent": payload.get("cpu_percent"),
            "success": success,
            "error_type": payload.get("error_type"),
            "error_message": payload.get("error_message"),
            "error_category": payload.get("error_category"),
            "error_priority": payload.get("error_priority"),
            "client_ip": payload.get("client_ip") or normalized.get("ip_address"),
            "user_agent": payload.get("user_agent") or normalized.get("user_agent"),
            "raw_data": payload.get("raw_data") or payload,
        }
    )
    return normalized


def build_preferences_setting(
    user_id: str,
    preferences: Mapping[str, Any],
    *,
    setting_id: str | None = None,
) -> dict[str, Any]:
    """Persist notification preferences in system_settings."""
    payload = {
        "id": setting_id,
        "scope": "user",
        "scope_id": user_id,
        "setting_key": "notification_preferences",
        "setting_value": dict(preferences),
        "setting_type": "json",
        "description": "Per-user notification preferences",
        "is_sensitive": False,
    }
    return sanitize_for_table("system_settings", payload)


def _iso_date(value: Any) -> str | None:
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, datetime):
        return value.date().isoformat()
    text = str(value or "").strip()
    if not text:
        return None
    return text[:10]
