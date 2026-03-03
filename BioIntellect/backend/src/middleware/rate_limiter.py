"""Rate Limiting Middleware using SlowAPI."""

from slowapi import Limiter, _rate_limit_exceeded_handler  # type: ignore
from slowapi.util import get_remote_address  # type: ignore
from slowapi.errors import RateLimitExceeded  # type: ignore
from slowapi.middleware import SlowAPIMiddleware  # type: ignore
from fastapi import Request

from src.security.config import security_config


def _request_ip(request: Request) -> str:
    """Resolve caller IP behind proxies while keeping a safe fallback."""
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return get_remote_address(request)


def _build_default_limit() -> str:
    """Translate numeric env config into SlowAPI limit string."""
    requests = max(1, int(security_config.RATE_LIMIT_REQUESTS))
    window = max(1, int(security_config.RATE_LIMIT_WINDOW))
    if window == 60:
        return f"{requests}/minute"
    if window == 3600:
        return f"{requests}/hour"
    return f"{requests}/{window} second"

# Initialize the limiter
limiter = Limiter(
    key_func=_request_ip,
    default_limits=[_build_default_limit()] if security_config.RATE_LIMIT_ENABLED else [],
    headers_enabled=True,
)

# Export for use in main.py
__all__ = [
    "limiter",
    "RateLimitExceeded",
    "_rate_limit_exceeded_handler",
    "SlowAPIMiddleware",
]
