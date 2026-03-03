"""
Metrics Middleware - Track API request/response metrics for dashboard monitoring.

This middleware automatically tracks:
- Request/response times
- Endpoint usage statistics
- Error occurrences
- Rate limiting violations
- Active requests count
"""

import time
import os
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from src.observability.logger import get_logger
from datetime import datetime

logger = get_logger("middleware.metrics")

# In-memory storage for active requests count
active_requests_count = 0
unsupported_audit_columns: set[str] = set()
ENABLE_METRICS_AUDIT_LOGGING = (
    os.getenv("ENABLE_METRICS_AUDIT_LOGGING", "true").strip().lower() == "true"
)
EXCLUDED_ENDPOINT_PREFIXES = (
    "/health",
    "/ready",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/scalar",
    "/swagger-diagnosis",
    "/swagger-fix",
)
if os.getenv("TESTING", "false").strip().lower() == "true":
    ENABLE_METRICS_AUDIT_LOGGING = False


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track API metrics for observability.

    Tracks:
    - Request duration
    - Response status codes
    - Endpoint usage
    - Active requests
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        global active_requests_count

        # Increment active requests
        active_requests_count += 1

        # Start timing
        start_time = time.time()

        # Extract request info
        endpoint = request.url.path
        method = request.method
        should_persist_metrics = ENABLE_METRICS_AUDIT_LOGGING and not endpoint.startswith(
            EXCLUDED_ENDPOINT_PREFIXES
        )

        response = None
        status_code = 500  # Default to error

        try:
            # Process request
            response = await call_next(request)
            status_code = response.status_code

            # Calculate response time
            response_time_ms = (time.time() - start_time) * 1000

            # Log metrics (async background task would be better for production)
            if should_persist_metrics:
                await self._log_api_metrics(
                    endpoint=endpoint,
                    method=method,
                    status_code=status_code,
                    response_time_ms=response_time_ms,
                    timestamp=datetime.now(),
                )

            # Add response time header for debugging
            response.headers["X-Response-Time"] = f"{response_time_ms:.2f}ms"

            return response

        except Exception as e:
            logger.error(f"Request failed: {endpoint} - {str(e)}")

            # Log error
            response_time_ms = (time.time() - start_time) * 1000
            if should_persist_metrics:
                await self._log_api_metrics(
                    endpoint=endpoint,
                    method=method,
                    status_code=500,
                    response_time_ms=response_time_ms,
                    timestamp=datetime.now(),
                    error=str(e),
                )

            raise  # Re-raise the exception

        finally:
            # Decrement active requests
            active_requests_count -= 1

    async def _log_api_metrics(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: float,
        timestamp: datetime,
        error: str = None,
    ):
        """
        Log API metrics to audit_logs table for dashboard consumption.
        With retry logic and local fallback.
        """
        log_data = {
            "user_id": None,
            "action": f"api_request:{method}",
            "resource_type": "api_endpoint",
            "resource_id": None,
            "details": {
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "response_time_ms": round(response_time_ms, 2),
                "error_message": error,
            },
        }

        await self._insert_with_retry(log_data)

    async def _insert_with_retry(
        self, log_data: dict, max_retries: int = 3, initial_delay: float = 1.0
    ):
        """Insert log data with exponential backoff and fallback."""
        from src.db.supabase.client import SupabaseProvider
        import asyncio

        payload = dict(log_data)
        for column in unsupported_audit_columns:
            payload.pop(column, None)

        for attempt in range(max_retries):
            try:
                client = await SupabaseProvider.get_admin()
                await client.table("audit_logs").insert(payload).execute()
                return  # Success
            except Exception as e:
                error_text = str(e)

                # Handle schema drift without adding request latency via retries.
                if "PGRST204" in error_text:
                    unknown_column = None
                    marker = "Could not find the '"
                    if marker in error_text:
                        unknown_column = error_text.split(marker, 1)[1].split("'", 1)[0]

                    if unknown_column and unknown_column in payload:
                        unsupported_audit_columns.add(unknown_column)
                        payload.pop(unknown_column, None)
                        continue

                if attempt == max_retries - 1:
                    logger.error(
                        f"Supabase logging failed after {max_retries} attempts: {error_text}"
                    )
                    await asyncio.to_thread(self._log_to_fallback_file, payload)
                    return

                delay = initial_delay * (2**attempt)
                logger.warning(
                    f"Logging attempt {attempt + 1} failed, retrying in {delay}s: {error_text}"
                )
                await asyncio.sleep(delay)

    def _log_to_fallback_file(self, data: dict):
        """Fallback logging to a local file when Supabase is unreachable."""
        import json
        import os

        try:
            log_dir = os.path.join("logs", "audit")
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, "audit_fallback.log")

            with open(log_file, "a") as f:
                log_entry = {
                    "fallback_timestamp": datetime.now().isoformat(),
                    "data": data,
                    "source": "metrics_middleware_fallback",
                }
                f.write(json.dumps(log_entry) + "\n")
            logger.info(f"Successfully wrote audit log to fallback file: {log_file}")
        except Exception as e:
            logger.error(f"Critical: Failed to write to fallback log: {str(e)}")


def get_active_requests_count() -> int:
    """Get current count of active requests."""
    return active_requests_count

