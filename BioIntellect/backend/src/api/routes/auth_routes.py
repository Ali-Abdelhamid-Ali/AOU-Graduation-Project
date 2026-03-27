"""Auth Routes - Endpoint definitions."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from src.api.controllers.auth_controller import AuthController
from src.config.settings import settings
from src.middleware.rate_limiter import limiter
from src.observability.logger import get_logger
from src.repositories.auth_repository import AuthRepository
from src.security.auth_middleware import get_current_user
from src.services.domain.auth_service import AuthService
from src.services.domain.logging_service import LoggingService
from src.validators.auth_dto import (
    PasswordResetRequestDTO,
    PasswordUpdateDTO,
    SignInDTO,
    SignOutDTO,
    SignUpDTO,
)
from src.validators.response_dto import ApiErrorResponse, AuthResponse, SuccessResponse

router = APIRouter(prefix="/auth", tags=["auth"])
logger = get_logger("route.auth")

REFRESH_COOKIE_NAME = "biointellect_refresh_token"
REFRESH_COOKIE_MAX_AGE = 60 * 60 * 24 * 30


def _cookie_kwargs():
    return {
        "httponly": True,
        "secure": settings.environment == "production",
        "samesite": "lax",
        "path": "/",
    }


def _set_refresh_cookie(response: Response, refresh_token: str):
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        max_age=REFRESH_COOKIE_MAX_AGE,
        **_cookie_kwargs(),
    )


def _clear_refresh_cookie(response: Response):
    response.delete_cookie(key=REFRESH_COOKIE_NAME, **_cookie_kwargs())


def _sanitize_auth_response(result):
    if isinstance(result, dict):
        session_payload = dict(result.get("session") or {})
        refresh_token = session_payload.pop("refresh_token", None)
        return {**result, "session": session_payload or None}, refresh_token

    session_payload = dict(getattr(result, "session", None) or {})
    refresh_token = session_payload.pop("refresh_token", None)
    result.session = session_payload or None
    return result, refresh_token


def get_auth_controller():
    repo = AuthRepository()
    service = AuthService(repo)
    return AuthController(service)


@router.post(
    "/signup",
    response_model=AuthResponse,
    responses={
        400: {"model": ApiErrorResponse},
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        422: {"model": ApiErrorResponse},
        500: {"model": ApiErrorResponse},
    },
)
async def sign_up(
    data: SignUpDTO,
    user: dict = Depends(get_current_user),
    controller: AuthController = Depends(get_auth_controller),
):
    # Only admins can create new accounts
    if user.get("role") not in ("admin", "super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create new accounts.",
        )
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
    result, refresh_token = _sanitize_auth_response(result)
    if refresh_token:
        _set_refresh_cookie(response, refresh_token)

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
        try:
            logging_service = LoggingService()
            await logging_service.log_user_login(
                user_id=user_payload["id"],
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent"),
            )
        except Exception as e:
            logger.warning(f"Failed to log login action: {e}")
    return result


@router.post(
    "/refresh",
    response_model=AuthResponse,
    responses={
        401: {"model": ApiErrorResponse},
        500: {"model": ApiErrorResponse},
    },
)
async def refresh_session(
    request: Request,
    response: Response,
    controller: AuthController = Depends(get_auth_controller),
):
    refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh session is unavailable. Please sign in again.",
        )

    result = await controller.refresh_session(refresh_token)
    result, next_refresh_token = _sanitize_auth_response(result)
    if next_refresh_token:
        _set_refresh_cookie(response, next_refresh_token)
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
        data.current_password,
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
    return await controller.get_me(
        user["id"], user["email"], user["role"], user.get("avatar_url")
    )


@router.post(
    "/sign-out",
    response_model=SuccessResponse,
    responses={
        401: {"model": ApiErrorResponse},
        500: {"model": ApiErrorResponse},
    },
)
async def sign_out(
    response: Response,
    data: SignOutDTO,
    user: dict = Depends(get_current_user),
    controller: AuthController = Depends(get_auth_controller),
):
    result = await controller.sign_out(
        user["id"], data.scope or "single", user["access_token"]
    )
    _clear_refresh_cookie(response)

    try:
        logging_service = LoggingService()
        await logging_service.log_user_logout(
            user_id=user["id"],
            ip_address=None,
            user_agent=None,
        )
    except Exception as e:
        logger.warning(f"Failed to log logout action: {e}")
    return result
