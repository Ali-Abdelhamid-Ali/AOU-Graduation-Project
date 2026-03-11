"""Main API Entry Point - BioIntellect Backend."""

import os
import time
from contextlib import asynccontextmanager
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from scalar_fastapi import get_scalar_api_reference
from starlette.middleware.trustedhost import TrustedHostMiddleware

from src.api.routes import (
    analytics_routes,
    audit_routes,
    auth_routes,
    clinical_routes,
    dashboard_routes,
    file_routes,
    geography_routes,
    llm_routes,
    logging_routes,
    notification_routes,
    real_time_monitoring_routes,
    report_routes,
    statistics_routes,
    system_routes,
    user_routes,
    websocket_routes,
)
from src.db.supabase.client import SupabaseProvider
from src.middleware.error_handler import GlobalExceptionHandlerMiddleware
from src.middleware.metrics_middleware import MetricsMiddleware
from src.middleware.performance_middleware import PerformanceMonitoringMiddleware
from src.middleware.rate_limiter import (
    RateLimitExceeded,
    SlowAPIMiddleware,
    _rate_limit_exceeded_handler,
    limiter,
)
from src.middleware.real_time_monitor import RealTimeMonitoringMiddleware
from src.middleware.security_headers import SecurityHeadersMiddleware
from src.observability.logger import get_logger, setup_logging
from src.repositories.storage_repository import StorageRepository
from src.security.auth_middleware import CorrelationMiddleware
from src.security.config import security_config
from src.services.domain.swagger_ui_fix import swagger_ui_fix_service
from src.services.domain.user_check_service import user_check_service
from src.services.infrastructure.memory_cache import global_cache
from src.validators.response_dto import ApiErrorResponse

setup_logging()
logger = get_logger(__name__)

_STARTUP_COMPLETED = False
_SHUTDOWN_COMPLETED = False


async def _run_startup() -> None:
    """Startup logic with idempotency for worker reload edge cases."""
    global _STARTUP_COMPLETED
    if _STARTUP_COMPLETED:
        logger.info("Startup logic already executed; skipping")
        return

    logger.info("Starting BioIntellect API initialization")
    _STARTUP_COMPLETED = True

    security_config.validate()
    user_status = await user_check_service.check_all_users_exist()
    logger.info(f"Verified Core User Profiles: {user_status}")

    diagnosis = await swagger_ui_fix_service.diagnose_swagger_issues()
    if diagnosis.get("issues_found", 0) > 0:
        logger.info(
            f"Applying Swagger UI fixes: {diagnosis['issues_found']} issues detected."
        )
        await swagger_ui_fix_service.apply_swagger_fixes()

    logger.info("BioIntellect API initialization complete")


async def _run_shutdown() -> None:
    """Shutdown logic with idempotency."""
    global _SHUTDOWN_COMPLETED
    if _SHUTDOWN_COMPLETED:
        return

    logger.info("Shutting down BioIntellect API")
    try:
        await SupabaseProvider.close_all()
        logger.info("Supabase connections closed successfully")
    except Exception as exc:
        logger.error(f"Error closing Supabase connections: {exc}")
    _SHUTDOWN_COMPLETED = True


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await _run_startup()
    except Exception as exc:
        logger.error(f"Critical error during startup: {exc}")
        raise RuntimeError("Startup failed") from exc

    try:
        yield
    finally:
        await _run_shutdown()


