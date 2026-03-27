"""Medical DTOs for request validation."""

from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime, date


# =====================================================
# GEOGRAPHIC TABLES
# =====================================================


class CountryCreateDTO(BaseModel):
    """DTO for creating countries."""

    country_code: str = Field(
        ..., min_length=1, max_length=3, description="Country code"
    )
    country_name_en: str = Field(
        ..., min_length=2, description="Country name in English"
    )
    country_name_ar: Optional[str] = Field(None, description="Country name in Arabic")
    phone_code: Optional[str] = Field(None, max_length=10, description="Phone code")
    is_active: bool = Field(default=True, description="Whether country is active")


class CountryUpdateDTO(BaseModel):
    """DTO for updating countries."""

    country_code: Optional[str] = Field(
        None, min_length=1, max_length=3, description="Country code"
    )
    country_name_en: Optional[str] = Field(
        None, min_length=2, description="Country name in English"
    )
    country_name_ar: Optional[str] = Field(None, description="Country name in Arabic")
    phone_code: Optional[str] = Field(None, max_length=10, description="Phone code")
    is_active: Optional[bool] = Field(None, description="Whether country is active")


class CountryResponseDTO(BaseModel):
    """Response DTO for countries."""

    id: str
    country_code: str
    country_name_en: str
    country_name_ar: Optional[str]
    phone_code: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class RegionCreateDTO(BaseModel):
    """DTO for creating regions."""

    country_id: str = Field(..., description="Country ID")
    region_code: str = Field(
        ..., min_length=2, max_length=10, description="Region code"
    )
    region_name_en: str = Field(..., min_length=2, description="Region name in English")
    region_name_ar: Optional[str] = Field(None, description="Region name in Arabic")
    is_active: bool = Field(default=True, description="Whether region is active")


class RegionUpdateDTO(BaseModel):
    """DTO for updating regions."""

    country_id: Optional[str] = Field(None, description="Country ID")
    region_code: Optional[str] = Field(
        None, min_length=2, max_length=10, description="Region code"
    )
    region_name_en: Optional[str] = Field(
        None, min_length=2, description="Region name in English"
    )
    region_name_ar: Optional[str] = Field(None, description="Region name in Arabic")
    is_active: Optional[bool] = Field(None, description="Whether region is active")


class RegionResponseDTO(BaseModel):
    """Response DTO for regions."""

    id: str
    country_id: str
    region_code: str
    region_name_en: str
    region_name_ar: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class HospitalCreateDTO(BaseModel):
    """DTO for creating hospitals."""

    region_id: str = Field(..., description="Region ID")
    hospital_code: str = Field(
        ..., min_length=2, max_length=10, description="Hospital code"
    )
    hospital_name_en: str = Field(
        ..., min_length=2, description="Hospital name in English"
    )
    hospital_name_ar: Optional[str] = Field(None, description="Hospital name in Arabic")
    address: Optional[str] = Field(None, description="Hospital address")
    phone: Optional[str] = Field(
        None, max_length=20, description="Hospital phone number"
    )
    email: Optional[EmailStr] = Field(None, description="Hospital email")
    license_number: Optional[str] = Field(
        None, max_length=50, description="License number"
    )
    is_active: bool = Field(default=True, description="Whether hospital is active")
    settings: Optional[Dict[str, Any]] = Field(
        default={}, description="Hospital settings"
    )


class HospitalUpdateDTO(BaseModel):
    """DTO for updating hospitals."""

    region_id: Optional[str] = Field(None, description="Region ID")
    hospital_code: Optional[str] = Field(
        None, min_length=2, max_length=10, description="Hospital code"
    )
    hospital_name_en: Optional[str] = Field(
        None, min_length=2, description="Hospital name in English"
    )
    hospital_name_ar: Optional[str] = Field(None, description="Hospital name in Arabic")
    address: Optional[str] = Field(None, description="Hospital address")
    phone: Optional[str] = Field(
        None, max_length=20, description="Hospital phone number"
    )
    email: Optional[EmailStr] = Field(None, description="Hospital email")
    license_number: Optional[str] = Field(
        None, max_length=50, description="License number"
    )
    is_active: Optional[bool] = Field(None, description="Whether hospital is active")
    settings: Optional[Dict[str, Any]] = Field(None, description="Hospital settings")


class HospitalResponseDTO(BaseModel):
    """Response DTO for hospitals."""

    id: str
    region_id: str
    hospital_code: str
    hospital_name_en: str
    hospital_name_ar: Optional[str]
    address: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    license_number: Optional[str]
    is_active: bool
    settings: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


# =====================================================
# USER ROLES TABLE
# =====================================================


class UserRoleCreateDTO(BaseModel):
    """DTO for creating user roles."""

    user_id: str = Field(..., description="User ID")
    role: str = Field(..., description="Role name")
    hospital_id: Optional[str] = Field(None, description="Hospital ID")
    granted_by: Optional[str] = Field(None, description="Granted by user ID")
    expires_at: Optional[datetime] = Field(None, description="Expiration date")
    is_active: bool = Field(default=True, description="Whether role is active")


class UserRoleUpdateDTO(BaseModel):
    """DTO for updating user roles."""

    role: Optional[str] = Field(None, description="Role name")
    hospital_id: Optional[str] = Field(None, description="Hospital ID")
    granted_by: Optional[str] = Field(None, description="Granted by user ID")
    expires_at: Optional[datetime] = Field(None, description="Expiration date")
    is_active: Optional[bool] = Field(None, description="Whether role is active")


class UserRoleResponseDTO(BaseModel):
    """Response DTO for user roles."""

    id: str
    user_id: str
    role: str
    hospital_id: Optional[str]
    granted_by: Optional[str]
    granted_at: datetime
    expires_at: Optional[datetime]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


