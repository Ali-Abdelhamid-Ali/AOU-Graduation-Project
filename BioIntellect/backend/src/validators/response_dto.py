"""Response DTOs for standardized API responses."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class SuccessResponse(BaseModel):
    """Standard success response."""

    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Standard error response."""

    success: bool = False
    error: str
    message: str = "Request failed"
    details: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    correlation_id: Optional[str] = None
    timestamp: Optional[str] = None


class ErrorDetail(BaseModel):
    """Detailed error information."""

    message: Optional[str] = Field(None, description="Human readable detail")
    field: Optional[str] = Field(None, description="Field name if validation error")
    code: Optional[str] = Field(None, description="Error code")
    value: Optional[Any] = Field(None, description="Invalid value")


class ApiErrorResponse(BaseModel):
    """Canonical API error payload."""

    success: bool = False
    error: str
    message: str
    details: Optional[ErrorDetail] = None
    error_code: str
    correlation_id: str
    timestamp: str


class AuthResponse(BaseModel):
    """Authentication response."""

    success: bool = Field(True, description="Authentication status")
    message: str = Field(..., description="Authentication message")
    user: Optional[Dict[str, Any]] = Field(default=None, description="User information")
    session: Optional[Dict[str, Any]] = Field(
        default=None, description="Session information"
    )


class PaginationResponse(BaseModel):
    """Pagination metadata."""

    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")


class ListResponse(BaseModel):
    """Standard list response with pagination."""

    success: bool = Field(True, description="Success status")
    data: List[Dict[str, Any]] = Field(..., description="List of items")
    pagination: Optional[PaginationResponse] = Field(
        None, description="Pagination information"
    )
    message: Optional[str] = Field(None, description="Additional message")


# Response DTOs for medical entities
class MedicalCaseResponseDTO(BaseModel):
    """Response DTO for medical cases."""

    id: str
    case_number: str
    patient_id: str
    hospital_id: str
    assigned_doctor_id: Optional[str]
    created_by_doctor_id: Optional[str]
    status: str
    priority: str
    chief_complaint: Optional[str]
    diagnosis: Optional[str]
    treatment_plan: Optional[str]
    notes: Optional[str]
    admission_date: Optional[datetime]
    discharge_date: Optional[datetime]
    follow_up_date: Optional[datetime]
    tags: Optional[List[str]]
    is_archived: bool
    created_at: datetime
    updated_at: datetime


class MedicalFileResponseDTO(BaseModel):
    """Response DTO for medical files."""

    id: str
    case_id: str
    patient_id: str
    uploaded_by: str
    file_type: str
    file_name: str
    file_path: str
    file_size: int
    mime_type: str
    is_analyzed: bool
    created_at: datetime
    updated_at: datetime


class ECGSignalResponseDTO(BaseModel):
    """Response DTO for ECG signals."""

    id: str
    file_id: str
    patient_id: str
    case_id: Optional[str]
    signal_data: Dict[str, Any]
    sampling_rate: Optional[int]
    duration_seconds: Optional[float]
    lead_count: Optional[int]
    leads_available: Optional[List[str]]
    recording_date: Optional[datetime]
    device_info: Optional[Dict[str, Any]]
    quality_score: Optional[float]
    created_at: datetime


class ECGResultResponseDTO(BaseModel):
    """Response DTO for ECG results."""

    id: str
    signal_id: str
    patient_id: str
    case_id: Optional[str]
    analyzed_by_model: str
    model_version: Optional[str]
    analysis_status: str
    heart_rate: Optional[int]
    heart_rate_variability: Optional[float]
    rhythm_classification: Optional[str]
    rhythm_confidence: Optional[float]
    detected_conditions: Optional[List[Dict[str, Any]]]
    pr_interval: Optional[int]
    qrs_duration: Optional[int]
    qt_interval: Optional[int]
    qtc_interval: Optional[int]
    ai_interpretation: Optional[str]
    ai_recommendations: Optional[List[str]]
    risk_score: Optional[float]
    is_reviewed: bool
    reviewed_by_doctor_id: Optional[str]
    reviewed_at: Optional[datetime]
    doctor_notes: Optional[str]
    doctor_agrees_with_ai: Optional[bool]
    processing_time_ms: Optional[int]
    created_at: datetime
    updated_at: datetime


class MRIScanResponseDTO(BaseModel):
    """Response DTO for MRI scans."""

    id: str
    file_id: str
    patient_id: str
    case_id: Optional[str]
    scan_type: Optional[str]
    sequence_type: Optional[str]
    body_part: Optional[str]
    slice_count: Optional[int]
    slice_thickness_mm: Optional[float]
    field_strength: Optional[float]
    scan_date: Optional[datetime]
    device_info: Optional[Dict[str, Any]]
    dicom_metadata: Optional[Dict[str, Any]]
    created_at: datetime


class MRIResultResponseDTO(BaseModel):
    """Response DTO for MRI results."""

    id: str
    scan_id: str
    patient_id: str
    case_id: Optional[str]
    analyzed_by_model: str
    model_version: Optional[str]
    analysis_status: str
    segmentation_mask_path: Optional[str]
    segmented_regions: Optional[List[Dict[str, Any]]]
    detected_abnormalities: Optional[List[Dict[str, Any]]]
    measurements: Optional[Dict[str, Any]]
    ai_interpretation: Optional[str]
    ai_recommendations: Optional[List[str]]
    severity_score: Optional[float]
    is_reviewed: bool
    reviewed_by_doctor_id: Optional[str]
    reviewed_at: Optional[datetime]
    doctor_notes: Optional[str]
    doctor_agrees_with_ai: Optional[bool]
    processing_time_ms: Optional[int]
    created_at: datetime
    updated_at: datetime


class ReportResponseDTO(BaseModel):
    """Response DTO for reports."""

    id: str
    report_number: str
    patient_id: str
    case_id: Optional[str]
    doctor_id: Optional[str]
    report_type: str
    ecg_result_id: Optional[str]
    mri_result_id: Optional[str]
    title: str
    summary: Optional[str]
    content: Dict[str, Any]
    generated_by_model: Optional[str]
    model_version: Optional[str]
    template_used: Optional[str]
    status: str
    approved_by_doctor_id: Optional[str]
    approved_at: Optional[datetime]
    approval_notes: Optional[str]
    digital_signature: Optional[str]
    signature_timestamp: Optional[datetime]
    signed_by_doctor_id: Optional[str]
    pdf_path: Optional[str]
    pdf_generated_at: Optional[datetime]
    is_final: bool
    version: int
    previous_version_id: Optional[str]
    created_at: datetime
    updated_at: datetime