def create_app() -> FastAPI:
    default_error_responses = {
        401: {"model": ApiErrorResponse, "description": "Unauthorized"},
        403: {"model": ApiErrorResponse, "description": "Forbidden"},
        429: {"model": ApiErrorResponse, "description": "Too Many Requests"},
        500: {"model": ApiErrorResponse, "description": "Internal Server Error"},
    }

    app = FastAPI(
        title="BioIntellect API",
        description="Refactored Production-Hardened Medical API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        responses=default_error_responses,
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(PerformanceMonitoringMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=security_config.CORS_ORIGINS,
        allow_origin_regex=security_config.CORS_ORIGIN_REGEX,
        allow_credentials=security_config.CORS_ALLOW_CREDENTIALS,
        allow_methods=security_config.CORS_ALLOW_METHODS,
        allow_headers=security_config.CORS_ALLOW_HEADERS,
    )
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=(
            security_config.TRUSTED_HOSTS
            if security_config.ENVIRONMENT == "production"
            else list(
                {
                    *security_config.TRUSTED_HOSTS,
                    "localhost",
                    "127.0.0.1",
                    "0.0.0.0",
                    "testserver",
                }
            )
        ),
    )
    app.add_middleware(CorrelationMiddleware)
    app.add_middleware(RealTimeMonitoringMiddleware)
    app.add_middleware(GlobalExceptionHandlerMiddleware)

    api_prefix = security_config.API_PREFIX

    app.include_router(auth_routes.router, prefix=api_prefix)
    app.include_router(dashboard_routes.router, prefix=api_prefix)
    app.include_router(clinical_routes.router, prefix=api_prefix)
    app.include_router(analytics_routes.router, prefix=api_prefix)
    app.include_router(file_routes.router, prefix=api_prefix)
    app.include_router(report_routes.router, prefix=api_prefix)
    app.include_router(geography_routes.router, prefix=api_prefix)
    app.include_router(user_routes.router, prefix=api_prefix)
    app.include_router(llm_routes.router, prefix=api_prefix)
    app.include_router(logging_routes.router, prefix=api_prefix)
    app.include_router(real_time_monitoring_routes.router, prefix=api_prefix)
    app.include_router(audit_routes.router, prefix=api_prefix)
    app.include_router(system_routes.router, prefix=api_prefix)
    app.include_router(statistics_routes.router, prefix=api_prefix)
    app.include_router(notification_routes.router, prefix=api_prefix)
    app.include_router(websocket_routes.router, prefix=api_prefix)

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        # Normalize empty JSON schemas so generated docs are contract-friendly.
        for path_item in schema.get("paths", {}).values():
            for operation in path_item.values():
                if not isinstance(operation, dict):
                    continue
                for response in (operation.get("responses") or {}).values():
                    app_json = (
                        response.get("content", {}).get("application/json")
                        if isinstance(response, dict)
                        else None
                    )
                    if app_json and app_json.get("schema") == {}:
                        app_json["schema"] = {"type": "object"}

        app.openapi_schema = schema
        return app.openapi_schema

    app.openapi = custom_openapi

    @app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse(url="/docs")

    @app.get("/health", tags=["system"])
    async def liveness_check() -> Dict[str, Any]:
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "version": "1.0.0",
        }

    @app.get(f"{api_prefix}/health", tags=["system"], include_in_schema=False)
    async def versioned_liveness_check() -> Dict[str, Any]:
        return await liveness_check()

    async def _readiness_payload() -> Dict[str, Any]:
        health_status: Dict[str, Any] = {
            "status": "ready",
            "timestamp": time.time(),
            "checks": {
                "database": "connected",
                "storage": "accessible",
                "cache": "active",
            },
        }

        try:
            await global_cache.set("health_check_ping", "pong", ttl_seconds=10)
            if await global_cache.get("health_check_ping") != "pong":
                health_status["checks"]["cache"] = "degraded"
        except Exception:
            health_status["checks"]["cache"] = "error"

        try:
            admin_client = await SupabaseProvider.get_admin()
            await admin_client.table("administrators").select("id").limit(1).execute()
        except Exception as exc:
            logger.error(f"Readiness database check failed: {exc}")
            health_status["checks"]["database"] = "error"
            health_status["status"] = "not_ready"

        try:
            storage = StorageRepository()
            await storage.is_accessible()
        except Exception as exc:
            logger.error(f"Readiness storage check failed: {exc}")
            health_status["checks"]["storage"] = "error"
            if health_status["status"] == "ready":
                health_status["status"] = "degraded"

        return health_status

    @app.get("/health/ready", tags=["system"])
    async def readiness_check() -> Dict[str, Any]:
        health_status = await _readiness_payload()
        if health_status["status"] == "not_ready":
            raise HTTPException(status_code=503, detail=health_status)
        return health_status

    @app.get(
        f"{api_prefix}/health/ready", tags=["system"], include_in_schema=False
    )
    async def versioned_readiness_check() -> Dict[str, Any]:
        return await readiness_check()

    @app.get("/ready", tags=["system"])
    async def readiness_alias() -> Dict[str, Any]:
        health_status = await _readiness_payload()
        if health_status["status"] == "not_ready":
            raise HTTPException(status_code=503, detail=health_status)
        return health_status

    @app.get(f"{api_prefix}/ready", tags=["system"], include_in_schema=False)
    async def versioned_readiness_alias() -> Dict[str, Any]:
        return await readiness_alias()

    @app.get("/swagger-diagnosis")
    async def swagger_diagnosis():
        return await swagger_ui_fix_service.diagnose_swagger_issues()

    @app.get("/swagger-fix")
    async def swagger_fix():
        return await swagger_ui_fix_service.apply_swagger_fixes()

    @app.get("/scalar", include_in_schema=False)
    def get_scalar_docs():
        return get_scalar_api_reference(
            openapi_url=app.openapi_url,
            title="Scalar API",
        )

    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
