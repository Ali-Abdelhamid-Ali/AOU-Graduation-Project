"""Auth Service - Business Logic for Authentication."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from src.observability.audit import AuditAction, log_audit
from src.observability.logger import get_logger
from src.repositories.auth_repository import AuthRepository
from src.services.infrastructure.memory_cache import global_cache
from src.validators.auth_dto import SignInDTO, SignUpDTO

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

    async def _build_user_payload(self, auth_user: Any) -> Dict[str, Any]:
        user_metadata = auth_user.user_metadata or {}
        metadata_role = user_metadata.get("role")
        role = await self.auth_repo.resolve_user_role(str(auth_user.id), metadata_role)
        table = ROLE_TABLE_MAP.get(role, "patients")
        profile = await self.auth_repo.get_profile_by_user_id(table, auth_user.id)
        profile = dict(profile or {})

        avatar_url = user_metadata.get("avatar_url") or user_metadata.get("photo_url")
        if avatar_url and not profile.get("avatar_url"):
            profile["avatar_url"] = avatar_url
        if avatar_url and not profile.get("photo_url"):
            profile["photo_url"] = avatar_url

        # Propagate password-change flag from Supabase metadata to the profile
        # so the frontend ProtectedRoute can intercept and force a reset.
        if user_metadata.get("password_change_required") or user_metadata.get("must_reset_password"):
            profile["must_reset_password"] = True

        return {
            "id": auth_user.id,
            "email": auth_user.email,
            "role": role,
            "profile": profile or {},
        }

    @staticmethod
    def _build_session_payload(session: Any) -> Dict[str, Any]:
        if not session or not getattr(session, "access_token", None):
            raise Exception("Authentication session is missing")

        return {
            "access_token": session.access_token,
            "refresh_token": getattr(session, "refresh_token", None),
            "expires_at": getattr(session, "expires_at", None),
        }

    async def _resolve_profile_id(
        self,
        table: str,
        user_id: str,
        profile_response: Any | None = None,
    ) -> Optional[str]:
        """Resolve the profile row id created for a given auth user."""
        profile_data = getattr(profile_response, "data", None) if profile_response is not None else None
        if profile_data:
            profile_id = profile_data[0].get("id")
            if profile_id:
                return str(profile_id)

        profile = await self.auth_repo.get_profile_by_user_id(table, user_id)
        if profile and profile.get("id"):
            return str(profile["id"])
        return None

    def _generate_mrn(self, hospital_id: Optional[str] = None) -> str:
        """Generates a unique Medical Record Number."""
        # UUID-derived suffix minimizes collision risk without relying on DB-side sequences.
        hospital_code = "GEN"  # Fallback
        year = datetime.now().strftime("%y")
        unique_suffix = uuid4().hex[:8].upper()
        return f"{hospital_code}{year}{unique_suffix}"

    async def sign_up(self, data: SignUpDTO) -> Dict[str, Any]:
        """
        Orchestrates User Registration for public signup.
        """
        user_id = None
        try:
            role = data.role.value
            if role != "patient":
                raise ValueError(
                    "Public signup currently supports patient accounts only. Staff accounts must be created by an administrator."
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
            profile_response = await self.auth_repo.create_profile(table, profile_data)
            logger.info(f"Profile created in {table} for {user_id}")

            # 4. Handle Doctor Specialty Linking
            if role == "doctor" and profile_data.get("specialty"):
                try:
                    doctor_profile_id = await self._resolve_profile_id(
                        table, user_id, profile_response
                    )
                    if not doctor_profile_id:
                        raise ValueError(
                            "Doctor profile was created but its primary key could not be resolved"
                        )
                    await self.auth_repo.link_doctor_specialty(
                        doctor_profile_id, profile_data["specialty"]
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
            try:
                user_payload = await self._build_user_payload(user)
            except Exception as payload_error:
                logger.warning(
                    f"Login succeeded but profile enrichment failed for {data.email}: {payload_error}"
                )
                user_metadata = getattr(user, "user_metadata", None) or {}
                fallback_role = str(user_metadata.get("role") or "patient").strip().lower() or "patient"
                user_payload = {
                    "id": user.id,
                    "email": user.email,
                    "role": fallback_role,
                    "profile": {},
                }

            try:
                log_audit(AuditAction.LOGIN, user_id=user.id, email=data.email)
            except Exception as audit_error:
                logger.warning(
                    f"Login audit logging failed for {data.email}: {audit_error}"
                )

            return {
                "user": user_payload,
                "session": self._build_session_payload(auth_response.session),
            }
        except Exception as e:
            logger.error(f"Signin failed for {data.email}: {str(e)}")
            try:
                await self.record_failed_attempt(data.email)
            except Exception as attempt_error:
                logger.warning(
                    f"Failed attempt tracking failed for {data.email}: {attempt_error}"
                )
            log_audit(AuditAction.LOGIN, email=data.email, success=False)
            raise e

    async def refresh_session(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh an authenticated session."""
        try:
            auth_response = await self.auth_repo.refresh_session(refresh_token)
            auth_user = getattr(auth_response, "user", None)

            return {
                "user": await self._build_user_payload(auth_user) if auth_user else None,
                "session": self._build_session_payload(auth_response.session),
            }
        except Exception as e:
            logger.error(f"Session refresh failed: {str(e)}")
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
        current_password: Optional[str] = None,
        logout_all: bool = False,
    ):
        """Update password."""
        try:
            # Step 1: Verify current password if provided
            if current_password:
                logger.info(f"Verifying current password for user {user_id}")
                try:
                    current_auth = await self.auth_repo.sign_in(email, current_password)
                    if not getattr(current_auth, "user", None):
                        raise PermissionError("Current password is incorrect")
                    logger.info(f"Current password verified for user {user_id}")
                except PermissionError:
                    raise
                except Exception as e:
                    error_msg = str(e)
                    if (
                        "Invalid login credentials" in error_msg
                        or "Invalid credentials" in error_msg
                    ):
                        raise PermissionError("Current password is incorrect")
                    raise

            # Step 2: Check that new password is different from old one
            # This is a best-effort check — if it fails for any reason
            # other than proving the password is the same, we proceed.
            try:
                check_auth = await self.auth_repo.sign_in(email, new_password)
                if getattr(check_auth, "user", None):
                    raise Exception(
                        "Security Alert: Your new password cannot be the same as your old one."
                    )
            except Exception as e:
                if "Your new password cannot be the same" in str(e):
                    raise
                # Any other error means the new password is different or
                # the check couldn't be performed — safe to proceed.
                logger.info(
                    f"Same-password check passed for user {user_id} "
                    f"(sign_in with new password failed as expected)"
                )

            # Step 3: Actually update the password via Admin API
            logger.info(f"Updating password via Admin API for user {user_id}")
            await self.auth_repo.update_password(user_id, new_password)
            logger.info(f"Password updated successfully for user {user_id}")

            # Clear the forced-reset flag from Supabase metadata so the user
            # is not redirected to the reset page again on next login.
            try:
                await self.auth_repo.update_user_metadata(
                    user_id,
                    {"password_change_required": False, "must_reset_password": False},
                )
            except Exception as meta_err:
                logger.warning(f"Could not clear password_change_required flag for {user_id}: {meta_err}")

            log_audit(AuditAction.PASSWORD_CHANGE, user_id=user_id)

            # Step 4: Optionally revoke other sessions
            if logout_all:
                logger.info(f"Revoking all sessions for user {user_id}")
                await self.auth_repo.sign_out(user_id, scope="global", jwt=access_token)

            return {"success": True, "message": "Password updated successfully"}
        except Exception as e:
            logger.error(f"Password update failed: {type(e).__name__}: {str(e)}")
            raise e

    async def get_me(self, user_id: str, email: str, role: str, avatar_url: str | None = None):
        """Fetch current user profile."""
        try:
            authoritative_role = await self.auth_repo.resolve_user_role(user_id, role)
            table = ROLE_TABLE_MAP.get(authoritative_role, "patients")
            profile = await self.auth_repo.get_profile_by_user_id(table, user_id)
            profile = dict(profile or {})

            if avatar_url and not profile.get("avatar_url"):
                profile["avatar_url"] = avatar_url
            if avatar_url and not profile.get("photo_url"):
                profile["photo_url"] = avatar_url

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

