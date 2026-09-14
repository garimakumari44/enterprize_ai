"""
app/db/models/embedding.py

Embedding metadata associated with a document chunk.

The actual embedding vector is stored in:

    document_chunk_vectors

This model stores the metadata and one-to-one association between
a Chunk and its generated embedding.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


if TYPE_CHECKING:
    from app.db.models.chunk import Chunk


class Embedding(Base):
    """
    Embedding metadata for a document chunk.

    One Chunk can have at most one Embedding metadata record.

    The actual vector is stored separately in
    document_chunk_vectors.
    """

    __tablename__ = "embeddings"

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    # ------------------------------------------------------------------
    # Source chunk
    # ------------------------------------------------------------------

    chunk_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "document_chunks.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
        index=True,
    )

    # ------------------------------------------------------------------
    # Embedding configuration
    # ------------------------------------------------------------------

    model: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="BAAI/bge-small-en-v1.5",
        server_default="BAAI/bge-small-en-v1.5",
    )

    dimension: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=384,
        server_default="384",
    )

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    # ------------------------------------------------------------------
    # Timestamps
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    chunk: Mapped["Chunk"] = relationship(
        "Chunk",
        back_populates="embedding",
        uselist=False,
        lazy="selectin",
    )

    # ------------------------------------------------------------------
    # Representation
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"<Embedding("
            f"id={self.id!r}, "
            f"chunk_id={self.chunk_id!r}, "
            f"model={self.model!r}, "
            f"dimension={self.dimension!r}"
            f")>"
        )