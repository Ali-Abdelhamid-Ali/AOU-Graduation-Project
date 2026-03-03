"""Auth Controller - API Handlers for Authentication."""

from fastapi import HTTPException, status
from typing import Optional
from src.services.domain.auth_service import AuthService
from src.validators.auth_dto import SignUpDTO, SignInDTO
from src.validators.response_dto import AuthResponse, SuccessResponse
from src.observability.logger import get_logger

logger = get_logger("controller.auth")


class AuthController:
    """
    Controller layer for Auth.
    Responsibility: Receive request, Validate, Call Service, Return Response.
    STRICT RULE: No business logic here.
    """

    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service

    async def sign_up(self, data: SignUpDTO):
        """Handle user registration with standardized error handling."""
        try:
            result = await self.auth_service.sign_up(data)
            return AuthResponse(
                success=True,
                message="Registration successful",
                user={"id": result["user_id"], "mrn": result.get("mrn")},
                session=None,
            )
        except HTTPException:
            # Re-raise HTTP exceptions as-is (validation, auth, etc.)
            raise
        except Exception as e:
            logger.error(f"Registration failed: {str(e)}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def sign_in(self, data: SignInDTO):
        """Handle user authentication with rate limiting and security checks."""
        # 1. Check Rate Limits (3 attempts, then backoff, 5 attempts email)
        await self.auth_service.check_login_attempts(data.email)

        try:
            # 2. Attempt Login
            result = await self.auth_service.sign_in(data)

            # 3. Reset Failures on Success
            await self.auth_service.reset_failed_attempts(data.email)

            return AuthResponse(
                success=True,
                user=result["user"],
                session=result["session"],
                message="Authentication successful",
            )
        except Exception as e:
            error_msg = str(e)
            if (
                "Invalid login credentials" in error_msg
                or "Invalid credentials" in error_msg
            ):
                # The service already recorded the failure
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication failed. Please check your credentials.",
                )
            elif "Email not confirmed" in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Please confirm your email before signing in",
                )
            elif "Too many failed attempts" in error_msg:
                # Re-raise the rate limit exception as 429
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=error_msg,
                )
            else:
                logger.error(f"Sign-in failed for {data.email}: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Authentication failed. Please try again.",
                )

    async def reset_password(self, email: str, redirect_to: Optional[str] = None):
        """Handle password reset request."""
        # Validate Redirect URL to prevent Open Redirects
        if redirect_to:
            from src.validators.url_validator import validate_safe_redirect_url

            if not validate_safe_redirect_url(redirect_to):
                logger.warning(f"Blocked unsafe redirect URL: {redirect_to}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid redirect URL",
                )

        try:
            result = await self.auth_service.reset_password(email, redirect_to)
            return SuccessResponse(
                success=True, message=result.get("message", "Password reset email sent")
            )
        except Exception as e:
            logger.error(f"Password reset failed for {email}: {str(e)}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def update_password(
        self,
        user_id: str,
        email: str,
        access_token: str,
        new_password: str,
        logout_all: bool = False,
    ):
        """Handle password update."""
        try:
            result = await self.auth_service.update_password(
                user_id, email, access_token, new_password, logout_all
            )
            return SuccessResponse(
                success=True,
                message=result.get("message", "Password updated successfully"),
            )
        except Exception as e:
            logger.error(f"Password update failed for user {user_id}: {str(e)}")

            error_msg = str(e)
            if "Your new password cannot be the same" in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg
                )

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def get_user_identity_from_access_token(self, access_token: str):
        """Resolve user id/email from access token."""
        try:
            return await self.auth_service.get_user_identity_from_access_token(
                access_token
            )
        except Exception as e:
            logger.error(f"Access token validation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed. Please try again.",
            )

    async def sign_out(self, user_id: str, scope: str, jwt: Optional[str] = None):
        """Handle user sign out."""
        try:
            _ = await self.auth_service.sign_out(user_id, scope, jwt)
            return SuccessResponse(success=True, message="Successfully signed out")
        except Exception as e:
            logger.error(f"Sign out failed for user {user_id}: {str(e)}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def get_me(self, user_id: str, email: str, role: str):
        """Get current user profile."""
        try:
            data = await self.auth_service.get_me(user_id, email, role)
            return SuccessResponse(
                success=True, data=data, message="User profile retrieved successfully"
            )
        except Exception as e:
            logger.error(f"GetMe failed for user {user_id}: {str(e)}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