# =====================================================
# SPECIALTY TABLES
# =====================================================


class SpecialtyTypeCreateDTO(BaseModel):
    """DTO for creating specialty types."""

    specialty_code: str = Field(
        ..., min_length=2, max_length=20, description="Specialty code"
    )
    specialty_name_en: str = Field(
        ..., min_length=2, description="Specialty name in English"
    )
    specialty_name_ar: Optional[str] = Field(
        None, description="Specialty name in Arabic"
    )
    specialty_category: str = Field(default="medical", description="Specialty category")
    parent_specialty_id: Optional[str] = Field(None, description="Parent specialty ID")
    description: Optional[str] = Field(None, description="Specialty description")
    is_active: bool = Field(default=True, description="Whether specialty is active")


class SpecialtyTypeUpdateDTO(BaseModel):
    """DTO for updating specialty types."""

    specialty_code: Optional[str] = Field(
        None, min_length=2, max_length=20, description="Specialty code"
    )
    specialty_name_en: Optional[str] = Field(
        None, min_length=2, description="Specialty name in English"
    )
    specialty_name_ar: Optional[str] = Field(
        None, description="Specialty name in Arabic"
    )
    specialty_category: Optional[str] = Field(None, description="Specialty category")
    parent_specialty_id: Optional[str] = Field(None, description="Parent specialty ID")
    description: Optional[str] = Field(None, description="Specialty description")
    is_active: Optional[bool] = Field(None, description="Whether specialty is active")


class SpecialtyTypeResponseDTO(BaseModel):
    """Response DTO for specialty types."""

    id: str
    specialty_code: str
    specialty_name_en: str
    specialty_name_ar: Optional[str]
    specialty_category: str
    parent_specialty_id: Optional[str]
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


# =====================================================
# USER PROFILE TABLES
# =====================================================


class DoctorCreateDTO(BaseModel):
    """DTO for creating doctors."""

    hospital_id: str = Field(..., description="Hospital ID")
    first_name: str = Field(..., min_length=2, description="First name")
    last_name: str = Field(..., min_length=2, description="Last name")
    email: EmailStr = Field(..., description="Email")
    password: str = Field(..., min_length=8, description="Initial password")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    specialty: str = Field(..., description="Doctor's primary specialty")
    license_number: str = Field(..., min_length=5, description="Medical license number")
    employee_id: Optional[str] = Field(None, max_length=50, description="Employee ID")
    first_name_ar: Optional[str] = Field(None, description="First name in Arabic")
    last_name_ar: Optional[str] = Field(None, description="Last name in Arabic")
    gender: Optional[str] = Field(None, description="Gender")
    date_of_birth: Optional[date] = Field(None, description="Date of birth")
    license_expiry: Optional[date] = Field(None, description="License expiry date")
    qualification: Optional[str] = Field(None, description="Qualification")
    years_of_experience: int = Field(default=0, ge=0, description="Years of experience")
    bio: Optional[str] = Field(None, description="Bio")
    country_id: Optional[str] = Field(None, description="Country ID")
    region_id: Optional[str] = Field(None, description="Region ID")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    is_active: bool = Field(default=True, description="Whether doctor is active")
    settings: Optional[Dict[str, Any]] = Field(
        default={}, description="Doctor settings"
    )


class DoctorUpdateDTO(BaseModel):
    """DTO for updating doctors."""

    hospital_id: Optional[str] = Field(None, description="Hospital ID")
    employee_id: Optional[str] = Field(None, max_length=50, description="Employee ID")
    first_name: Optional[str] = Field(None, min_length=2, description="First name")
    last_name: Optional[str] = Field(None, min_length=2, description="Last name")
    first_name_ar: Optional[str] = Field(None, description="First name in Arabic")
    last_name_ar: Optional[str] = Field(None, description="Last name in Arabic")
    email: Optional[EmailStr] = Field(None, description="Email")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    gender: Optional[str] = Field(None, description="Gender")
    date_of_birth: Optional[date] = Field(None, description="Date of birth")
    license_number: Optional[str] = Field(
        None, min_length=5, description="Medical license number"
    )
    license_expiry: Optional[date] = Field(None, description="License expiry date")
    qualification: Optional[str] = Field(None, description="Qualification")
    years_of_experience: Optional[int] = Field(
        None, ge=0, description="Years of experience"
    )
    bio: Optional[str] = Field(None, description="Bio")
    country_id: Optional[str] = Field(None, description="Country ID")
    region_id: Optional[str] = Field(None, description="Region ID")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    is_active: Optional[bool] = Field(None, description="Whether doctor is active")
    is_verified: Optional[bool] = Field(None, description="Whether doctor is verified")
    verified_at: Optional[datetime] = Field(None, description="Verified at")
    verified_by: Optional[str] = Field(None, description="Verified by user ID")
    settings: Optional[Dict[str, Any]] = Field(None, description="Doctor settings")


class DoctorResponseDTO(BaseModel):
    """Response DTO for doctors."""

    id: str
    user_id: str
    hospital_id: str
    employee_id: Optional[str]
    first_name: str
    last_name: str
    first_name_ar: Optional[str]
    last_name_ar: Optional[str]
    email: str
    phone: Optional[str]
    gender: Optional[str]
    date_of_birth: Optional[date]
    license_number: str
    license_expiry: Optional[date]
    qualification: Optional[str]
    years_of_experience: int
    bio: Optional[str]
    country_id: Optional[str]
    region_id: Optional[str]
    avatar_url: Optional[str]
    is_active: bool
    is_verified: bool
    verified_at: Optional[datetime]
    verified_by: Optional[str]
    settings: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class DoctorSpecialtyCreateDTO(BaseModel):
    """DTO for creating doctor specialties."""

    specialty_id: str = Field(..., description="Specialty ID")
    is_primary: bool = Field(
        default=False, description="Whether this is the primary specialty"
    )
    certification_number: Optional[str] = Field(
        None, max_length=100, description="Certification number"
    )
    certification_date: Optional[date] = Field(None, description="Certification date")
    expiry_date: Optional[date] = Field(None, description="Expiry date")


