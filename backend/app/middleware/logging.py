"""
Request logging middleware.

Tracks incoming API requests and response information.

Captures:
- HTTP method
- Endpoint path
- Status code
- Processing time
- Request ID
"""

import logging
import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


logger = logging.getLogger(
    "api.request"
)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for API request logging.
    """

    async def dispatch(
        self,
        request: Request,
        call_next,
    ) -> Response:
        """
        Process and log HTTP requests.

        Args:
            request:
                Incoming request.

            call_next:
                Next middleware or route handler.

        Returns:
            Response object.
        """

        start_time = time.perf_counter()


        response = await call_next(
            request
        )


        process_time = (
            time.perf_counter()
            -
            start_time
        )


        request_id = getattr(
            request.state,
            "request_id",
            None,
        )


        logger.info(
            {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(
                    process_time * 1000,
                    2,
                ),
            }
        )


        return response