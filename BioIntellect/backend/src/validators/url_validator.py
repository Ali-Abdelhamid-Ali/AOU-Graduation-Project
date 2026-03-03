"""URL Validation Utilities for Security."""

from urllib.parse import urlparse
from src.security.config import security_config

# Allowed domains for open redirect prevention
# In production, this should be strictly controlled
ALLOWED_DOMAINS = {
    "localhost",
    "127.0.0.1",
    "biointellect.com",  # Example production domain
    "app.biointellect.com",
}


def validate_safe_redirect_url(url: str) -> bool:
    """
    Validates if a URL is safe for redirection.
    1. Must be absolute or relative path.
    2. If absolute, host must be in ALLOWED_DOMAINS.
    """
    if not url:
        return False

    try:
        parsed = urlparse(url.strip())

        # Relative redirects are allowed only for rooted local paths.
        if not parsed.netloc:
            return parsed.path.startswith("/") and not parsed.path.startswith("//")

        # If absolute, check hostname
        hostname = parsed.hostname
        if not hostname:
            return False
        hostname = hostname.lower()

        if parsed.scheme not in {"http", "https"}:
            return False

        if parsed.username or parsed.password:
            return False

        # Check against allowed list and CORS origins
        if (
            hostname in ALLOWED_DOMAINS
            or hostname in security_config.PASSWORD_RESET_REDIRECT_ALLOWLIST
        ):
            return True

        # Also allow if it matches any CORS origin host (helper for dev)
        for origin in security_config.CORS_ORIGINS:
            origin_parsed = urlparse(origin)
            if (origin_parsed.hostname or "").lower() == hostname:
                return True

        return False

    except Exception:
        return False

