"""
app/db/models/document_version.py

Immutable uploaded artifact version.

A Document can have multiple versions:

    Document
        ├── Version 1
        ├── Version 2
        └── Version 3

Processing always operates on exactly one DocumentVersion.

DocumentVersion stores:
    - original file identity
    - object-storage location
    - checksum
    - processing state
    - logical/extracted metadata
    - relationships to processing jobs and chunks
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database  import Base


if TYPE_CHECKING:
    from app.db.models.chunk import Chunk
    from app.db.models.document import Document
    from app.db.models.processing_job import ProcessingJob


class DocumentVersion(Base):
    """
    Represents one uploaded document artifact.

    A DocumentVersion is the exact artifact that a processing job operates
    on. Each version belongs to one logical Document.
    """

    __tablename__ = "document_versions"

    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "version_number",
            name="uq_document_version_number",
        ),
    )

    # ==================================================================
    # Identity
    # ==================================================================

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    document_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "documents.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # ==================================================================
    # Original file
    # ==================================================================

    original_filename: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )

    mime_type: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    file_size: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    checksum: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        index=True,
    )

    # ==================================================================
    # Object storage
    # ==================================================================

    storage_provider: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="minio",
        server_default="minio",
    )

    object_storage_bucket: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    object_storage_key: Mapped[str] = mapped_column(
        String(2000),
        nullable=False,
    )

    # ==================================================================
    # Processing state
    # ==================================================================

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="uploaded",
        server_default="uploaded",
        index=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ==================================================================
    # Extracted / logical metadata
    # ==================================================================

    page_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    detected_language: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    metadata_: Mapped[dict] = mapped_column(
        "metadata",
        MutableDict.as_mutable(JSONB),
        nullable=False,
        default=dict,
        server_default="{}",
    )

    # ==================================================================
    # Timestamps
    # ==================================================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # ==================================================================
    # Relationships
    # ==================================================================

    document: Mapped["Document"] = relationship(
        "Document",
        back_populates="versions",
        foreign_keys=[document_id],
    )

    processing_jobs: Mapped[list["ProcessingJob"]] = relationship(
        "ProcessingJob",
        back_populates="document_version",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ProcessingJob.created_at",
    )

    chunks: Mapped[list["Chunk"]] = relationship(
        "Chunk",
        back_populates="document_version",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Chunk.chunk_index",
    )

    # ==================================================================
    # Representation
    # ==================================================================

    def __repr__(self) -> str:
        return (
            f"<DocumentVersion("
            f"id={self.id!r}, "
            f"document_id={self.document_id!r}, "
            f"version_number={self.version_number}, "
            f"status={self.status!r}"
            f")>"
        )


__all__ = [
    "DocumentVersion",
]