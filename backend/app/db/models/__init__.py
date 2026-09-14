"""
app/db/models/__init__.py

Central SQLAlchemy model registry.

Every SQLAlchemy ORM model must be imported here so that all
tables are registered with Base.metadata.

Alembic should import this module before reading Base.metadata.
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

from app.db.database import Base


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

from app.db.models.user import (
    User,
)


# ---------------------------------------------------------------------------
# Assistant
# ---------------------------------------------------------------------------

from app.db.models.assistant import (
    AssistantSession,
    AssistantMessage,
)


# ---------------------------------------------------------------------------
# AI Providers / Secrets
# ---------------------------------------------------------------------------

from app.db.models.ai_provider import (
    AIProvider,
)

from app.db.models.ai_secret import (
    AISecret,
)


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------

from app.db.models.document import (
    Document,
    document_tags,
)

from app.db.models.document_version import (
    DocumentVersion,
)

from app.db.models.chunk import (
    Chunk,
)

from app.db.models.document_chunk_vector import (
    DocumentChunkVector,
)


# ---------------------------------------------------------------------------
# Folders / Tags
# ---------------------------------------------------------------------------

from app.db.models.folder import (
    Folder,
)

from app.db.models.tag import (
    Tag,
)


# ---------------------------------------------------------------------------
# Processing
# ---------------------------------------------------------------------------

from app.db.models.processing_job import (
    ProcessingJob,
)

from app.db.models.processing_step import (
    ProcessingStep,
)


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------

from app.db.models.extraction_result import (
    ExtractionResult,
)

from app.db.models.extracted_field import (
    ExtractedField,
)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

from app.db.models.validation_result import (
    ValidationResult,
)


# ---------------------------------------------------------------------------
# Human Review
# ---------------------------------------------------------------------------

from app.db.models.review_record import (
    ReviewRecord,
)


# ---------------------------------------------------------------------------
# Document Intelligence
# ---------------------------------------------------------------------------

from app.db.models.document_intelligence_result import (
    DocumentIntelligenceResult,
)


# ---------------------------------------------------------------------------
# Workflow
# ---------------------------------------------------------------------------

from app.db.models.workflow import (
    Workflow,
)

from app.db.models.workflow_step import (
    WorkflowStep,
)


# ---------------------------------------------------------------------------
# Public exports
# ---------------------------------------------------------------------------

__all__ = [
    # Base
    "Base",

    # Authentication
    "User",

    # Assistant
    "AssistantSession",
    "AssistantMessage",

    # AI Providers / Secrets
    "AIProvider",
    "AISecret",

    # Documents
    "Document",
    "DocumentVersion",
    "Chunk",
    "DocumentChunkVector",
    "document_tags",

    # Organization
    "Folder",
    "Tag",

    # Processing
    "ProcessingJob",
    "ProcessingStep",

    # Extraction
    "ExtractionResult",
    "ExtractedField",

    # Validation
    "ValidationResult",

    # Human Review
    "ReviewRecord",

    # Document Intelligence
    "DocumentIntelligenceResult",

    # Workflow
    "Workflow",
    "WorkflowStep",
]