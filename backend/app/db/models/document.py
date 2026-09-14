"""
app/db/models/document.py

Canonical logical document model.

A Document represents the logical identity of a document.

The actual uploaded artifact is represented by DocumentVersion.

Architecture:

    Document
        |
        +── DocumentVersion v1
        |
        +── DocumentVersion v2
        |
        +── DocumentVersion v3
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    String,
    Table,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.database  import Base


if TYPE_CHECKING:
    from app.db.models.document_version import DocumentVersion
    from app.db.models.tag import Tag


# ============================================================================
# Document ↔ Tag association
# ============================================================================

document_tags = Table(
    "document_tags",
    Base.metadata,
    Column(
        "document_id",
        UUID(as_uuid=True),
        ForeignKey(
            "documents.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),
    Column(
        "tag_id",
        UUID(as_uuid=True),
        ForeignKey(
            "tags.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),
)


# ============================================================================
# Document
# ============================================================================


class Document(Base):
    """
    Logical document identity.

    This table does NOT store the physical uploaded file.

    Physical file information belongs to DocumentVersion.
    """

    __tablename__ = "documents"

    # ------------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------------

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ------------------------------------------------------------------------
    # Logical document information
    # ------------------------------------------------------------------------

    name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    document_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="active",
        server_default="active",
        index=True,
    )

    # ------------------------------------------------------------------------
    # Current version
    # ------------------------------------------------------------------------

    current_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "document_versions.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    # ------------------------------------------------------------------------
    # Application metadata
    # ------------------------------------------------------------------------

    metadata_: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
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

    versions: Mapped[list["DocumentVersion"]] = relationship(
        "DocumentVersion",
        back_populates="document",
        foreign_keys="DocumentVersion.document_id",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="DocumentVersion.version_number",
    )

    tags: Mapped[list["Tag"]] = relationship(
        secondary=document_tags,
        back_populates="documents",
        cascade="save-update",
    )

    def __repr__(self) -> str:
        return (
            f"<Document("
            f"id={self.id!r}, "
            f"name={self.name!r}, "
            f"status={self.status!r}"
            f")>"
        )