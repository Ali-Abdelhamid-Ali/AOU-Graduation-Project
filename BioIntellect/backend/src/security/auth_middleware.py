"""Security Middleware - Authentication, Authorization, and Tracing."""

import hashlib

import uuid
from typing import Annotated, Any

from fastapi import HTTPException, Request, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware

from src.db.supabase.client import SupabaseProvider
from src.observability.logger import (
    get_correlation_id,
    get_logger,
    set_correlation_id,
)
from src.repositories.auth_repository import AuthRepository
from src.security.permission_map import Permission, get_role_permissions

logger = get_logger("security.middleware")
security = HTTPBearer(auto_error=False)
ALLOWED_ROLES = {"patient", "doctor", "nurse", "admin", "super_admin"}
# ...........
FAILED_ATTEMPTS_TTL = 60 * 5  # 5 minutes


class AuthService:
    def __init__(self, repo, cache):
        self.repo = repo
        self.cache = cache  # Redis client

    async def _get_failed_attempts(self, email: str) -> int:
        value = await self.cache.get(f"login_fail:{email}")
        return int(value) if value else 0

    async def _increment_failed_attempts(self, email: str):
        key = f"login_fail:{email}"

        attempts = await self.cache.incr(key)

        # ط£ظˆظ„ ظ…ط±ط© â†’ ط­ط· TTL
        if attempts == 1:
            await self.cache.expire(key, FAILED_ATTEMPTS_TTL)

        return attempts

    async def _reset_failed_attempts(self, email: str):
        await self.cache.delete(f"login_fail:{email}")


# ...............
class CorrelationMiddleware(BaseHTTPMiddleware):
    """
    Pure middleware that only attaches context without business logic.
    No authentication, no authorization, no logging - pure context management.
    Excludes Swagger UI routes to prevent conflicts with unauthenticated requests.
    """

    # Routes that should be excluded from correlation middleware
    EXCLUDED_PATHS = {
        "/docs",
        "/redoc",
        "/openapi.json",
        "/",
        "/health",
        "/swagger-diagnosis",
        "/swagger-fix",
    }

    def should_exclude_path(self, path: str) -> bool:
        """Check if the path should be excluded from correlation middleware."""
        # Handle exact matches
        if path in self.EXCLUDED_PATHS:
            return True

        # Handle path prefixes (e.g., /docs/anything)
        for excluded_path in self.EXCLUDED_PATHS:
            if path.startswith(excluded_path + "/"):
                return True

        return False

    async def dispatch(self, request: Request, call_next):
        # Skip correlation middleware for excluded paths
        if self.should_exclude_path(request.url.path):
            return await call_next(request)

        # âœ… CORRECT: Context attachment only
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        set_correlation_id(correlation_id)

        # âœ… CORRECT: Attach to request state
        request.state.correlation_id = correlation_id

        # âœ… CORRECT: Pass through without business logic
        response = await call_next(request)

        # âœ… CORRECT: Add headers only
        response.headers["X-Correlation-ID"] = correlation_id

        return response


def _extract_user_attr(user: Any, attr: str, default: Any = "") -> Any:
    """Read auth user attributes across object and dict payloads."""
    return getattr(user, attr, default) or (
        user.get(attr, default) if isinstance(user, dict) else default
    )


def _normalize_role(role: Any) -> str | None:
    value = str(role or "").strip().lower()
    return value if value in ALLOWED_ROLES else None


async def _resolve_role(user_id: str, metadata_role: str | None) -> str:
    """Resolve authoritative role and prevent metadata-only escalation."""
    resolved = await AuthRepository().resolve_user_role(user_id, metadata_role)
    normalized = _normalize_role(resolved)
    return normalized or "patient"


