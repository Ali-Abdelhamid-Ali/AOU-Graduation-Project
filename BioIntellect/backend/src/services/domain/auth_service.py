"""Auth Service - Business Logic for Authentication."""

from typing import Dict, Any, Optional
import random
from datetime import datetime

from src.repositories.auth_repository import AuthRepository
from src.validators.auth_dto import SignUpDTO, SignInDTO
from src.observability.logger import get_logger
from src.observability.audit import log_audit, AuditAction
from src.services.infrastructure.memory_cache import global_cache

logger = get_logger("service.auth")

ROLE_TABLE_MAP = {
    "patient": "patients",
    "doctor": "doctors",
    "nurse": "nurses",
    "admin": "administrators",
    "super_admin": "administrators",
}


class AuthService:
    def __init__(self, auth_repo: AuthRepository):
        self.auth_repo = auth_repo

    def _generate_mrn(self, hospital_id: Optional[str] = None) -> str:
        """Generates a unique Medical Record Number."""
        # Simplified: In production, this would query a sequence or hospital-specific logic
        hospital_code = "GEN"  # Fallback
        year = datetime.now().strftime("%y")
        seq = str(random.randint(1, 999999)).zfill(6)
        return f"{hospital_code}{year}{seq}"

    async def sign_up(self, data: SignUpDTO) -> Dict[str, Any]:
        """
        Orchestrates User Registration for public signup.
        """
        user_id = None
        try:
            role = data.role.value
            if role in {"admin", "super_admin"}:
                raise ValueError(
                    "Public signup does not allow administrative roles"
                )
            table = ROLE_TABLE_MAP.get(role)
            if not table:
                raise ValueError(f"Invalid role: {role}")

            # 1. Prepare Auth Metadata
            metadata = {
                "role": role,
                "first_name": data.first_name,
                "last_name": data.last_name,
                "full_name": f"{data.first_name} {data.last_name}",
                "hospital_id": str(data.hospital_id) if data.hospital_id else None,
            }

            # 2. Step 1: Create Auth User
            user_id = await self.auth_repo.create_auth_user(
                data.email, data.password, metadata
            )
            logger.info(f"Auth user created: {user_id}")

            # 3. Step 2: Create Profile
            profile_data = {
                "user_id": user_id,
                "first_name": data.first_name,
                "last_name": data.last_name,
                "email": data.email,
                "phone": data.phone,
                "hospital_id": str(data.hospital_id) if data.hospital_id else None,
                "country_id": str(data.country_id) if data.country_id else None,
                "region_id": str(data.region_id) if data.region_id else None,
                "is_active": True,
            }

            # Role-Specific Logic
            if role == "patient":
                profile_data["mrn"] = self._generate_mrn(
                    str(data.hospital_id) if data.hospital_id else None
                )
            elif role in ["admin", "super_admin"]:
                profile_data["role"] = role
                profile_data["department"] = data.department or "General"
                profile_data["employee_id"] = data.employee_id

            # Execute Profile Insertion
            await self.auth_repo.create_profile(table, profile_data)
            logger.info(f"Profile created in {table} for {user_id}")

            # 5. Success Logging
            log_audit(AuditAction.SIGNUP, user_id=user_id, email=data.email)

            return {
                "success": True,
                "user_id": user_id,
                "mrn": profile_data.get("mrn"),
                "message": "Registration completed successfully",
            }

        except Exception as e:
            logger.error(f"Registration failed for {data.email}: {str(e)}")
            if user_id:
                logger.warning(
                    f"Compensating: Deleting orphaned Auth account {user_id}"
                )
                await self.auth_repo.delete_auth_user(user_id)
            raise e

    async def admin_create_user(
        self, role: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Specialized creation for admins to create other users (Doctors, Admins, Patients).
        Ensures both Auth account and Profile are created.
        """
        user_id = None
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            raise ValueError("Email and password are required for user creation")

        try:
            # 1. Prepare Auth Metadata
            metadata = {
                "role": role,
                "first_name": data.get("first_name"),
                "last_name": data.get("last_name"),
                "full_name": f"{data.get('first_name')} {data.get('last_name')}",
                "hospital_id": str(data.get("hospital_id"))
                if data.get("hospital_id")
                else None,
            }

            # 2. Create Auth User
            user_id = await self.auth_repo.create_auth_user(email, password, metadata)
            logger.info(f"Auth user created by admin for {role}: {user_id}")

            # 3. Create Profile
            table = ROLE_TABLE_MAP.get(role)
            if not table:
                raise ValueError(f"Invalid role: {role}")

            # Base profile data
            profile_data = {
                "user_id": user_id,
                "first_name": data.get("first_name"),
                "last_name": data.get("last_name"),
                "email": email,
                "phone": data.get("phone"),
                "hospital_id": str(data.get("hospital_id"))
                if data.get("hospital_id")
                else None,
                "is_active": data.get("is_active", True),
                "avatar_url": data.get("avatar_url"),
            }

            # Link Geographic data if provided
            if data.get("country_id"):
                profile_data["country_id"] = str(data.get("country_id"))
            if data.get("region_id"):
                profile_data["region_id"] = str(data.get("region_id"))

            # Link Arabic names if provided
            if data.get("first_name_ar"):
                profile_data["first_name_ar"] = data.get("first_name_ar")
            if data.get("last_name_ar"):
                profile_data["last_name_ar"] = data.get("last_name_ar")

            # Role-Specific Logic
            if role == "patient":
                profile_data["mrn"] = self._generate_mrn(
                    profile_data.get("hospital_id")
                )
                profile_data["gender"] = data.get("gender")
                profile_data["date_of_birth"] = data.get("date_of_birth")
                profile_data["blood_type"] = data.get("blood_type", "unknown")
                profile_data["national_id"] = data.get("national_id")
                profile_data["passport_number"] = data.get("passport_number")
                profile_data["address"] = data.get("address")
                profile_data["city"] = data.get("city")
                profile_data["insurance_provider"] = data.get("insurance_provider")
                profile_data["insurance_number"] = data.get("insurance_number")
                profile_data["emergency_contact_name"] = data.get(
                    "emergency_contact_name"
                )
                profile_data["emergency_contact_phone"] = data.get(
                    "emergency_contact_phone"
                )
                profile_data["emergency_contact_relation"] = data.get(
                    "emergency_contact_relation"
                )
                profile_data["allergies"] = data.get("allergies", [])
                profile_data["chronic_conditions"] = data.get("chronic_conditions", [])
                profile_data["current_medications"] = data.get(
                    "current_medications", []
                )
                profile_data["notes"] = data.get("notes")
            elif role == "doctor":
                profile_data["license_number"] = data.get("license_number")
                profile_data["specialty"] = data.get("specialty")
                profile_data["employee_id"] = data.get("employee_id")
                profile_data["qualification"] = data.get("qualification")
                profile_data["years_of_experience"] = data.get("years_of_experience", 0)
                profile_data["bio"] = data.get("bio")
                profile_data["gender"] = data.get("gender")
                profile_data["date_of_birth"] = data.get("date_of_birth")
                profile_data["license_expiry"] = data.get("license_expiry")
            elif role in ["admin", "super_admin"]:
                profile_data["department"] = data.get("department", "General")
                profile_data["employee_id"] = data.get("employee_id")
                profile_data["role"] = role

            # Execute Profile Insertion
            await self.auth_repo.create_profile(table, profile_data)
            logger.info(f"Profile created in {table} for {user_id}")

            # 4. Handle Doctor Specialty Linking
            if role == "doctor" and profile_data.get("specialty"):
                try:
                    await self.auth_repo.link_doctor_specialty(
                        user_id, profile_data["specialty"]
                    )
                except Exception as e:
                    logger.warning(f"Failed to link doctor specialty: {str(e)}")

            log_audit(
                AuditAction.SIGNUP,
                user_id=user_id,
                email=email,
                details={"created_by_role": "admin", "target_role": role},
            )

            return {
                "success": True,
                "user_id": user_id,
                "mrn": profile_data.get("mrn"),
                "message": f"{role.capitalize()} created successfully",
            }

        except Exception as e:
            logger.error(f"Admin creation failed for {email}: {str(e)}")
            if user_id:
                logger.warning(
                    f"Compensating: Deleting orphaned Auth account {user_id}"
                )
                await self.auth_repo.delete_auth_user(user_id)
            raise e

    async def sign_in(self, data: SignInDTO) -> Dict[str, Any]:
        """Business logic for signing in."""
        try:
            auth_response = await self.auth_repo.sign_in(data.email, data.password)
            if not auth_response.user:
                raise Exception("Invalid credentials")

            user = auth_response.user
            metadata_role = (user.user_metadata or {}).get("role")
            role = await self.auth_repo.resolve_user_role(str(user.id), metadata_role)

            # Fetch profile
            table = ROLE_TABLE_MAP.get(role, "patients")
            profile = await self.auth_repo.get_profile_by_user_id(table, user.id)

            log_audit(AuditAction.LOGIN, user_id=user.id, email=data.email)

            return {
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "role": role,
                    "profile": profile or {},
                },
                "session": {
                    "access_token": auth_response.session.access_token,
                    "refresh_token": auth_response.session.refresh_token,
                    "expires_at": auth_response.session.expires_at,
                },
            }
        except Exception as e:
            logger.error(f"Signin failed for {data.email}: {str(e)}")
            await self.record_failed_attempt(data.email)
            log_audit(AuditAction.LOGIN, email=data.email, success=False)
            raise e

    async def check_login_attempts(self, email: str):
        """Enforce rate limiting."""
        key = f"login_fail:{email}"
        attempts_data = await global_cache.get(key)
        if not attempts_data:
            return
        count = attempts_data.get("count", 0)
        last_attempt_time = attempts_data.get("last_attempt", 0)
        if count < 3:
            return
        base_delay = 60
        lockout_duration = min(base_delay * (5 ** (count - 3)), 3600)
        elapsed = datetime.now().timestamp() - last_attempt_time
        remaining = lockout_duration - elapsed
        if remaining > 0:
            raise Exception(
                f"Too many failed attempts. Please try again in {int(remaining)} seconds."
            )

    async def record_failed_attempt(self, email: str):
        """Increment failure count."""
        key = f"login_fail:{email}"
        attempts_data = await global_cache.get(key) or {"count": 0, "last_attempt": 0}
        attempts_data["count"] += 1
        attempts_data["last_attempt"] = datetime.now().timestamp()
        await global_cache.set(key, attempts_data, ttl_seconds=3600)
        if attempts_data["count"] == 5:
            try:
                await self.auth_repo.reset_password(email)
            except Exception as e:
                logger.error(f"Failed to send security warning email: {e}")

    async def reset_failed_attempts(self, email: str):
        """Reset failure count."""
        key = f"login_fail:{email}"
        await global_cache.delete(key)

    async def reset_password(self, email: str, redirect_to: Optional[str] = None):
        """Send password reset email."""
        try:
            await self.auth_repo.reset_password(email, redirect_to)
            log_audit(AuditAction.PASSWORD_RESET_REQUEST, email=email)
            return {"success": True, "message": "Password reset email sent"}
        except Exception as e:
            logger.error(f"Password reset failed: {str(e)}")
            raise e

    async def get_user_identity_from_access_token(
        self, access_token: str
    ) -> Dict[str, str]:
        """Resolve user id/email from access token."""
        return await self.auth_repo.get_user_from_token(access_token)

    async def update_password(
        self,
        user_id: str,
        email: str,
        access_token: str,
        new_password: str,
        logout_all: bool = False,
    ):
        """Update password."""
        try:
            try:
                check_auth = await self.auth_repo.sign_in(email, new_password)
                if check_auth.user:
                    raise Exception(
                        "Security Alert: Your new password cannot be the same as your old one."
                    )
            except Exception as e:
                if "Your new password cannot be the same" in str(e):
                    raise e
                if "Invalid credentials" not in str(e):
                    raise e
            await self.auth_repo.update_password(user_id, new_password)
            log_audit(AuditAction.PASSWORD_CHANGE, user_id=user_id)
            if logout_all:
                await self.auth_repo.sign_out(user_id, scope="global", jwt=access_token)
            return {"success": True, "message": "Password updated successfully"}
        except Exception as e:
            logger.error(f"Password update failed: {str(e)}")
            raise e

    async def get_me(self, user_id: str, email: str, role: str):
        """Fetch current user profile."""
        try:
            authoritative_role = await self.auth_repo.resolve_user_role(user_id, role)
            table = ROLE_TABLE_MAP.get(authoritative_role, "patients")
            profile = await self.auth_repo.get_profile_by_user_id(table, user_id)
            return {
                "id": user_id,
                "email": email,
                "role": authoritative_role,
                "profile": profile or {},
            }
        except Exception as e:
            logger.error(f"GetMe failed: {str(e)}")
            raise e

    async def sign_out(
        self, user_id: str, scope: str = "local", jwt: Optional[str] = None
    ):
        """Perform sign out."""
        try:
            await self.auth_repo.sign_out(user_id, scope, jwt)
            log_audit(AuditAction.LOGOUT, user_id=user_id, details={"scope": scope})
            return {"success": True}
        except Exception as e:
            logger.error(f"Sign out failed: {str(e)}")
            raise e

