"""
Security middleware.

Adds HTTP security headers to API responses.

Provides basic protection against:
- Clickjacking
- MIME sniffing
- Browser XSS attacks
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Adds security-related HTTP headers.
    """

    async def dispatch(
        self,
        request: Request,
        call_next,
    ) -> Response:
        """
        Process request and attach security headers.

        Args:
            request:
                Incoming HTTP request.

            call_next:
                Next middleware or route handler.

        Returns:
            HTTP response.
        """

        response = await call_next(
            request
        )

        # Prevent browsers from guessing content types
        response.headers[
            "X-Content-Type-Options"
        ] = "nosniff"


        # Prevent page embedding inside iframes
        response.headers[
            "X-Frame-Options"
        ] = "DENY"


        # Enable browser XSS protection
        response.headers[
            "X-XSS-Protection"
        ] = "1; mode=block"


        # Control referrer information
        response.headers[
            "Referrer-Policy"
        ] = "strict-origin-when-cross-origin"


        return response