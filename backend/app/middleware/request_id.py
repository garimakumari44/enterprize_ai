"""
Request ID middleware.

Creates a unique identifier for every incoming request.

Used for:
- Request tracing
- Logging correlation
- Debugging
- Future distributed tracing
"""

import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that attaches a unique request ID
    to every HTTP request.
    """

    async def dispatch(
        self,
        request: Request,
        call_next,
    ) -> Response:
        """
        Process incoming request.

        Args:
            request:
                Incoming HTTP request.

            call_next:
                Next middleware or route handler.

        Returns:
            HTTP response with request ID attached.
        """

        # Generate unique request identifier
        request_id = str(uuid.uuid4())

        # Store request ID for access in routes/services
        request.state.request_id = request_id

        # Continue request processing
        response = await call_next(request)

        # Add request ID to response headers
        response.headers[
            "X-Request-ID"
        ] = request_id

        return response