class DoctorSpecialtyUpdateDTO(BaseModel):
    """DTO for updating doctor specialties."""

    specialty_id: Optional[str] = Field(None, description="Specialty ID")
    is_primary: Optional[bool] = Field(
        None, description="Whether this is the primary specialty"
    )
    certification_number: Optional[str] = Field(
        None, max_length=100, description="Certification number"
    )
    certification_date: Optional[date] = Field(None, description="Certification date")
    expiry_date: Optional[date] = Field(None, description="Expiry date")


class DoctorSpecialtyResponseDTO(BaseModel):
    """Response DTO for doctor specialties."""

    id: str
    doctor_id: str
    specialty_id: str
    is_primary: bool
    certification_number: Optional[str]
    certification_date: Optional[date]
    expiry_date: Optional[date]
    created_at: datetime


class AdministratorCreateDTO(BaseModel):
    """DTO for creating administrators."""

    hospital_id: Optional[str] = Field(None, description="Hospital ID")
    first_name: str = Field(..., min_length=2, description="First name")
    last_name: str = Field(..., min_length=2, description="Last name")
    email: EmailStr = Field(..., description="Email")
    password: str = Field(..., min_length=8, description="Initial password")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    department: str = Field(..., min_length=2, description="Department")
    employee_id: Optional[str] = Field(None, max_length=50, description="Employee ID")
    country_id: Optional[str] = Field(None, description="Country ID")
    region_id: Optional[str] = Field(None, description="Region ID")
    is_active: bool = Field(default=True, description="Whether administrator is active")
    role: str = Field(
        default="admin", description="Admin role level (admin, super_admin)"
    )


class AdministratorUpdateDTO(BaseModel):
    """DTO for updating administrators."""

    hospital_id: Optional[str] = Field(None, description="Hospital ID")
    employee_id: Optional[str] = Field(None, max_length=50, description="Employee ID")
    first_name: Optional[str] = Field(None, min_length=2, description="First name")
    last_name: Optional[str] = Field(None, min_length=2, description="Last name")
    email: Optional[EmailStr] = Field(None, description="Email")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    department: Optional[str] = Field(None, min_length=2, description="Department")
    country_id: Optional[str] = Field(None, description="Country ID")
    region_id: Optional[str] = Field(None, description="Region ID")
    is_active: Optional[bool] = Field(
        None, description="Whether administrator is active"
    )


class AdministratorResponseDTO(BaseModel):
    """Response DTO for administrators."""

    id: str
    user_id: str
    hospital_id: Optional[str]
    employee_id: Optional[str]
    first_name: str
    last_name: str
    email: str
    phone: Optional[str]
    department: str
    avatar_url: Optional[str] = None
    role: Optional[str] = "admin"
    country_id: Optional[str] = None
    region_id: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class NurseCreateDTO(BaseModel):
    """DTO for creating nurses."""

    user_id: str = Field(..., description="User ID")
    hospital_id: str = Field(..., description="Hospital ID")
    employee_id: Optional[str] = Field(None, max_length=50, description="Employee ID")
    first_name: str = Field(..., min_length=2, description="First name")
    last_name: str = Field(..., min_length=2, description="Last name")
    email: EmailStr = Field(..., description="Email")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    license_number: Optional[str] = Field(
        None, max_length=50, description="Nursing license number"
    )
    department: str = Field(..., min_length=2, description="Department")
    is_active: bool = Field(default=True, description="Whether nurse is active")


class NurseUpdateDTO(BaseModel):
    """DTO for updating nurses."""

    hospital_id: Optional[str] = Field(None, description="Hospital ID")
    employee_id: Optional[str] = Field(None, max_length=50, description="Employee ID")
    first_name: Optional[str] = Field(None, min_length=2, description="First name")
    last_name: Optional[str] = Field(None, min_length=2, description="Last name")
    email: Optional[EmailStr] = Field(None, description="Email")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    license_number: Optional[str] = Field(
        None, max_length=50, description="Nursing license number"
    )
    department: Optional[str] = Field(None, min_length=2, description="Department")
    is_active: Optional[bool] = Field(None, description="Whether nurse is active")


