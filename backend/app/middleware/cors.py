"""
CORS middleware configuration.

Allows communication between:
- Next.js frontend
- FastAPI backend

Configured for development environment.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def add_cors_middleware(app: FastAPI) -> None:
    """
    Add CORS support to FastAPI application.

    Args:
        app:
            FastAPI application instance.
    """

    app.add_middleware(
        CORSMiddleware,

        # Frontend applications allowed to access API
        allow_origins=[
            "http://localhost:3000",
        ],

        # Allow cookies and authentication headers
        allow_credentials=True,

        # Allow all HTTP methods
        allow_methods=[
            "*",
        ],

        # Allow all request headers
        allow_headers=[
            "*",
        ],
    )