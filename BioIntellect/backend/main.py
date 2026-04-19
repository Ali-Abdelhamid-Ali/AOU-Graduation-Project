"""Main API Entry Point - BioIntellect Backend."""

import os
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, cast

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
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
    logging_routes,
    notification_routes,
    rag_data,
    NLP_routes,
    rag_routes,
    real_time_monitoring_routes,
    report_routes,
    statistics_routes,
    system_routes,
    user_routes,
    websocket_routes,
)
from src.config.settings import get_settings
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
from src.stores.llm.templates.template_parser import template_parser
from src.stores.llm.LLMProviderFactory import LLMProviderFactory
from src.validators.response_dto import ApiErrorResponse
from src.stores.vectordb.VectorDBProviderFactory import VectorDBProviderFactory
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

    security_config.validate()
    user_status = await user_check_service.check_all_users_exist()
    logger.info(f"Verified Core User Profiles: {user_status}")

    diagnosis = await swagger_ui_fix_service.diagnose_swagger_issues()
    if diagnosis.get("issues_found", 0) > 0:
        logger.info(
            f"Applying Swagger UI fixes: {diagnosis['issues_found']} issues detected."
        )
        await swagger_ui_fix_service.apply_swagger_fixes()

    _STARTUP_COMPLETED = True
    logger.info("BioIntellect API initialization complete")


async def _run_shutdown(app: FastAPI) -> None:
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

    try:
        if hasattr(app.state, "vectordb_client") and app.state.vectordb_client:
            app.state.vectordb_client.disconnect()
            logger.info("VectorDB connections closed successfully")
    except Exception as exc:
        logger.error(f"Error disconnecting VectorDB client: {exc}")

    _SHUTDOWN_COMPLETED = True