class NurseResponseDTO(BaseModel):
    """Response DTO for nurses."""

    id: str
    user_id: str
    hospital_id: str
    employee_id: Optional[str]
    first_name: str
    last_name: str
    email: str
    phone: Optional[str]
    license_number: Optional[str]
    department: str
    avatar_url: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PatientCreateDTO(BaseModel):
    """DTO for creating patients."""

    hospital_id: str = Field(..., description="Hospital ID")
    first_name: str = Field(..., min_length=2, description="First name")
    last_name: str = Field(..., min_length=2, description="Last name")
    email: EmailStr = Field(..., description="Email")
    password: str = Field(..., min_length=8, description="Initial password")
    phone: str = Field(..., max_length=20, description="Phone number")
    date_of_birth: date = Field(..., description="Date of birth")
    gender: str = Field(..., description="Gender")
    first_name_ar: Optional[str] = Field(None, description="First name in Arabic")
    last_name_ar: Optional[str] = Field(None, description="Last name in Arabic")
    blood_type: Optional[str] = Field(default="unknown", description="Blood type")
    national_id: Optional[str] = Field(None, max_length=50, description="National ID")
    passport_number: Optional[str] = Field(
        None, max_length=50, description="Passport number"
    )
    address: Optional[str] = Field(None, description="Address")
    city: Optional[str] = Field(None, max_length=100, description="City")
    region_id: Optional[str] = Field(None, description="Region ID")
    country_id: Optional[str] = Field(None, description="Country ID")
    emergency_contact_name: Optional[str] = Field(
        None, max_length=200, description="Emergency contact name"
    )
    emergency_contact_phone: Optional[str] = Field(
        None, max_length=20, description="Emergency contact phone"
    )
    emergency_contact_relation: Optional[str] = Field(
        None, max_length=50, description="Emergency contact relation"
    )
    allergies: Optional[List[str]] = Field(default=[], description="Allergies")
    chronic_conditions: Optional[List[str]] = Field(
        default=[], description="Chronic conditions"
    )
    current_medications: Optional[List[Dict[str, Any]]] = Field(
        default=[], description="Current medications"
    )
    insurance_provider: Optional[str] = Field(
        None, max_length=100, description="Insurance provider"
    )
    insurance_number: Optional[str] = Field(
        None, max_length=50, description="Insurance number"
    )
    primary_doctor_id: Optional[str] = Field(None, description="Primary doctor ID")
    is_active: bool = Field(default=True, description="Whether patient is active")
    notes: Optional[str] = Field(None, description="Notes")
    settings: Optional[Dict[str, Any]] = Field(
        default={}, description="Patient settings"
    )
    avatar_url: Optional[str] = Field(None, description="Avatar URL")


class PatientUpdateDTO(BaseModel):
    """DTO for updating patients."""

    user_id: Optional[str] = Field(None, description="User ID")
    hospital_id: Optional[str] = Field(None, description="Hospital ID")
    mrn: Optional[str] = Field(None, min_length=5, description="Medical Record Number")
    first_name: Optional[str] = Field(None, min_length=2, description="First name")
    last_name: Optional[str] = Field(None, min_length=2, description="Last name")
    first_name_ar: Optional[str] = Field(None, description="First name in Arabic")
    last_name_ar: Optional[str] = Field(None, description="Last name in Arabic")
    email: Optional[EmailStr] = Field(None, description="Email")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    gender: Optional[str] = Field(None, description="Gender")
    date_of_birth: Optional[date] = Field(None, description="Date of birth")
    blood_type: Optional[str] = Field(None, description="Blood type")
    national_id: Optional[str] = Field(None, max_length=50, description="National ID")
    passport_number: Optional[str] = Field(
        None, max_length=50, description="Passport number"
    )
    address: Optional[str] = Field(None, description="Address")
    city: Optional[str] = Field(None, max_length=100, description="City")
    region_id: Optional[str] = Field(None, description="Region ID")
    country_id: Optional[str] = Field(None, description="Country ID")
    emergency_contact_name: Optional[str] = Field(
        None, max_length=200, description="Emergency contact name"
    )
    emergency_contact_phone: Optional[str] = Field(
        None, max_length=20, description="Emergency contact phone"
    )
    emergency_contact_relation: Optional[str] = Field(
        None, max_length=50, description="Emergency contact relation"
    )
    allergies: Optional[List[str]] = Field(None, description="Allergies")
    chronic_conditions: Optional[List[str]] = Field(
        None, description="Chronic conditions"
    )
    current_medications: Optional[List[Dict[str, Any]]] = Field(
        None, description="Current medications"
    )
    insurance_provider: Optional[str] = Field(
        None, max_length=100, description="Insurance provider"
    )
    insurance_number: Optional[str] = Field(
        None, max_length=50, description="Insurance number"
    )
    primary_doctor_id: Optional[str] = Field(None, description="Primary doctor ID")
    is_active: Optional[bool] = Field(None, description="Whether patient is active")
    notes: Optional[str] = Field(None, description="Notes")
    settings: Optional[Dict[str, Any]] = Field(None, description="Patient settings")


class PatientResponseDTO(BaseModel):
    """Response DTO for patients."""

    id: str
    user_id: Optional[str]
    hospital_id: str
    mrn: str
    first_name: str
    last_name: str
    first_name_ar: Optional[str]
    last_name_ar: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    gender: Optional[str]
    date_of_birth: Optional[date]
    blood_type: str
    avatar_url: Optional[str] = None
    national_id: Optional[str]
    passport_number: Optional[str]
    address: Optional[str]
    city: Optional[str]
    region_id: Optional[str]
    country_id: Optional[str]
    emergency_contact_name: Optional[str]
    emergency_contact_phone: Optional[str]
    emergency_contact_relation: Optional[str]
    allergies: List[str]
    chronic_conditions: List[str]
    current_medications: List[Dict[str, Any]]
    insurance_provider: Optional[str]
    insurance_number: Optional[str]
    primary_doctor_id: Optional[str]
    is_active: bool
    notes: Optional[str]
    settings: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


# =====================================================
# MEDICAL CASES
# =====================================================


class MedicalCaseCreateDTO(BaseModel):
    """DTO for creating medical cases."""

    patient_id: str = Field(..., description="Patient ID")
    hospital_id: str = Field(..., description="Hospital ID")
    assigned_doctor_id: Optional[str] = Field(None, description="Assigned doctor ID")
    created_by_doctor_id: Optional[str] = Field(
        None, description="Created by doctor ID"
    )
    status: str = Field(default="open", description="Case status")
    priority: str = Field(default="normal", description="Case priority")
    chief_complaint: str = Field(..., min_length=10, description="Chief complaint")
    diagnosis: Optional[str] = Field(None, description="Diagnosis")
    diagnosis_icd10: Optional[str] = Field(
        None, max_length=20, description="ICD-10 diagnosis code"
    )
    treatment_plan: Optional[str] = Field(None, description="Treatment plan")
    notes: Optional[str] = Field(None, description="Additional notes")
    admission_date: Optional[datetime] = Field(None, description="Admission date")
    discharge_date: Optional[datetime] = Field(None, description="Discharge date")
    follow_up_date: Optional[date] = Field(None, description="Follow-up date")
    tags: Optional[List[str]] = Field(default=[], description="Tags")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Metadata")


