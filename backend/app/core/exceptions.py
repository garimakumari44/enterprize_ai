"""
app/core/exceptions.py

Application exception hierarchy.

Architecture:

    AppException
        |
        +-- ConfigurationError
        +-- ValidationError
        +-- NotFoundError
        +-- StorageError
        +-- DocumentError
        +-- ProcessingError
        +-- ProviderError
        +-- RetrievalError
        +-- AuthenticationError
        +-- AuthorizationError
"""

from __future__ import annotations


class AppException(Exception):
    """
    Base exception for all expected application errors.
    """

    code: str = "APP_ERROR"
    status_code: int = 500

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)

        self.message = message

        if code is not None:
            self.code = code

        if status_code is not None:
            self.status_code = status_code

    def __str__(self) -> str:
        return self.message


# ============================================================================
# Configuration
# ============================================================================


class ConfigurationError(AppException):
    """Raised when application configuration is invalid."""

    code = "CONFIGURATION_ERROR"
    status_code = 500


# ============================================================================
# Validation
# ============================================================================


class ValidationError(AppException):
    """Raised when application-level validation fails."""

    code = "VALIDATION_ERROR"
    status_code = 400


# ============================================================================
# Authentication / Authorization
# ============================================================================


class AuthenticationError(AppException):
    """Raised when authentication fails."""

    code = "AUTHENTICATION_ERROR"
    status_code = 401


class AuthorizationError(AppException):
    """Raised when a user lacks permission."""

    code = "AUTHORIZATION_ERROR"
    status_code = 403


# ============================================================================
# Resource errors
# ============================================================================


class NotFoundError(AppException):
    """Raised when a requested resource does not exist."""

    code = "NOT_FOUND"
    status_code = 404


class ConflictError(AppException):
    """Raised when an operation conflicts with current state."""

    code = "CONFLICT"
    status_code = 409


# ============================================================================
# Document errors
# ============================================================================


class DocumentError(AppException):
    """Base exception for document-related failures."""

    code = "DOCUMENT_ERROR"
    status_code = 400


class DocumentNotFoundError(DocumentError):
    """Raised when a document cannot be found."""

    code = "DOCUMENT_NOT_FOUND"
    status_code = 404


class UnsupportedDocumentTypeError(DocumentError):
    """Raised when a document type is unsupported."""

    code = "UNSUPPORTED_DOCUMENT_TYPE"
    status_code = 415


class DocumentTooLargeError(DocumentError):
    """Raised when a document exceeds the configured size limit."""

    code = "DOCUMENT_TOO_LARGE"
    status_code = 413


# ============================================================================
# Storage
# ============================================================================


class StorageError(AppException):
    """Base exception for storage failures."""

    code = "STORAGE_ERROR"
    status_code = 500


class StorageUploadError(StorageError):
    """Raised when an object cannot be uploaded."""

    code = "STORAGE_UPLOAD_ERROR"


class StorageDownloadError(StorageError):
    """Raised when an object cannot be downloaded."""

    code = "STORAGE_DOWNLOAD_ERROR"


class StorageDeleteError(StorageError):
    """Raised when an object cannot be deleted."""

    code = "STORAGE_DELETE_ERROR"


class StorageNotFoundError(StorageError):
    """Raised when an object does not exist."""

    code = "STORAGE_NOT_FOUND"
    status_code = 404


# ============================================================================
# Processing
# ============================================================================


class ProcessingError(AppException):
    """Base exception for document-processing failures."""

    code = "PROCESSING_ERROR"
    status_code = 500


class ProcessingNotFoundError(ProcessingError):
    """Raised when a processing job does not exist."""

    code = "PROCESSING_NOT_FOUND"
    status_code = 404


class ProcessingAlreadyRunningError(ProcessingError):
    """Raised when processing is already active."""

    code = "PROCESSING_ALREADY_RUNNING"
    status_code = 409


class ProcessingCancelledError(ProcessingError):
    """Raised when processing is cancelled."""

    code = "PROCESSING_CANCELLED"
    status_code = 409


# ============================================================================
# Providers
# ============================================================================


class ProviderError(AppException):
    """
    Base exception for external/internal providers.

    Examples:

        OCR provider
        Embedding provider
        LLM provider
        Storage provider
    """

    code = "PROVIDER_ERROR"
    status_code = 502


class ProviderUnavailableError(ProviderError):
    """Raised when a provider is unavailable."""

    code = "PROVIDER_UNAVAILABLE"
    status_code = 503


class ProviderConfigurationError(ProviderError):
    """Raised when a provider is incorrectly configured."""

    code = "PROVIDER_CONFIGURATION_ERROR"
    status_code = 500


# ============================================================================
# Retrieval
# ============================================================================


class RetrievalError(AppException):
    """Base exception for retrieval failures."""

    code = "RETRIEVAL_ERROR"
    status_code = 500


class RetrievalUnavailableError(RetrievalError):
    """Raised when retrieval infrastructure is unavailable."""

    code = "RETRIEVAL_UNAVAILABLE"
    status_code = 503