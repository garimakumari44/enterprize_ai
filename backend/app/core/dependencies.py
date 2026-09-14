"""
app/core/dependencies.py

Application dependencies.

This module is responsible for wiring infrastructure and
application services into FastAPI endpoints.

Architecture:

    API
     |
     +--> Authentication
     |       |
     |       v
     |   Sync Session
     |
     +--> DocumentService
             |
             v
        AsyncSession
             |
             v
        StorageService
             |
             v
        StorageProvider
             |
             v
        MinIOProvider
"""

from functools import lru_cache
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security import security, verify_access_token
from app.db.session import get_async_db, get_db
from app.db.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.documents.document_service import DocumentService
from app.storage.minio import MinIOProvider
from app.storage.service import StorageService


# ============================================================================
# Settings
# ============================================================================


@lru_cache
def get_app_settings() -> Settings:
    """
    Return the application settings singleton.

    Settings are cached so the same configuration object
    is reused throughout the application process.
    """

    return get_settings()


# ============================================================================
# Storage Provider
# ============================================================================


@lru_cache
def get_storage_provider() -> MinIOProvider:
    """
    Create and return the MinIO storage provider.

    The provider is infrastructure-level code and is shared
    rather than recreated for every request.

    Returns:
        MinIOProvider: Configured MinIO storage provider.

    Raises:
        RuntimeError: If storage configuration is invalid.
    """

    settings = get_app_settings()

    # ------------------------------------------------------------------------
    # Validate storage backend
    # ------------------------------------------------------------------------

    storage_backend = (
        settings.STORAGE_BACKEND
        or ""
    ).lower().strip()

    if storage_backend != "minio":
        raise RuntimeError(
            "Unsupported storage backend: "
            f"{settings.STORAGE_BACKEND!r}. "
            "Expected 'minio'."
        )

    # ------------------------------------------------------------------------
    # Validate MinIO endpoint
    # ------------------------------------------------------------------------

    if not settings.MINIO_ENDPOINT:
        raise RuntimeError(
            "MINIO_ENDPOINT is required when "
            "STORAGE_BACKEND='minio'."
        )

    # ------------------------------------------------------------------------
    # Validate MinIO access key
    # ------------------------------------------------------------------------

    if not settings.MINIO_ACCESS_KEY:
        raise RuntimeError(
            "MINIO_ACCESS_KEY is required when "
            "STORAGE_BACKEND='minio'."
        )

    # ------------------------------------------------------------------------
    # Validate MinIO secret key
    # ------------------------------------------------------------------------

    if not settings.MINIO_SECRET_KEY:
        raise RuntimeError(
            "MINIO_SECRET_KEY is required when "
            "STORAGE_BACKEND='minio'."
        )

    # ------------------------------------------------------------------------
    # Validate storage bucket
    # ------------------------------------------------------------------------

    if not settings.STORAGE_BUCKET:
        raise RuntimeError(
            "STORAGE_BUCKET cannot be empty."
        )

    # ------------------------------------------------------------------------
    # Create MinIO provider
    # ------------------------------------------------------------------------

    return MinIOProvider(
        endpoint_url=settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        bucket=settings.STORAGE_BUCKET,
        region=settings.MINIO_REGION,
        secure=settings.MINIO_SECURE,
    )


# ============================================================================
# Storage Service
# ============================================================================


@lru_cache
def get_storage_service() -> StorageService:
    """
    Create the application-facing storage service.

    StorageService hides the concrete storage provider
    from the rest of the application.

    The bucket is passed explicitly because StorageService
    requires it as a keyword-only constructor argument.

    Returns:
        StorageService: Configured application storage service.

    Raises:
        RuntimeError: If storage configuration is invalid.
    """

    settings = get_app_settings()
    provider = get_storage_provider()

    return StorageService(
        provider=provider,
        bucket=settings.STORAGE_BUCKET,
    )


# ============================================================================
# Document Service
# ============================================================================


def get_document_service(
    db: AsyncSession = Depends(get_async_db),
    storage_service: StorageService = Depends(
        get_storage_service
    ),
) -> DocumentService:
    """
    Create a request-scoped DocumentService.

    DocumentService uses AsyncSession, so it receives the
    asynchronous database dependency.

    Storage infrastructure is shared through the cached
    StorageService dependency.
    """

    return DocumentService(
        session=db,
        storage=storage_service,
    )


# ============================================================================
# Current User
# ============================================================================


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),
    db: Session = Depends(get_db),
) -> User:
    """
    Return the currently authenticated user.

    Authentication continues using the existing synchronous
    SQLAlchemy session.

    Args:
        credentials: Bearer authentication credentials.
        db: Synchronous SQLAlchemy session.

    Returns:
        User: Authenticated user.

    Raises:
        HTTPException: If the token is invalid, the user does
        not exist, or the account is inactive.
    """

    # ------------------------------------------------------------------------
    # Verify access token
    # ------------------------------------------------------------------------

    try:
        payload = verify_access_token(
            credentials.credentials
        )

        user_id = UUID(
            payload["sub"]
        )

    except (
        JWTError,
        ValueError,
        KeyError,
        TypeError,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    # ------------------------------------------------------------------------
    # Load user
    # ------------------------------------------------------------------------

    repository = UserRepository(db)

    user = repository.get_by_id(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    # ------------------------------------------------------------------------
    # Validate account status
    # ------------------------------------------------------------------------

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled.",
        )

    return user


# ============================================================================
# Current Active User
# ============================================================================


def get_current_active_user(
    current_user: User = Depends(
        get_current_user
    ),
) -> User:
    """
    Return the authenticated active user.

    This dependency exists as an explicit semantic layer
    for endpoints that require an active account.
    """

    return current_user