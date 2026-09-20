
"""
CORS middleware configuration.

Allows communication between:
- Next.js frontend
- FastAPI backend

CORS origins are loaded from application settings so the same
implementation works in both development and production.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings


def add_cors_middleware(app: FastAPI) -> None:
    """
    Add CORS support to the FastAPI application.

    CORS origins are controlled by the BACKEND_CORS_ORIGINS
    environment setting.

    Development example:
        BACKEND_CORS_ORIGINS=["http://localhost:3000"]

    Production example:
        BACKEND_CORS_ORIGINS=["https://enterprize-ai.vercel.app"]

    Args:
        app:
            FastAPI application instance.
    """

    app.add_middleware(
        CORSMiddleware,

        # Frontend applications allowed to access the API.
        # Loaded from environment/application configuration.
        allow_origins=settings.BACKEND_CORS_ORIGINS,

        # Allow cookies and authentication headers.
        allow_credentials=True,

        # Allow all HTTP methods.
        allow_methods=[
            "*",
        ],

        # Allow all request headers.
        allow_headers=[
            "*",
        ],
    )

