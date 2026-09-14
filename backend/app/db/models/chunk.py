"""
app/db/models/chunk.py

Document chunk model.

A Chunk represents a semantically meaningful piece of a processed
DocumentVersion.

Chunking happens after:

    classification
        ↓
    layout analysis
        ↓
    OCR / native extraction
        ↓
    structure detection
        ↓
    normalization
        ↓
    semantic chunking

Chunks are then used for:

    embeddings
        ↓
    vector search
        ↓
    hybrid retrieval
        ↓
    RAG
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


# ============================================================================
# TYPE CHECKING
# ============================================================================

if TYPE_CHECKING:
    from app.db.models.document_version import DocumentVersion
    from app.db.models.embedding import Embedding


# ============================================================================
# CHUNK MODEL
# ============================================================================

class Chunk(Base):
    """
    Semantic document chunk.

    A Chunk belongs to exactly one DocumentVersion.

    A Chunk may optionally have one Embedding metadata record.

    The actual vector is stored separately in:

        document_chunk_vectors

    This model stores the canonical textual representation and
    metadata required for retrieval and RAG.
    """

    __tablename__ = "document_chunks"

    # ------------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------------

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    document_version_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "document_versions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------------------
    # Chunk ordering / hierarchy
    # ------------------------------------------------------------------------

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    parent_chunk_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "document_chunks.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    chunk_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="text",
        server_default="text",
        index=True,
    )

    # ------------------------------------------------------------------------
    # Content
    # ------------------------------------------------------------------------

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    normalized_content: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    token_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    character_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # ------------------------------------------------------------------------
    # Document location
    # ------------------------------------------------------------------------

    page_start: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    page_end: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    section_title: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    section_path: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # ------------------------------------------------------------------------
    # Semantic metadata
    # ------------------------------------------------------------------------

    metadata_: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    entities: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    keywords: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # ------------------------------------------------------------------------
    # Embedding / indexing state
    # ------------------------------------------------------------------------

    embedding_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        server_default="pending",
        index=True,
    )

    embedding_model: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    embedding_dimensions: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    indexed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        index=True,
    )

    # ------------------------------------------------------------------------
    # Timestamps
    # ------------------------------------------------------------------------

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

    # ------------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------------

    document_version: Mapped["DocumentVersion"] = relationship(
        "DocumentVersion",
        back_populates="chunks",
    )

    # One-to-one relationship:
    #
    # document_chunks.id
    #        ↓
    # embeddings.chunk_id
    #
    # Embedding.chunk_id is UNIQUE, therefore a Chunk can have
    # at most one Embedding metadata record.
    embedding: Mapped["Embedding | None"] = relationship(
        "Embedding",
        back_populates="chunk",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # ------------------------------------------------------------------------
    # Parent / child chunk hierarchy
    # ------------------------------------------------------------------------

    parent: Mapped["Chunk | None"] = relationship(
        "Chunk",
        remote_side="Chunk.id",
        back_populates="children",
    )

    children: Mapped[list["Chunk"]] = relationship(
        "Chunk",
        back_populates="parent",
        cascade="save-update",
    )

    # ------------------------------------------------------------------------
    # Representation
    # ------------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"<Chunk("
            f"id={self.id!r}, "
            f"document_version_id={self.document_version_id!r}, "
            f"chunk_index={self.chunk_index}, "
            f"chunk_type={self.chunk_type!r}"
            f")>"
        )