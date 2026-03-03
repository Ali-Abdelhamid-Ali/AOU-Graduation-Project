import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from src.observability.logger import get_logger

logger = get_logger("middleware.performance")


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()

        response = await call_next(request)

        process_time = time.perf_counter() - start_time

        log_message = (
            f"{request.method} {request.url.path} processed in {process_time:.4f}s"
        )

        if process_time > 5.0:
            logger.error(f"CRITICAL SLOW REQUEST: {log_message}")
        elif process_time > 1.0:
            logger.warning(f"SLOW REQUEST: {log_message}")
        else:
            logger.debug(log_message)

        response.headers["X-Process-Time"] = str(process_time)
        return response

