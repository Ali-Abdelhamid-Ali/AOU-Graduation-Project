"""Authentication DTOs for request validation."""

import re
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from typing import Optional
from enum import Enum


class UserRole(str, Enum):
    """Allowed roles for signup."""

    PATIENT = "patient"
    DOCTOR = "doctor"
    NURSE = "nurse"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class SignUpDTO(BaseModel):
    """DTO for user registration."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    first_name: str = Field(..., min_length=2, description="User first name")
    last_name: str = Field(..., min_length=2, description="User last name")
    role: UserRole = Field(..., description="User role")
    hospital_id: Optional[str] = Field(
        None, description="Hospital ID for healthcare workers (must be a valid UUID)"
    )
    phone: Optional[str] = Field(None, max_length=20, description="User phone number")
    employee_id: Optional[str] = Field(None, max_length=50, description="Employee ID")
    department: Optional[str] = Field(None, description="Department")
    country_id: Optional[str] = Field(None, description="Country ID")
    region_id: Optional[str] = Field(None, description="Region ID")

    @field_validator(
        "phone", "employee_id", "department", "country_id", "region_id", mode="before"
    )
    @classmethod
    def normalize_optional_strings(cls, v):
        """Convert empty strings to None and trim whitespace."""
        if v is None:
            return None
        if isinstance(v, str):
            normalized = v.strip()
            return normalized or None
        return v

    @field_validator("hospital_id", mode="before")
    @classmethod
    def validate_hospital_id(cls, v):
        """Handle empty strings and validate UUID format without storing as UUID object."""
        if v is None:
            return None
        if isinstance(v, str):
            v = v.strip()
        if not v:
            return None

        # Validate UUID format
        import uuid

        try:
            uuid.UUID(str(v))
            return str(v)
        except ValueError:
            raise ValueError("Input should be a valid UUID string")

    @model_validator(mode="after")
    def validate_role_requirements(self):
        """Role-based required fields for signup."""
        if self.role in {UserRole.ADMIN, UserRole.SUPER_ADMIN}:
            employee_id = self.employee_id
            department = self.department
            if not employee_id:
                raise ValueError("employee_id is required for admin and super_admin")
            if not department:
                raise ValueError("department is required for admin and super_admin")

        if self.role in {UserRole.DOCTOR, UserRole.NURSE} and not self.employee_id:
            raise ValueError("employee_id is required for doctor and nurse")

        return self

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        """Enforce a minimum password complexity baseline."""
        password = value or ""
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", password):
            raise ValueError("Password must include at least one uppercase letter")
        if not re.search(r"[a-z]", password):
            raise ValueError("Password must include at least one lowercase letter")
        if not re.search(r"\d", password):
            raise ValueError("Password must include at least one number")
        if not re.search(r"[^\w\s]", password):
            raise ValueError("Password must include at least one special character")
        return password


class SignInDTO(BaseModel):
    """DTO for user login."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class PasswordResetRequestDTO(BaseModel):
    """DTO for password reset request."""

    email: EmailStr = Field(..., description="User email address")
    redirect_to: Optional[str] = Field(
        None, description="Redirect URL after password reset"
    )

    @field_validator("redirect_to")
    @classmethod
    def validate_redirect_url(cls, value: Optional[str]) -> Optional[str]:
        if value in (None, ""):
            return None
        from src.validators.url_validator import validate_safe_redirect_url

        if not validate_safe_redirect_url(value):
            raise ValueError("Invalid redirect URL")
        return value


class PasswordUpdateDTO(BaseModel):
    """DTO for password update."""

    access_token: str = Field(..., description="Access token")
    new_password: str = Field(..., min_length=8, description="New password")
    logout_all: Optional[bool] = Field(False, description="Logout all sessions")

    @field_validator("new_password")
    @classmethod
    def validate_new_password_strength(cls, value: str) -> str:
        return SignUpDTO.validate_password_strength(value)


class ForgotPasswordDTO(BaseModel):
    """DTO for forgot password request."""

    email: EmailStr = Field(..., description="User email address")


class ResetPasswordDTO(BaseModel):
    """DTO for password reset."""

    token: str = Field(..., description="Reset token")
    password: str = Field(..., min_length=8, description="New password")


class VerifyEmailDTO(BaseModel):
    """DTO for email verification."""

    token: str = Field(..., description="Verification token")


class SignOutDTO(BaseModel):
    """DTO for user logout."""

    scope: Optional[str] = Field(None, description="Logout scope (single, all)")
