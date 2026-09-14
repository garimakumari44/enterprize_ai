"""
Document schemas.

These schemas define the application/API contract for documents.
They are intentionally separate from SQLAlchemy models.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DocumentStatus(str, Enum):
    """Lifecycle status of a document."""

    PENDING = "pending"
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DELETED = "deleted"


class DocumentCreate(BaseModel):
    """Input required to create a document record."""

    filename: str = Field(..., min_length=1, max_length=512)

    content_type: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    size_bytes: int = Field(
        ...,
        ge=0,
    )

    project_id: UUID | None = None


class DocumentUpdate(BaseModel):
    """Fields that can be updated after document creation."""

    filename: str | None = Field(
        default=None,
        min_length=1,
        max_length=512,
    )

    status: DocumentStatus | None = None

    metadata: dict | None = None


class DocumentResponse(BaseModel):
    """Public document representation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    filename: str
    content_type: str
    size_bytes: int

    checksum: str | None = None

    status: DocumentStatus

    storage_key: str | None = None

    project_id: UUID | None = None

    metadata: dict | None = None

    created_at: datetime
    updated_at: datetime


class DocumentUploadResult(BaseModel):
    """Result returned after successful object upload."""

    document: DocumentResponse

    storage_key: str

    checksum: str

    size_bytes: int