class MedicalCaseUpdateDTO(BaseModel):
    """DTO for updating medical cases."""

    assigned_doctor_id: Optional[str] = Field(None, description="Assigned doctor ID")
    created_by_doctor_id: Optional[str] = Field(
        None, description="Created by doctor ID"
    )
    status: Optional[str] = Field(None, description="Case status")
    priority: Optional[str] = Field(None, description="Case priority")
    diagnosis: Optional[str] = Field(None, description="Diagnosis")
    diagnosis_icd10: Optional[str] = Field(
        None, max_length=20, description="ICD-10 diagnosis code"
    )
    treatment_plan: Optional[str] = Field(None, description="Treatment plan")
    notes: Optional[str] = Field(None, description="Additional notes")
    admission_date: Optional[datetime] = Field(None, description="Admission date")
    discharge_date: Optional[datetime] = Field(None, description="Discharge date")
    follow_up_date: Optional[date] = Field(None, description="Follow-up date")
    tags: Optional[List[str]] = Field(None, description="Tags")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata")
    is_archived: Optional[bool] = Field(None, description="Whether case is archived")
    archived_at: Optional[datetime] = Field(None, description="Archived at")
    archived_by: Optional[str] = Field(None, description="Archived by user ID")


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
    diagnosis_icd10: Optional[str]
    treatment_plan: Optional[str]
    notes: Optional[str]
    admission_date: Optional[datetime]
    discharge_date: Optional[datetime]
    follow_up_date: Optional[date]
    tags: List[str]
    metadata: Dict[str, Any]
    is_archived: bool
    archived_at: Optional[datetime]
    archived_by: Optional[str]
    created_at: datetime
    updated_at: datetime


# =====================================================
# MEDICAL FILES
# =====================================================


class MedicalFileCreateDTO(BaseModel):
    """DTO for creating medical files."""

    case_id: str = Field(..., description="Case ID")
    patient_id: str = Field(..., description="Patient ID")
    uploaded_by: str = Field(..., description="Uploaded by user ID")
    file_type: str = Field(..., description="File type")
    file_name: str = Field(..., description="File name")
    file_path: str = Field(..., description="File path")
    file_size: int = Field(..., gt=0, description="File size in bytes")
    mime_type: str = Field(..., description="MIME type")
    storage_bucket: str = Field(default="medical-files", description="Storage bucket")
    description: Optional[str] = Field(None, description="Description")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Metadata")


class MedicalFileUpdateDTO(BaseModel):
    """DTO for updating medical files."""

    file_type: Optional[str] = Field(None, description="File type")
    file_name: Optional[str] = Field(None, description="File name")
    file_path: Optional[str] = Field(None, description="File path")
    file_size: Optional[int] = Field(None, gt=0, description="File size in bytes")
    mime_type: Optional[str] = Field(None, description="MIME type")
    storage_bucket: Optional[str] = Field(None, description="Storage bucket")
    description: Optional[str] = Field(None, description="Description")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata")
    is_analyzed: Optional[bool] = Field(None, description="Whether file is analyzed")
    analyzed_at: Optional[datetime] = Field(None, description="Analyzed at")
    is_deleted: Optional[bool] = Field(None, description="Whether file is deleted")
    deleted_at: Optional[datetime] = Field(None, description="Deleted at")
    deleted_by: Optional[str] = Field(None, description="Deleted by user ID")


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
    storage_bucket: str
    description: Optional[str]
    metadata: Dict[str, Any]
    is_analyzed: bool
    analyzed_at: Optional[datetime]
    is_deleted: bool
    deleted_at: Optional[datetime]
    deleted_by: Optional[str]
    created_at: datetime
    updated_at: datetime


# =====================================================
# ECG ANALYSIS TABLES
# =====================================================


class ECGSignalCreateDTO(BaseModel):
    """DTO for creating ECG signals."""

    file_id: str = Field(..., description="File ID")
    patient_id: str = Field(..., description="Patient ID")
    case_id: Optional[str] = Field(None, description="Case ID")
    signal_data: Dict[str, Any] = Field(..., description="ECG signal data")
    sampling_rate: Optional[int] = Field(None, description="Sampling rate")
    duration_seconds: Optional[float] = Field(None, description="Duration in seconds")
    lead_count: int = Field(default=12, description="Number of leads")
    leads_available: Optional[List[str]] = Field(None, description="Available leads")
    recording_date: Optional[datetime] = Field(None, description="Recording date")
    device_info: Optional[Dict[str, Any]] = Field(
        None, description="Device information"
    )
    quality_score: Optional[float] = Field(
        None, ge=0.0, le=100.0, description="Quality score"
    )
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Metadata")


class ECGSignalResponseDTO(BaseModel):
    """Response DTO for ECG signals."""

    id: str
    file_id: str
    patient_id: str
    case_id: Optional[str]
    signal_data: Dict[str, Any]
    sampling_rate: Optional[int]
    duration_seconds: Optional[float]
    lead_count: int
    leads_available: Optional[List[str]]
    recording_date: Optional[datetime]
    device_info: Optional[Dict[str, Any]]
    quality_score: Optional[float]
    metadata: Dict[str, Any]
    created_at: datetime


