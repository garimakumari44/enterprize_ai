"""
app/db/models/extraction_result.py

Persisted document extraction result.

An ExtractionResult represents the structured extraction produced during
a processing job for a specific document version.

Relationship:

    ProcessingJob
         |
         v
    ExtractionResult
         |
         +---- ExtractedField
         +---- ExtractedField
         +---- ExtractedField

Architecture notes
------------------

ExtractionResult stores canonical extraction information.

It must remain independent of specific extraction providers such as:

    - PaddleOCR
    - Tesseract
    - LLM providers
    - cloud document intelligence providers

Provider-specific output is normalized by ResultMapper before persistence.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ExtractionResult(Base):
    """
    Persisted canonical document extraction result.

    One result belongs to:

        - one document
        - one document version
        - one processing job

    An ExtractionResult can contain multiple ExtractedField records.
    """

    __tablename__ = "extraction_results"

    # ------------------------------------------------------------------
    # Primary key
    # ------------------------------------------------------------------

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # ------------------------------------------------------------------
    # Document
    # ------------------------------------------------------------------

    document_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "documents.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Document version
    #
    # Important because a document may have multiple versions.
    # ------------------------------------------------------------------

    document_version_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "document_versions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Processing job
    #
    # Identifies the processing execution that produced this result.
    #
    # Not unique intentionally:
    #
    #   - retries
    #   - alternative extraction strategies
    #   - multiple extraction attempts
    #   - future re-processing scenarios
    # ------------------------------------------------------------------

    processing_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "processing_jobs.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------

    document_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------------
    # Overall extraction confidence
    #
    # Canonical range:
    #
    #     0.0 <= confidence <= 1.0
    #
    # This is extraction confidence, not necessarily classification
    # confidence.
    # ------------------------------------------------------------------

    overall_confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    # ------------------------------------------------------------------
    # Raw extracted text
    #
    # This represents the canonical text produced by the extraction
    # pipeline.
    #
    # For extremely large documents, this can later be moved to object
    # storage with a reference stored in metadata.
    # ------------------------------------------------------------------

    raw_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Structured extraction
    #
    # Example:
    #
    # {
    #     "invoice_number": "INV-1001",
    #     "invoice_date": "2026-08-31",
    #     "vendor_name": "ABC Ltd",
    #     "total_amount": 12500.0,
    #     "currency": "USD"
    # }
    #
    # This contains canonical structured extraction data.
    # Individual field-level provenance belongs in ExtractedField.
    # ------------------------------------------------------------------

    structured_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Validation status
    #
    # Typical values:
    #
    #     pending
    #     passed
    #     failed
    #     warning
    # ------------------------------------------------------------------

    validation_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
    )

    # ------------------------------------------------------------------
    # Extraction method
    #
    # Examples:
    #
    #     rule_based
    #     llm
    #     hybrid
    #     invoice_extractor
    #     generic_extractor
    #
    # This should describe the logical extraction strategy, not expose
    # provider-specific implementation details.
    # ------------------------------------------------------------------

    extraction_method: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Extraction metadata
    #
    # Provider-independent metadata associated with this extraction.
    #
    # Examples:
    #
    # {
    #     "page_count": 4,
    #     "language": "en",
    #     "processing_duration_ms": 1240,
    #     "extraction_version": "2.1"
    # }
    #
    # Do NOT store provider response blobs here.
    # ------------------------------------------------------------------

    extraction_metadata: Mapped[
        dict[str, Any] | None
    ] = mapped_column(
        JSONB,
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Timestamps
    # ------------------------------------------------------------------

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Constraints and indexes
    # ------------------------------------------------------------------

    __table_args__ = (
        CheckConstraint(
            """
            overall_confidence >= 0
            AND overall_confidence <= 1
            """,
            name="ck_extraction_results_overall_confidence",
        ),
        Index(
            "ix_extraction_results_document_id",
            "document_id",
        ),
        Index(
            "ix_extraction_results_document_version_id",
            "document_version_id",
        ),
        Index(
            "ix_extraction_results_processing_id",
            "processing_id",
        ),
    )

    # ------------------------------------------------------------------
    # Representation
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            "<ExtractionResult("
            f"id={self.id}, "
            f"document_id={self.document_id}, "
            f"document_version_id={self.document_version_id}, "
            f"processing_id={self.processing_id}, "
            f"document_type={self.document_type!r}, "
            f"overall_confidence={self.overall_confidence:.2f}, "
            f"validation_status={self.validation_status!r}"
            ")>"
        )


__all__ = [
    "ExtractionResult",
]