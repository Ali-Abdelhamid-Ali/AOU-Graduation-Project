"""Analytics DTOs for request validation."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, date


class AnalyticsQueryDTO(BaseModel):
    """DTO for analytics query parameters."""

    start_date: Optional[date] = Field(None, description="Start date for query")
    end_date: Optional[date] = Field(None, description="End date for query")
    hospital_id: Optional[str] = Field(None, description="Hospital ID filter")
    department: Optional[str] = Field(None, description="Department filter")
    doctor_id: Optional[str] = Field(None, description="Doctor ID filter")
    patient_id: Optional[str] = Field(None, description="Patient ID filter")
    metrics: Optional[List[str]] = Field(
        None, description="Specific metrics to include"
    )
    granularity: str = Field(
        default="daily", description="Granularity (daily, weekly, monthly)"
    )


class AnalyticsResponseDTO(BaseModel):
    """DTO for analytics responses."""

    period: str = Field(..., description="Time period")
    metrics: Dict[str, Any] = Field(..., description="Metrics data")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class PatientAnalyticsDTO(BaseModel):
    """DTO for patient analytics data."""

    patient_id: str = Field(..., description="Patient ID")
    total_visits: int = Field(..., description="Total number of visits")
    last_visit: Optional[datetime] = Field(None, description="Last visit date")
    average_visit_duration: Optional[float] = Field(
        None, description="Average visit duration in minutes"
    )
    total_cases: int = Field(..., description="Total number of cases")
    active_cases: int = Field(..., description="Number of active cases")
    completed_cases: int = Field(..., description="Number of completed cases")
    ecg_count: int = Field(..., description="Number of ECG analyses")
    mri_count: int = Field(..., description="Number of MRI analyses")
    report_count: int = Field(..., description="Number of generated reports")


class DoctorAnalyticsDTO(BaseModel):
    """DTO for doctor analytics data."""

    doctor_id: str = Field(..., description="Doctor ID")
    total_patients: int = Field(..., description="Total number of patients")
    active_patients: int = Field(..., description="Number of active patients")
    total_cases: int = Field(..., description="Total number of cases")
    completed_cases: int = Field(..., description="Number of completed cases")
    average_case_duration: Optional[float] = Field(
        None, description="Average case duration in days"
    )
    ecg_analyses: int = Field(..., description="Number of ECG analyses performed")
    mri_analyses: int = Field(..., description="Number of MRI analyses performed")
    reports_generated: int = Field(..., description="Number of reports generated")
    patient_satisfaction_score: Optional[float] = Field(
        None, ge=0.0, le=5.0, description="Patient satisfaction score"
    )


class HospitalAnalyticsDTO(BaseModel):
    """DTO for hospital analytics data."""

    hospital_id: str = Field(..., description="Hospital ID")
    total_patients: int = Field(..., description="Total number of patients")
    daily_admissions: int = Field(..., description="Daily admissions count")
    daily_discharges: int = Field(..., description="Daily discharges count")
    occupancy_rate: Optional[float] = Field(
        None, ge=0.0, le=100.0, description="Occupancy rate percentage"
    )
    average_length_of_stay: Optional[float] = Field(
        None, description="Average length of stay in days"
    )
    total_cases: int = Field(..., description="Total number of cases")
    active_cases: int = Field(..., description="Number of active cases")
    completed_cases: int = Field(..., description="Number of completed cases")
    ecg_analyses: int = Field(..., description="Number of ECG analyses")
    mri_analyses: int = Field(..., description="Number of MRI analyses")
    reports_generated: int = Field(..., description="Number of reports generated")
    revenue: Optional[float] = Field(None, description="Total revenue")


class SystemAnalyticsDTO(BaseModel):
    """DTO for system-wide analytics data."""

    total_users: int = Field(..., description="Total number of users")
    active_users: int = Field(..., description="Number of active users")
    new_users: int = Field(..., description="Number of new users")
    total_hospitals: int = Field(..., description="Total number of hospitals")
    active_hospitals: int = Field(..., description="Number of active hospitals")
    total_patients: int = Field(..., description="Total number of patients")
    active_patients: int = Field(..., description="Number of active patients")
    total_cases: int = Field(..., description="Total number of cases")
    completed_cases: int = Field(..., description="Number of completed cases")
    ecg_analyses: int = Field(..., description="Number of ECG analyses")
    mri_analyses: int = Field(..., description="Number of MRI analyses")
    reports_generated: int = Field(..., description="Number of reports generated")
    system_uptime: float = Field(
        ..., ge=0.0, le=100.0, description="System uptime percentage"
    )


class PerformanceMetricsDTO(BaseModel):
    """DTO for system performance metrics."""

    response_time: float = Field(
        ..., description="Average response time in milliseconds"
    )
    throughput: int = Field(..., description="Requests per second")
    error_rate: float = Field(..., ge=0.0, le=1.0, description="Error rate percentage")
    memory_usage: float = Field(..., description="Memory usage in MB")
    cpu_usage: float = Field(..., ge=0.0, le=100.0, description="CPU usage percentage")
    disk_usage: float = Field(
        ..., ge=0.0, le=100.0, description="Disk usage percentage"
    )


class TrendDataDTO(BaseModel):
    """DTO for trend data points."""

    timestamp: datetime = Field(..., description="Timestamp")
    value: float = Field(..., description="Metric value")
    category: Optional[str] = Field(None, description="Category or segment")


class ReportGenerationDTO(BaseModel):
    """DTO for report generation parameters."""

    report_type: str = Field(
        ..., description="Report type (patient, doctor, hospital, system)"
    )
    format: str = Field(default="pdf", description="Output format (pdf, csv, excel)")
    period: str = Field(
        default="monthly",
        description="Report period (daily, weekly, monthly, quarterly, yearly)",
    )
    parameters: Optional[Dict[str, Any]] = Field(
        default={}, description="Additional report parameters"
    )


class AppointmentUpdateDTO(BaseModel):
    """DTO for updating appointment records."""

    appointment_date: Optional[datetime] = Field(
        None, description="New appointment date and time"
    )
    status: Optional[str] = Field(
        None,
        description="Appointment status (scheduled, completed, cancelled, no-show)",
    )
    notes: Optional[str] = Field(None, description="Additional notes or comments")
    doctor_id: Optional[str] = Field(
        None, description="Doctor ID if changing assigned doctor"
    )
    department: Optional[str] = Field(None, description="Department if applicable")
    reason: Optional[str] = Field(None, description="Reason for appointment or update")
