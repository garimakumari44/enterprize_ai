"""
Middleware package.

Contains all FastAPI application middleware components:
- CORS configuration
- Request tracing
- Logging
- Security headers
- Global exception handling
"""

from app.middleware.cors import add_cors_middleware
from app.middleware.logging import LoggingMiddleware
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.security import SecurityMiddleware
from app.middleware.error_handler import global_exception_handler


__all__ = [
    "add_cors_middleware",
    "LoggingMiddleware",
    "RequestIDMiddleware",
    "SecurityMiddleware",
    "global_exception_handler",
]