"""
Global exception handler.

Provides centralized error handling
for FastAPI application.

Handles:
- Unexpected exceptions
- Error logging
- Consistent API responses
"""

import logging

from fastapi import Request
from fastapi.responses import JSONResponse


logger = logging.getLogger(
    "application.error"
)


async def global_exception_handler(
    request: Request,
    exc: Exception,
):
    """
    Handle unexpected application errors.

    Args:
        request:
            Incoming HTTP request.

        exc:
            Raised exception.

    Returns:
        JSON error response.
    """

    request_id = getattr(
        request.state,
        "request_id",
        None,
    )


    # Log complete error internally
    logger.exception(
        {
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "error": str(exc),
        }
    )


    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "request_id": request_id,
        },
    )