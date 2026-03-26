import ast
import asyncio
import functools
import logging
import re
from typing import Any, Callable, Tuple, Type

logger = logging.getLogger("infrastructure.retry")


def _coerce_mapping(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        return value

    if isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith("{") and stripped.endswith("}"):
            try:
                parsed = ast.literal_eval(stripped)
            except (SyntaxError, ValueError):
                return None

            if isinstance(parsed, dict):
                return parsed

    return None


def extract_exception_status_code(exception: Exception) -> int | None:
    """Best-effort HTTP/storage status extraction for retry decisions."""

    def _coerce_status(value: Any) -> int | None:
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return None

    def _extract_status_from_string(value: Any) -> int | None:
        if not isinstance(value, str):
            return None

        match = re.search(r"status(?:Code|_code)?['\"]?\s*:\s*(\d{3})", value)
        if match:
            return int(match.group(1))
        return None

    for attr in ("status_code", "status", "statusCode"):
        status = _coerce_status(getattr(exception, attr, None))
        if status is not None:
            return status

    candidates = (
        getattr(exception, "args", (None,))[0],
        getattr(exception, "response", None),
        getattr(exception, "detail", None),
    )

    for candidate in candidates:
        status = _coerce_status(getattr(candidate, "status_code", None))
        if status is not None:
            return status

        status = _extract_status_from_string(candidate)
        if status is not None:
            return status

        payload = _coerce_mapping(candidate)
        if not payload:
            continue

        for key in ("statusCode", "status_code", "status"):
            status = _coerce_status(payload.get(key))
            if status is not None:
                return status

    return None


def should_retry_http_exception(exception: Exception) -> bool:
    """Retry only when the failure does not look like a client-side HTTP/storage error."""

    status_code = extract_exception_status_code(exception)
    return status_code is None or status_code >= 500


def async_retry(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
    retry_on_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    retry_if: Callable[[Exception], bool] | None = None,
):
    """
    Plan Section 8.A: Async Retry Decorator with Exponential Backoff.
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            from src.security.config import security_config

            if not getattr(security_config, "ENABLE_RETRIES", True):
                return await func(*args, **kwargs)

            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except retry_on_exceptions as e:
                    last_exception = e
                    if retry_if is not None and not retry_if(e):
                        logger.warning(
                            f"Non-retryable failure for {func.__name__}: {str(e)}"
                        )
                        raise e

                    if attempt == max_retries - 1:
                        logger.error(
                            f"Final attempt failed for {func.__name__}: {str(e)}"
                        )
                        raise e

                    logger.warning(
                        f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. "
                        f"Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                    delay *= backoff_factor

        return wrapper

    return decorator