class ECGResultCreateDTO(BaseModel):
    """DTO for creating ECG results."""

    signal_id: str = Field(..., description="Signal ID")
    patient_id: str = Field(..., description="Patient ID")
    case_id: Optional[str] = Field(None, description="Case ID")
    analyzed_by_model: str = Field(..., description="Analyzed by model")
    model_version: Optional[str] = Field(None, description="Model version")
    analysis_status: str = Field(default="pending", description="Analysis status")

    # Analysis Results
    heart_rate: Optional[int] = Field(None, description="Heart rate")
    heart_rate_variability: Optional[float] = Field(
        None, description="Heart rate variability"
    )
    rhythm_classification: Optional[str] = Field(
        None, description="Rhythm classification"
    )
    rhythm_confidence: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Rhythm confidence"
    )

    # Detected Conditions
    detected_conditions: Optional[List[Dict[str, Any]]] = Field(
        default=[], description="Detected conditions"
    )

    # Intervals (in milliseconds)
    pr_interval: Optional[int] = Field(None, description="PR interval")
    qrs_duration: Optional[int] = Field(None, description="QRS duration")
    qt_interval: Optional[int] = Field(None, description="QT interval")
    qtc_interval: Optional[int] = Field(None, description="QTc interval")

    # AI Interpretation
    ai_interpretation: Optional[str] = Field(None, description="AI interpretation")
    ai_recommendations: Optional[List[str]] = Field(
        default=[], description="AI recommendations"
    )
    risk_score: Optional[float] = Field(
        None, ge=0.0, le=100.0, description="Risk score"
    )

    # Review
    is_reviewed: bool = Field(default=False, description="Whether result is reviewed")
    reviewed_by_doctor_id: Optional[str] = Field(
        None, description="Reviewed by doctor ID"
    )
    reviewed_at: Optional[datetime] = Field(None, description="Reviewed at")
    doctor_notes: Optional[str] = Field(None, description="Doctor notes")
    doctor_agrees_with_ai: Optional[bool] = Field(
        None, description="Doctor agrees with AI"
    )

    # Metadata
    processing_time_ms: Optional[int] = Field(
        None, description="Processing time in milliseconds"
    )
    raw_output: Optional[Dict[str, Any]] = Field(None, description="Raw output")
    error_message: Optional[str] = Field(None, description="Error message")


class ECGResultUpdateDTO(BaseModel):
    """DTO for updating ECG results."""

    analyzed_by_model: Optional[str] = Field(None, description="Analyzed by model")
    model_version: Optional[str] = Field(None, description="Model version")
    analysis_status: Optional[str] = Field(None, description="Analysis status")

    heart_rate: Optional[int] = Field(None, description="Heart rate")
    heart_rate_variability: Optional[float] = Field(
        None, description="Heart rate variability"
    )
    rhythm_classification: Optional[str] = Field(
        None, description="Rhythm classification"
    )
    rhythm_confidence: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Rhythm confidence"
    )

    detected_conditions: Optional[List[Dict[str, Any]]] = Field(
        None, description="Detected conditions"
    )

    pr_interval: Optional[int] = Field(None, description="PR interval")
    qrs_duration: Optional[int] = Field(None, description="QRS duration")
    qt_interval: Optional[int] = Field(None, description="QT interval")
    qtc_interval: Optional[int] = Field(None, description="QTc interval")

    ai_interpretation: Optional[str] = Field(None, description="AI interpretation")
    ai_recommendations: Optional[List[str]] = Field(
        None, description="AI recommendations"
    )
    risk_score: Optional[float] = Field(
        None, ge=0.0, le=100.0, description="Risk score"
    )

    is_reviewed: Optional[bool] = Field(None, description="Whether result is reviewed")
    reviewed_by_doctor_id: Optional[str] = Field(
        None, description="Reviewed by doctor ID"
    )
    reviewed_at: Optional[datetime] = Field(None, description="Reviewed at")
    doctor_notes: Optional[str] = Field(None, description="Doctor notes")
    doctor_agrees_with_ai: Optional[bool] = Field(
        None, description="Doctor agrees with AI"
    )

    processing_time_ms: Optional[int] = Field(
        None, description="Processing time in milliseconds"
    )
    raw_output: Optional[Dict[str, Any]] = Field(None, description="Raw output")
    error_message: Optional[str] = Field(None, description="Error message")


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

    detected_conditions: List[Dict[str, Any]]
    pr_interval: Optional[int]
    qrs_duration: Optional[int]
    qt_interval: Optional[int]
    qtc_interval: Optional[int]

    ai_interpretation: Optional[str]
    ai_recommendations: List[str]
    risk_score: Optional[float]

    is_reviewed: bool
    reviewed_by_doctor_id: Optional[str]
    reviewed_at: Optional[datetime]
    doctor_notes: Optional[str]
    doctor_agrees_with_ai: Optional[bool]

    processing_time_ms: Optional[int]
    raw_output: Optional[Dict[str, Any]]
    error_message: Optional[str]

    created_at: datetime
    updated_at: datetime


# =====================================================
# MRI ANALYSIS TABLES
# =====================================================


