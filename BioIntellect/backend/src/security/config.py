"""Security Configuration - Production Hardened Settings."""

import os
from typing import Dict, Any

from src.config.settings import settings
from src.observability.logger import get_logger

logger = get_logger("security.config")


class SecurityConfig:
    """Security configuration for different environments."""

    # Environment settings
    ENVIRONMENT = settings.environment
    DEBUG = settings.debug

    # Supabase Configuration
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    # Plan Section 13: Feature Flags for Optimization Rollback
    USE_ASYNC_CLIENT = os.getenv("USE_ASYNC_CLIENT", "True").lower() == "true"
    ENABLE_CACHING = os.getenv("ENABLE_CACHING", "True").lower() == "true"
    ENABLE_RATE_LIMITING = os.getenv("ENABLE_RATE_LIMITING", "True").lower() == "true"
    ENABLE_RETRIES = os.getenv("ENABLE_RETRIES", "True").lower() == "true"

    # CORS Configuration
    CORS_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://0.0.0.0:5173",
        "http://0.0.0.0:5174",
        "http://0.0.0.0:3000",
        "http://0.0.0.0:8080",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://0.0.0.0:5175",
    ]

    if ENVIRONMENT == "production":
        # Production CORS should be explicit and environment-driven.
        CORS_ORIGINS = settings.cors_origin_list

    CORS_ALLOW_CREDENTIALS = True
    CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
    CORS_ALLOW_HEADERS = [
        "Authorization",
        "Content-Type",
        "Accept",
        "X-Correlation-ID",
        "X-Requested-With",
    ]

    # Regex to allow all localhost/local network URLs in development
    CORS_ORIGIN_REGEX = r"^https?://(localhost|127\.0\.0\.1|0\.0\.0\.0|192\.168\.\d+\.\d+|172\.1[6-9]\.\d+\.\d+|10\.\d+\.\d+\.\d+)(:\d+)?$"

    # Trusted host policy
    TRUSTED_HOSTS = settings.trusted_host_list

    # Content Security Policy
    @classmethod
    def get_csp_policy(cls) -> str:
        """Get Content Security Policy based on environment."""
        if cls.ENVIRONMENT == "development":
            return (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
                "img-src 'self' data: https: blob:; "
                "font-src 'self' data: https://fonts.gstatic.com; "
                "connect-src 'self' http://localhost:8000 http://127.0.0.1:8000 https://*.supabase.co https://*.supabase.in https://fonts.googleapis.com https://fonts.gstatic.com https://restcountries.com https://countriesnow.space; "
                "frame-src 'self' https://sketchfab.com; "
                "frame-ancestors 'self'; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "form-action 'self'; "
                "upgrade-insecure-requests"
            )
        else:
            # Production CSP - strict
            return (
                "default-src 'self'; "
                "script-src 'self' 'sha256-xyz123'; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "img-src 'self' data: https:; "
                "font-src 'self' https://fonts.gstatic.com; "
                "connect-src 'self' https://*.supabase.co https://fonts.googleapis.com https://fonts.gstatic.com; "
                "frame-src 'none'; "
                "frame-ancestors 'none'; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "form-action 'self'; "
                "upgrade-insecure-requests"
            )

    # Security Headers
    @classmethod
    def get_security_headers(cls) -> Dict[str, str]:
        """Get security headers based on environment."""
        headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": cls.get_csp_policy(),
        }

        if cls.ENVIRONMENT == "production":
            headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return headers

    # Authentication Settings
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = 24

    # Rate Limiting
    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "True").lower() == "true"
    RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds

    # Database Security
    DB_TIMEOUT = int(os.getenv("DB_TIMEOUT", "30"))  # seconds
    DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "20"))
    DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "30"))

    # Redis Configuration
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
    REDIS_SSL = os.getenv("REDIS_SSL", "False").lower() == "true"

    # Logging Security
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Error Handling
    EXPOSE_ERROR_DETAILS = DEBUG  # Only expose details in development

    # File Upload Security
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    ALLOWED_FILE_TYPES = [
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/gif",
        "text/plain",
        "application/json",
    ]

    # API Security
    API_VERSION = "v1"
    # Contract-first canonical prefix used by routers and OpenAPI.
    API_PREFIX = f"/{API_VERSION}"

    # Password reset redirect allow-list (host names only).
    PASSWORD_RESET_REDIRECT_ALLOWLIST = [
        host.strip().lower()
        for host in os.getenv(
            "PASSWORD_RESET_REDIRECT_ALLOWLIST",
            "localhost,127.0.0.1,biointellect.com,app.biointellect.com",
        ).split(",")
        if host.strip()
    ]

    @classmethod
    def validate(cls):
        """Validate all required configuration values."""
        required = {
            "SUPABASE_URL": cls.SUPABASE_URL,
            "SUPABASE_SERVICE_ROLE_KEY": cls.SUPABASE_SERVICE_ROLE_KEY,
        }

        missing = [key for key, value in required.items() if not value]
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}"
            )

        if not cls.SUPABASE_URL.startswith("https://"):
            raise ValueError("SUPABASE_URL must start with https://")

        if not cls.SUPABASE_SERVICE_ROLE_KEY.startswith("eyJ"):
            raise ValueError(
                "SUPABASE_SERVICE_ROLE_KEY format is invalid (expected JWT)"
            )

        if cls.ENVIRONMENT == "production" and not cls.CORS_ORIGINS:
            raise ValueError("CORS_ORIGINS is required in production")

        logger.info("Security configuration validated successfully")

    @classmethod
    def get_supabase_config(cls) -> Dict[str, str]:
        """Get Supabase configuration."""
        return {
            "url": cls.SUPABASE_URL,
            "anon_key": cls.SUPABASE_ANON_KEY,
            "service_role_key": cls.SUPABASE_SERVICE_ROLE_KEY,
        }

    @classmethod
    def get_security_config(cls) -> Dict[str, Any]:
        """Get complete security configuration."""
        return {
            "environment": cls.ENVIRONMENT,
            "debug": cls.DEBUG,
            "cors": {
                "origins": cls.CORS_ORIGINS,
                "allow_credentials": cls.CORS_ALLOW_CREDENTIALS,
                "allow_methods": cls.CORS_ALLOW_METHODS,
                "allow_headers": cls.CORS_ALLOW_HEADERS,
            },
            "trusted_hosts": cls.TRUSTED_HOSTS,
            "security_headers": cls.get_security_headers(),
            "rate_limiting": {
                "enabled": cls.RATE_LIMIT_ENABLED,
                "requests": cls.RATE_LIMIT_REQUESTS,
                "window": cls.RATE_LIMIT_WINDOW,
            },
            "database": {
                "timeout": cls.DB_TIMEOUT,
                "pool_size": cls.DB_POOL_SIZE,
                "max_overflow": cls.DB_MAX_OVERFLOW,
            },
            "logging": {
                "level": cls.LOG_LEVEL,
                "format": cls.LOG_FORMAT,
            },
            "error_handling": {
                "expose_details": cls.EXPOSE_ERROR_DETAILS,
            },
            "file_upload": {
                "max_size": cls.MAX_FILE_SIZE,
                "allowed_types": cls.ALLOWED_FILE_TYPES,
            },
        }


# Global security configuration instance
security_config = SecurityConfig()