async def _build_user_context(token: str, user: Any) -> dict[str, Any]:
    user_metadata = _extract_user_attr(user, "user_metadata", {}) or {}
    user_id: str = str(_extract_user_attr(user, "id", "") or "")
    user_email: str = str(_extract_user_attr(user, "email", "") or "")
    hospital_id: str | None = user_metadata.get("hospital_id")
    metadata_role = _normalize_role(user_metadata.get("role"))
    role = await _resolve_role(user_id, metadata_role)
    auth_repo = AuthRepository()
    profile_table = {
        "patient": "patients",
        "doctor": "doctors",
        "nurse": "nurses",
        "admin": "administrators",
        "super_admin": "administrators",
    }.get(role)
    try:
        profile = (
            await auth_repo.get_profile_by_user_id(profile_table, user_id)
            if profile_table
            else None
        )
    except Exception:
        profile = None
    profile_id = str(profile.get("id")) if profile and profile.get("id") else None
    if not hospital_id and profile:
        hospital_id = profile.get("hospital_id")

    if metadata_role and metadata_role != role:
        logger.warning(
            "Role mismatch detected; using authoritative role",
            extra={"user_id": user_id, "metadata_role": metadata_role, "resolved_role": role},
        )

    return {
        "id": user_id,
        "profile_id": profile_id,
        "email": user_email,
        "role": role,
        "avatar_url": user_metadata.get("avatar_url"),
        "hospital_id": hospital_id,
        "permissions": get_role_permissions(role),
        "access_token": token,
    }


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(security)],
) -> dict[str, Any]:
    """
    Dependency to verify token and extract user context.
    """
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=401, detail="Authentication required. Missing bearer token."
        )

    token = credentials.credentials
    try:
        supabase = await SupabaseProvider.get_client()
        auth_response = await supabase.auth.get_user(token)

        # Robust user extraction
        user = getattr(auth_response, "user", None) or (
            auth_response.get("user") if isinstance(auth_response, dict) else None
        )

        if not user:
            raise HTTPException(
                status_code=401, detail="Authentication failed. Please try again."
            )

        return await _build_user_context(token, user)
    except HTTPException:
        raise
    except Exception as e:
        # Security: Do not log sensitive token information (OWASP violation)
        token_hint = (
            hashlib.sha256(token.encode()).hexdigest()[:16] if token else "missing"
        )
        logger.error(
            f"Auth verification failed: {str(e)} | token_hint={token_hint}"
        )
        raise HTTPException(
            status_code=401, detail="Authentication failed. Please try again."
        ) from e


async def get_current_user_ws(token: str | None) -> dict[str, Any] | None:
    """
    Verify JWT token for WebSocket connections.

    Args:
        token: JWT token from query parameter

    Returns:
        User dict with id, email, role, and permissions or None if auth fails
    """
    try:
        if not token:
            return None
        supabase = await SupabaseProvider.get_client()
        auth_response = await supabase.auth.get_user(token)

        # Robust user extraction
        user = getattr(auth_response, "user", None) or (
            auth_response.get("user") if isinstance(auth_response, dict) else None
        )

        if not user:
            logger.warning("Invalid WebSocket token")
            return None

        user_context = await _build_user_context(token, user)
        user_context.pop("access_token", None)
        return user_context
    except Exception as e:
        logger.error(f"WebSocket auth failed: {str(e)}")
        return None


def require_permission(permission: Permission):
    """
    Higher-order dependency for Permission-Based Access Control (PBAC).
    Implements DEFAULT-DENY with enhanced security logging.
    """

    async def permission_checker(
        user: Annotated[dict, Security(get_current_user)]
    ):
        if permission not in user["permissions"]:
            logger.warning(
                "Unauthorized access attempt",
                extra={
                    "user_id": user["id"],
                    "user_email": user.get("email", "unknown"),
                    "user_role": user.get("role", "unknown"),
                    "requested_permission": permission,
                    "correlation_id": get_correlation_id(),
                },
            )
            raise HTTPException(
                status_code=403,
                detail="Access denied: Insufficient permissions",
                headers={"X-Correlation-ID": get_correlation_id()},
            )
        return user

    return permission_checker