def create_app() -> FastAPI:
    default_error_responses: Dict[int | str, Dict[str, Any]] = {
        401: {"model": ApiErrorResponse, "description": "Unauthorized"},
        403: {"model": ApiErrorResponse, "description": "Forbidden"},
        429: {"model": ApiErrorResponse, "description": "Too Many Requests"},
        500: {"model": ApiErrorResponse, "description": "Internal Server Error"},
    }

    async def on_startup(app: FastAPI) -> None:
        startup_started = time.perf_counter()
        timings: Dict[str, float] = {}
        settings = get_settings()
        embedding_backend = settings.EMBEDDING_BACKEND or settings.GENERATION_BACKEND
        #Provider Factories
        llm_provider_factory = LLMProviderFactory(settings)
        vectordb_provider_factory = VectorDBProviderFactory(settings)
        
        generation_started = time.perf_counter()
        generation_client = llm_provider_factory.create(backend=settings.GENERATION_BACKEND)
        timings["generation_client_s"] = time.perf_counter() - generation_started

        if settings.GENERATION_MODEL_ID:
            generation_client.set_generation_model(model_id=settings.GENERATION_MODEL_ID)
        else:
            logger.warning("GENERATION_MODEL_ID is not set; using provider default generation model")
        app.state.generation_client = generation_client

        embedding_started = time.perf_counter()
        if embedding_backend == settings.GENERATION_BACKEND:
            embedding_client = generation_client
        else:
            embedding_client = llm_provider_factory.create(backend=embedding_backend)

        if embedding_backend == "cohere":
            if not settings.EMBEDDING_MODEL_ID or settings.EMBEDDING_MODEL_SIZE is None:
                raise RuntimeError("Invalid cohere embedding configuration: EMBEDDING_MODEL_ID and EMBEDDING_MODEL_SIZE are required.")
            embedding_client.set_embedding_model(model_id=settings.EMBEDDING_MODEL_ID,embedding_size=settings.EMBEDDING_MODEL_SIZE)
        elif embedding_backend == "openai":
            if not settings.EMBEDDING_MODEL_ID:
                raise RuntimeError("Invalid openai embedding configuration: EMBEDDING_MODEL_ID is required.")
            embedding_client.set_embedding_model(model_id=settings.EMBEDDING_MODEL_ID,embedding_size=settings.EMBEDDING_MODEL_SIZE or 0)
        elif embedding_backend == "phi_qa":
            logger.info("Embedding backend is phi_qa; using local model path without separate EMBEDDING_MODEL_ID")
        elif embedding_backend == "medmo":
            raise RuntimeError("medmo embedding is not supported. ""Set EMBEDDING_BACKEND to phi_qa, openai, or cohere.")
        else:
            raise RuntimeError(f"Unsupported embedding backend during startup: {embedding_backend}")
        timings["embedding_client_s"] = time.perf_counter() - embedding_started

        app.state.embedding_client = embedding_client
        vectordb_started = time.perf_counter()
        app.state.vectordb_client = vectordb_provider_factory.create(
            Provider=settings.VECTOR_DB_BACKEND
        )
        if app.state.vectordb_client is None:
            failure_context = (
                vectordb_provider_factory.last_error
                if vectordb_provider_factory.last_error
                else "unknown error"
            )
            raise RuntimeError(
                f"Vector database provider failed to initialize; "
                f"provider={settings.VECTOR_DB_BACKEND}, "
                f"db_path={vectordb_provider_factory.last_db_path}, "
                f"reason={failure_context}"
            )
        app.state.vectordb_client.connect()
        logger.info(
            f"Connected to vector database using {settings.VECTOR_DB_BACKEND} provider"
        )
        timings["vectordb_client_s"] = time.perf_counter() - vectordb_started
        app.state.template_parser = template_parser(language=settings.PRIMARY_LANG, default_language=settings.DEFAULT_LANG)
        timings["startup_total_s"] = time.perf_counter() - startup_started
        logger.info("Startup timings %s", timings)
        

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        try:
            await _run_startup()
            await on_startup(app)
        except Exception as exc:
            logger.error(f"Critical error during startup: {exc}")
            raise RuntimeError("Startup failed") from exc

        try:
            yield
        finally:
            await _run_shutdown(app)

    app = FastAPI(
        title="BioIntellect API",
        description="Refactored Production-Hardened Medical API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        
        openapi_url="/openapi.json",
        responses=default_error_responses,
        lifespan=lifespan,
    )

    app.state.limiter = limiter

    async def _rate_limit_exception_handler(request: Request, exc: Exception):
        return _rate_limit_exceeded_handler(request, cast(RateLimitExceeded, exc))

    app.add_exception_handler(RateLimitExceeded, _rate_limit_exception_handler)
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
    app.include_router(logging_routes.router, prefix=api_prefix)
    app.include_router(real_time_monitoring_routes.router, prefix=api_prefix)
    app.include_router(audit_routes.router, prefix=api_prefix)
    app.include_router(system_routes.router, prefix=api_prefix)
    app.include_router(statistics_routes.router, prefix=api_prefix)
    app.include_router(notification_routes.router, prefix=api_prefix)
    app.include_router(websocket_routes.router, prefix=api_prefix)
    app.include_router(rag_routes.router, prefix=api_prefix)
    app.include_router(rag_data.router, prefix=api_prefix)
    app.include_router(NLP_routes.router, prefix=api_prefix)

    app.openapi_schema = None

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

    app.openapi = custom_openapi  # type: ignore[method-assign]

    @app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse(url="/docs")

    @app.get("/health", tags=["system"])
    async def liveness_check() -> Dict[str, Any]:
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "version": app.version,
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
                if health_status["status"] == "ready":
                    health_status["status"] = "degraded"
        except Exception:
            health_status["checks"]["cache"] = "error"
            if health_status["status"] == "ready":
                health_status["status"] = "degraded"

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
        if security_config.ENVIRONMENT == "production":
            raise HTTPException(status_code=404, detail="Not found")
        return await swagger_ui_fix_service.diagnose_swagger_issues()

    @app.get("/swagger-fix")
    async def swagger_fix():
        if security_config.ENVIRONMENT == "production":
            raise HTTPException(status_code=404, detail="Not found")
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
    uvicorn.run(app, host="127.0.0.1", port=int(os.getenv("PORT", "8000")))
