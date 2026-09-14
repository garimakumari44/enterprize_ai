"""
app/core/constants.py

Application-wide constants.

Do not place mutable runtime state here.
Use configuration/environment variables for
deployment-specific values.
"""

from __future__ import annotations

from enum import StrEnum


# ============================================================================
# Application
# ============================================================================

APP_NAME = "Enterprise AI Platform"
APP_VERSION = "1.0.0"
API_VERSION = "v1"


# ============================================================================
# Environment
# ============================================================================


class Environment(StrEnum):
    """Supported application environments."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


# ============================================================================
# Document Processing
# ============================================================================


class DocumentStatus(StrEnum):
    """Lifecycle states of a document."""

    CREATED = "created"
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    DELETED = "deleted"


class ProcessingStatus(StrEnum):
    """Lifecycle states of a processing job."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProcessingStage(StrEnum):
    """
    Canonical stages of the document-intelligence pipeline.

    This enum is the single source of truth for processing-stage
    identifiers throughout the application.

    Canonical pipeline:

        classification
            ↓
        layout_analysis
            ↓
        text_extraction
            ↓
        ocr
            ↓
        structure_detection
            ↓
        cleaning
            ↓
        chunking
            ↓
        metadata_enrichment
            ↓
        embedding
            ↓
        indexing

    Do not create duplicate processing-stage constants elsewhere.
    """

    CLASSIFICATION = "classification"

    LAYOUT_ANALYSIS = "layout_analysis"

    TEXT_EXTRACTION = "text_extraction"

    OCR = "ocr"

    STRUCTURE_DETECTION = "structure_detection"

    CLEANING = "cleaning"

    CHUNKING = "chunking"

    METADATA_ENRICHMENT = "metadata_enrichment"

    EMBEDDING = "embedding"

    INDEXING = "indexing"


# ============================================================================
# Storage
# ============================================================================


class StorageBackend(StrEnum):
    """Supported object-storage backends."""

    LOCAL = "local"
    S3 = "s3"
    MINIO = "minio"


# ============================================================================
# Retrieval
# ============================================================================


class RetrievalStrategy(StrEnum):
    """Supported retrieval strategies."""

    DENSE = "dense"
    SPARSE = "sparse"
    HYBRID = "hybrid"
    BM25 = "bm25"


# ============================================================================
# Pagination
# ============================================================================

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


# ============================================================================
# Chunking
# ============================================================================

DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 120


# ============================================================================
# Retrieval Limits
# ============================================================================

DEFAULT_TOP_K = 10
MAX_TOP_K = 100


# ============================================================================
# File Handling
# ============================================================================

DEFAULT_MAX_FILE_SIZE_MB = 100

ALLOWED_DOCUMENT_EXTENSIONS = frozenset(
    {
        ".pdf",
        ".doc",
        ".docx",
        ".txt",
        ".md",
        ".csv",
        ".json",
        ".html",
        ".htm",
    }
)


# ============================================================================
# HTTP
# ============================================================================

HEALTH_ENDPOINT = "/health"
API_PREFIX = "/api/v1"


# ============================================================================
# Public API
# ============================================================================

__all__ = [
    # Application
    "APP_NAME",
    "APP_VERSION",
    "API_VERSION",

    # Environment
    "Environment",

    # Document processing
    "DocumentStatus",
    "ProcessingStatus",
    "ProcessingStage",

    # Storage
    "StorageBackend",

    # Retrieval
    "RetrievalStrategy",

    # Pagination
    "DEFAULT_PAGE",
    "DEFAULT_PAGE_SIZE",
    "MAX_PAGE_SIZE",

    # Chunking
    "DEFAULT_CHUNK_SIZE",
    "DEFAULT_CHUNK_OVERLAP",

    # Retrieval limits
    "DEFAULT_TOP_K",
    "MAX_TOP_K",

    # File handling
    "DEFAULT_MAX_FILE_SIZE_MB",
    "ALLOWED_DOCUMENT_EXTENSIONS",

    # HTTP
    "HEALTH_ENDPOINT",
    "API_PREFIX",
]