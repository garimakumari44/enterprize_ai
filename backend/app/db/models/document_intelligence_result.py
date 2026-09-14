"""
app/db/models/document_intelligence_result.py

Persisted business-level intelligence produced from a processed document.

ProcessingJob / ProcessingStep track HOW a document was processed.

DocumentIntelligenceResult stores WHAT was learned from the document.

Provider-specific output must NOT be persisted directly here.
Provider output should first be normalized into ProcessingContext and
then mapped into this model by result_mapper.py.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DocumentIntelligenceResult(Base):
    """
    Canonical business intelligence produced from one processing job.

    A ProcessingJob produces at most one final intelligence result.

    This model intentionally contains canonical application-level data
    rather than provider-specific response structures.
    """

    __tablename__ = "document_intelligence_results"

    # ------------------------------------------------------------------
    # Primary key
    # ------------------------------------------------------------------

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ------------------------------------------------------------------
    # Processing job
    # ------------------------------------------------------------------

    processing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "processing_jobs.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
    )

    # ------------------------------------------------------------------
    # Document
    # ------------------------------------------------------------------

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "documents.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Document version
    # ------------------------------------------------------------------

    document_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "document_versions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------

    document_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    classification_confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Canonical structured business intelligence
    # ------------------------------------------------------------------

    structured_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    validation_results: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    # ------------------------------------------------------------------
    # Generated artifacts
    # ------------------------------------------------------------------

    artifacts: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    # ------------------------------------------------------------------
    # Knowledge representation
    # ------------------------------------------------------------------

    knowledge: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    # ------------------------------------------------------------------
    # Raw extracted text
    # ------------------------------------------------------------------

    raw_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Timestamps
    # ------------------------------------------------------------------

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    review_records: Mapped[list["ReviewRecord"]] = relationship(
        "ReviewRecord",
        back_populates="intelligence_result",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    # ------------------------------------------------------------------
    # Constraints / indexes
    # ------------------------------------------------------------------

    __table_args__ = (
        CheckConstraint(
            """
            classification_confidence IS NULL
            OR (
                classification_confidence >= 0
                AND classification_confidence <= 1
            )
            """,
            name="ck_document_intelligence_classification_confidence",
        ),
        Index(
            "ix_document_intelligence_results_document_id",
            "document_id",
        ),
        Index(
            "ix_document_intelligence_results_document_version_id",
            "document_version_id",
        ),
    )

    # ------------------------------------------------------------------
    # Representation
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            "<DocumentIntelligenceResult("
            f"id={self.id}, "
            f"document_id={self.document_id}, "
            f"document_version_id={self.document_version_id}, "
            f"document_type={self.document_type!r}, "
            f"classification_confidence="
            f"{self.classification_confidence!r}"
            ")>"
        )


__all__ = [
    "DocumentIntelligenceResult",
]