class MRIScanCreateDTO(BaseModel):
    """DTO for creating MRI scans."""

    file_id: str = Field(..., description="File ID")
    patient_id: str = Field(..., description="Patient ID")
    case_id: Optional[str] = Field(None, description="Case ID")
    scan_type: Optional[str] = Field(None, max_length=50, description="Scan type")
    sequence_type: Optional[str] = Field(
        None, max_length=50, description="Sequence type"
    )
    body_part: Optional[str] = Field(None, max_length=100, description="Body part")
    slice_count: Optional[int] = Field(None, description="Slice count")
    slice_thickness_mm: Optional[float] = Field(
        None, description="Slice thickness in mm"
    )
    field_strength: Optional[float] = Field(None, description="Field strength in Tesla")
    scan_date: Optional[datetime] = Field(None, description="Scan date")
    device_info: Optional[Dict[str, Any]] = Field(
        None, description="Device information"
    )
    dicom_metadata: Optional[Dict[str, Any]] = Field(None, description="DICOM metadata")


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


class MRISegmentationResultCreateDTO(BaseModel):
    """DTO for creating MRI segmentation results."""

    scan_id: str = Field(..., description="Scan ID")
    patient_id: str = Field(..., description="Patient ID")
    case_id: Optional[str] = Field(None, description="Case ID")
    analyzed_by_model: str = Field(..., description="Analyzed by model")
    model_version: Optional[str] = Field(None, description="Model version")
    analysis_status: str = Field(default="pending", description="Analysis status")

    # Segmentation Results
    segmentation_mask_path: Optional[str] = Field(
        None, description="Segmentation mask path"
    )
    segmented_regions: Optional[List[Dict[str, Any]]] = Field(
        default=[], description="Segmented regions"
    )

    # Findings
    tumor_detected: Optional[bool] = Field(None, description="Whether tumor was detected")
    confidence_score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Overall confidence score"
    )
    detected_abnormalities: Optional[List[Dict[str, Any]]] = Field(
        default=[], description="Detected abnormalities"
    )

    # Measurements
    measurements: Optional[Dict[str, Any]] = Field(
        default={}, description="Measurements"
    )

    # AI Interpretation
    ai_interpretation: Optional[str] = Field(None, description="AI interpretation")
    ai_recommendations: Optional[List[str]] = Field(
        default=[], description="AI recommendations"
    )
    severity_score: Optional[float] = Field(
        None, ge=0.0, le=100.0, description="Severity score"
    )

    # Review
    is_reviewed: bool = Field(default=False, description="Whether result is reviewed")
    reviewed_by_doctor_id: Optional[str] = Field(
        None, description="Reviewed by doctor ID"
    )
    reviewed_at: Optional[datetime] = Field(None, description="Reviewed at")
    doctor_notes: Optional[str] = Field(None, description="Doctor notes")
    doctor_agrees_with_ai: Optional[bool] = Field(
        None, description="Doctor agrees with AI"
    )

    # Metadata
    processing_time_ms: Optional[int] = Field(
        None, description="Processing time in milliseconds"
    )
    raw_output: Optional[Dict[str, Any]] = Field(None, description="Raw output")
    error_message: Optional[str] = Field(None, description="Error message")


class MRISegmentationResultUpdateDTO(BaseModel):
    """DTO for updating MRI segmentation results."""

    analyzed_by_model: Optional[str] = Field(None, description="Analyzed by model")
    model_version: Optional[str] = Field(None, description="Model version")
    analysis_status: Optional[str] = Field(None, description="Analysis status")

    segmentation_mask_path: Optional[str] = Field(
        None, description="Segmentation mask path"
    )
    segmented_regions: Optional[List[Dict[str, Any]]] = Field(
        None, description="Segmented regions"
    )

    tumor_detected: Optional[bool] = Field(None, description="Whether tumor was detected")
    confidence_score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Overall confidence score"
    )
    detected_abnormalities: Optional[List[Dict[str, Any]]] = Field(
        None, description="Detected abnormalities"
    )

    measurements: Optional[Dict[str, Any]] = Field(None, description="Measurements")

    ai_interpretation: Optional[str] = Field(None, description="AI interpretation")
    ai_recommendations: Optional[List[str]] = Field(
        None, description="AI recommendations"
    )
    severity_score: Optional[float] = Field(
        None, ge=0.0, le=100.0, description="Severity score"
    )

    is_reviewed: Optional[bool] = Field(None, description="Whether result is reviewed")
    reviewed_by_doctor_id: Optional[str] = Field(
        None, description="Reviewed by doctor ID"
    )
    reviewed_at: Optional[datetime] = Field(None, description="Reviewed at")
    doctor_notes: Optional[str] = Field(None, description="Doctor notes")
    doctor_agrees_with_ai: Optional[bool] = Field(
        None, description="Doctor agrees with AI"
    )

    processing_time_ms: Optional[int] = Field(
        None, description="Processing time in milliseconds"
    )
    raw_output: Optional[Dict[str, Any]] = Field(None, description="Raw output")
    error_message: Optional[str] = Field(None, description="Error message")


class MRISegmentationResultResponseDTO(BaseModel):
    """Response DTO for MRI segmentation results."""

    id: str
    scan_id: str
    patient_id: str
    case_id: Optional[str]
    analyzed_by_model: str
    model_version: Optional[str]
    analysis_status: str

    segmentation_mask_path: Optional[str]
    segmented_regions: List[Dict[str, Any]]
    tumor_detected: Optional[bool]
    confidence_score: Optional[float]
    detected_abnormalities: List[Dict[str, Any]]
    measurements: Dict[str, Any]

    ai_interpretation: Optional[str]
    ai_recommendations: List[str]
    severity_score: Optional[float]

    is_reviewed: bool
    reviewed_by_doctor_id: Optional[str]
    reviewed_at: Optional[datetime]
    doctor_notes: Optional[str]
    doctor_agrees_with_ai: Optional[bool]

    processing_time_ms: Optional[int]
    raw_output: Optional[Dict[str, Any]]
    error_message: Optional[str]

    created_at: datetime
    updated_at: datetime


# =====================================================
# GENERATED REPORTS
# =====================================================


