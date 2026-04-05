"""Global Exception Handler Middleware."""

from datetime import datetime
import re

try:
    from datetime import UTC  # Python 3.11+
except ImportError:
    from datetime import timezone
    UTC = timezone.utc
import uuid

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.observability.logger import get_correlation_id, get_logger
from src.security.config import security_config
from src.validators.response_dto import ApiErrorResponse, ErrorDetail

logger = get_logger("middleware.error_handler")

_SENSITIVE_ERROR_PATTERNS = [
    (re.compile(r"(password\s*[=:]\s*)([^\s,;]+)", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(token\s*[=:]\s*)([^\s,;]+)", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(secret\s*[=:]\s*)([^\s,;]+)", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"([A-Za-z]:\\[^\s'\"]+|/[^\s'\"]+/[^\s'\"]+)", re.IGNORECASE), "[REDACTED_PATH]"),
]


def _redact_sensitive_message(value: str) -> str:
    redacted = value
    for pattern, replacement in _SENSITIVE_ERROR_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


class GlobalExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """Global exception handler for consistent error responses."""

    @staticmethod
    def _error_payload(
        *,
        status_code: int,
        error: str,
        message: str,
        error_code: str,
        details: ErrorDetail | None = None,
    ) -> JSONResponse:
        payload = ApiErrorResponse(
            success=False,
            error=error,
            message=message,
            details=details,
            error_code=error_code,
            correlation_id=get_correlation_id(),
            timestamp=datetime.now(UTC).isoformat(),
        )
        return JSONResponse(status_code=status_code, content=payload.model_dump())

    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except HTTPException as exc:
            detail = exc.detail if isinstance(exc.detail, str) else "Request failed"
            return self._error_payload(
                status_code=exc.status_code,
                error=detail,
                message=detail,
                error_code=f"HTTP_{exc.status_code}",
            )
        except ValueError as exc:
            logger.warning(
                f"Validation error: {str(exc)}",
                extra={
                    "correlation_id": get_correlation_id(),
                    "path": str(request.url.path),
                },
            )
            return self._error_payload(
                status_code=400,
                error="Validation failed",
                message="Validation failed",
                error_code="VALIDATION_ERROR",
                details=ErrorDetail(message=str(exc), field="request"),
            )
        except Exception as exc:
            error_id = str(uuid.uuid4())
            error_message = "An internal server error occurred"
            if security_config.EXPOSE_ERROR_DETAILS:
                error_message = f"Internal error: {_redact_sensitive_message(str(exc))}"

            logger.error(
                f"Unhandled exception [{error_id}]: {str(exc)}",
                extra={
                    "correlation_id": get_correlation_id(),
                    "error_id": error_id,
                    "path": str(request.url.path),
                    "method": request.method,
                    "user_agent": request.headers.get("user-agent", "unknown"),
                    "client_ip": request.client.host if request.client else "unknown",
                },
            )

            return self._error_payload(
                status_code=500,
                error=error_message,
                message="Unexpected internal error",
                error_code="INTERNAL_SERVER_ERROR",
                details=ErrorDetail(
                    message="Please contact support if this persists",
                    field="system",
                    code=error_id,
                ),
            )
