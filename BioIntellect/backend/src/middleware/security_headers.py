"""Security Headers Middleware for BioIntellect."""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable

from src.security.config import security_config


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.
    Handles CSP frame-ancestors and X-Frame-Options directives properly via HTTP headers.
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.config = security_config.get_security_config()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers from configuration
        security_headers = self.config["security_headers"]
        
        for header, value in security_headers.items():
            response.headers[header] = value
        
        # Set CSP from configuration
        response.headers["Content-Security-Policy"] = self.config["security_headers"]["Content-Security-Policy"]
        
        # Remove server header for security
        if "server" in response.headers:
            del response.headers["server"]
        
        return response