class GeneratedReportCreateDTO(BaseModel):
    """DTO for creating generated reports."""

    patient_id: str = Field(..., description="Patient ID")
    case_id: Optional[str] = Field(None, description="Case ID")
    doctor_id: Optional[str] = Field(None, description="Doctor ID")
    report_type: str = Field(..., description="Report type")

    # Source Analysis
    ecg_result_id: Optional[str] = Field(None, description="ECG result ID")
    mri_result_id: Optional[str] = Field(None, description="MRI result ID")

    # Report Content
    title: str = Field(..., min_length=5, description="Report title")
    summary: Optional[str] = Field(None, description="Report summary")
    content: Dict[str, Any] = Field(..., description="Report content")

    # Generation Info
    generated_by_model: Optional[str] = Field(None, description="Generated by model")
    model_version: Optional[str] = Field(None, description="Model version")
    template_used: Optional[str] = Field(None, description="Template used")

    # Approval Workflow
    status: str = Field(default="draft", description="Report status")
    approved_by_doctor_id: Optional[str] = Field(
        None, description="Approved by doctor ID"
    )
    approved_at: Optional[datetime] = Field(None, description="Approved at")
    approval_notes: Optional[str] = Field(None, description="Approval notes")

    # Digital Signature
    digital_signature: Optional[str] = Field(None, description="Digital signature")
    signature_timestamp: Optional[datetime] = Field(
        None, description="Signature timestamp"
    )
    signed_by_doctor_id: Optional[str] = Field(None, description="Signed by doctor ID")

    # PDF Storage
    pdf_path: Optional[str] = Field(None, description="PDF path")
    pdf_generated_at: Optional[datetime] = Field(None, description="PDF generated at")

    # Metadata
    is_final: bool = Field(default=False, description="Whether report is final")
    version: int = Field(default=1, description="Report version")
    previous_version_id: Optional[str] = Field(None, description="Previous version ID")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Metadata")


class GeneratedReportUpdateDTO(BaseModel):
    """DTO for updating generated reports."""

    doctor_id: Optional[str] = Field(None, description="Doctor ID")
    report_type: Optional[str] = Field(None, description="Report type")

    ecg_result_id: Optional[str] = Field(None, description="ECG result ID")
    mri_result_id: Optional[str] = Field(None, description="MRI result ID")

    title: Optional[str] = Field(None, min_length=5, description="Report title")
    summary: Optional[str] = Field(None, description="Report summary")
    content: Optional[Dict[str, Any]] = Field(None, description="Report content")

    generated_by_model: Optional[str] = Field(None, description="Generated by model")
    model_version: Optional[str] = Field(None, description="Model version")
    template_used: Optional[str] = Field(None, description="Template used")

    status: Optional[str] = Field(None, description="Report status")
    approved_by_doctor_id: Optional[str] = Field(
        None, description="Approved by doctor ID"
    )
    approved_at: Optional[datetime] = Field(None, description="Approved at")
    approval_notes: Optional[str] = Field(None, description="Approval notes")

    digital_signature: Optional[str] = Field(None, description="Digital signature")
    signature_timestamp: Optional[datetime] = Field(
        None, description="Signature timestamp"
    )
    signed_by_doctor_id: Optional[str] = Field(None, description="Signed by doctor ID")

    pdf_path: Optional[str] = Field(None, description="PDF path")
    pdf_generated_at: Optional[datetime] = Field(None, description="PDF generated at")

    is_final: Optional[bool] = Field(None, description="Whether report is final")
    version: Optional[int] = Field(None, description="Report version")
    previous_version_id: Optional[str] = Field(None, description="Previous version ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata")


class GeneratedReportResponseDTO(BaseModel):
    """Response DTO for generated reports."""

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
    metadata: Dict[str, Any]

    created_at: datetime
    updated_at: datetime


class ReportApproveDTO(BaseModel):
    """DTO for approving/finalizing reports."""

    notes: Optional[str] = Field(None, description="Approval notes or feedback")


# =====================================================
# GENERIC PROFILE DTOS
# =====================================================


class UserProfileUpdateDTO(BaseModel):
    """Generic DTO for updating current user's profile."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    first_name_ar: Optional[str] = None
    last_name_ar: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    avatar_url: Optional[str] = None
    country_id: Optional[str] = None
    region_id: Optional[str] = None
    hospital_id: Optional[str] = None

    # Patient Specific (Optional for others)
    mrn: Optional[str] = None
    blood_type: Optional[str] = None
    national_id: Optional[str] = None
    passport_number: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_number: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None
    allergies: Optional[List[str]] = None
    chronic_conditions: Optional[List[str]] = None
    current_medications: Optional[List[Dict[str, Any]]] = None
    notes: Optional[str] = None

    # Doctor/Admin Specific (Optional for others)
    employee_id: Optional[str] = None
    license_number: Optional[str] = None
    specialty: Optional[str] = None
    department: Optional[str] = None

    @field_validator("date_of_birth", mode="before")
    @classmethod
    def coerce_empty_date(cls, v):
        """Convert empty strings to None so Pydantic doesn't reject them."""
        if isinstance(v, str) and not v.strip():
            return None
        return v


class UserProfileResponseDTO(BaseModel):
    """Generic DTO for current user's profile response."""

    id: str
    user_id: str
    first_name: str
    last_name: str
    first_name_ar: Optional[str] = None
    last_name_ar: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    user_role: Optional[str] = None
    avatar_url: Optional[str] = None
    hospital_id: Optional[str] = None
    country_id: Optional[str] = None
    region_id: Optional[str] = None
    created_at: datetime

    # Additional fields are allowed for role-specific data
    model_config = {"extra": "allow"}
