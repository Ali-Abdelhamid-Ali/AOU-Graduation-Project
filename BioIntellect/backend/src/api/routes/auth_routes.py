"""Auth Routes - Endpoint definitions."""

from fastapi import APIRouter, Depends, Request, Response
from src.api.controllers.auth_controller import AuthController
from src.services.domain.auth_service import AuthService
from src.repositories.auth_repository import AuthRepository
from src.services.domain.logging_service import LoggingService
from src.observability.logger import get_logger
from src.validators.auth_dto import (
    SignUpDTO,
    SignInDTO,
    PasswordResetRequestDTO,
    PasswordUpdateDTO,
    SignOutDTO,
)
from src.security.auth_middleware import get_current_user
from src.middleware.rate_limiter import limiter
from src.validators.response_dto import AuthResponse, SuccessResponse, ApiErrorResponse

router = APIRouter(prefix="/auth", tags=["auth"])
logger = get_logger("route.auth")


# Manual Dependency Injection (Container-like helper)
def get_auth_controller():
    repo = AuthRepository()
    service = AuthService(repo)
    return AuthController(service)


@router.post(
    "/signup",
    response_model=AuthResponse,
    responses={
        400: {"model": ApiErrorResponse},
        422: {"model": ApiErrorResponse},
        500: {"model": ApiErrorResponse},
    },
)
async def sign_up(
    data: SignUpDTO, controller: AuthController = Depends(get_auth_controller)
):
    return await controller.sign_up(data)


@router.post(
    "/signin",
    response_model=AuthResponse,
    responses={
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        429: {"model": ApiErrorResponse},
        500: {"model": ApiErrorResponse},
    },
)
@limiter.limit("5/minute")
async def sign_in(
    request: Request,
    response: Response,
    data: SignInDTO,
    controller: AuthController = Depends(get_auth_controller),
):
    result = await controller.sign_in(data)
    success = (
        getattr(result, "success", False)
        if not isinstance(result, dict)
        else result.get("success", False)
    )
    user_payload = (
        getattr(result, "user", None)
        if not isinstance(result, dict)
        else result.get("user")
    ) or {}

    if success and user_payload.get("id"):
        # Log successful login (optional - don't fail if logging fails)
        try:
            logging_service = LoggingService()
            await logging_service.log_user_login(
                user_id=user_payload["id"],
                ip_address=request.client.host,  # Would come from request headers
                user_agent=request.headers.get(
                    "user-agent"
                ),  # Would come from request headers
            )
        except Exception as e:
            # Log the error but don't fail the login
            logger.warning(f"Failed to log login action: {e}")
    return result


@router.post(
    "/reset-password",
    response_model=SuccessResponse,
    responses={
        400: {"model": ApiErrorResponse},
        429: {"model": ApiErrorResponse},
        500: {"model": ApiErrorResponse},
    },
)
@limiter.limit("3/minute")
async def reset_password(
    request: Request,
    response: Response,
    data: PasswordResetRequestDTO,
    controller: AuthController = Depends(get_auth_controller),
):
    return await controller.reset_password(data.email, data.redirect_to)


@router.post(
    "/update-password",
    response_model=SuccessResponse,
    responses={
        400: {"model": ApiErrorResponse},
        401: {"model": ApiErrorResponse},
        429: {"model": ApiErrorResponse},
        500: {"model": ApiErrorResponse},
    },
)
@limiter.limit("3/minute")
async def update_password(
    request: Request,
    response: Response,
    data: PasswordUpdateDTO,
    controller: AuthController = Depends(get_auth_controller),
):
    user_identity = await controller.get_user_identity_from_access_token(
        data.access_token
    )

    return await controller.update_password(
        user_identity["id"],
        user_identity["email"],
        data.access_token,
        data.new_password,
        data.logout_all if data.logout_all is not None else False,
    )


@router.get(
    "/me",
    response_model=SuccessResponse,
    responses={
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        500: {"model": ApiErrorResponse},
    },
)
async def get_me(
    user: dict = Depends(get_current_user),
    controller: AuthController = Depends(get_auth_controller),
):
    return await controller.get_me(user["id"], user["email"], user["role"])


@router.post(
    "/sign-out",
    response_model=SuccessResponse,
    responses={
        401: {"model": ApiErrorResponse},
        500: {"model": ApiErrorResponse},
    },
)
async def sign_out(
    data: SignOutDTO,
    user: dict = Depends(get_current_user),
    controller: AuthController = Depends(get_auth_controller),
):
    result = await controller.sign_out(
        user["id"], data.scope or "single", user["access_token"]
    )
    # Log logout action (optional - don't fail if logging fails)
    try:
        logging_service = LoggingService()
        await logging_service.log_user_logout(
            user_id=user["id"],
            ip_address=None,  # Would come from request headers
            user_agent=None,  # Would come from request headers
        )
    except Exception as e:
        # Log the error but don't fail the logout
        logger.warning(f"Failed to log logout action: {e}")
    return result

