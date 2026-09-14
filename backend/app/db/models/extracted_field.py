"""
app/db/models/extracted_field.py

Persisted field extracted from a document.

Each ExtractedField belongs to exactly one ExtractionResult.

Example:

    ExtractionResult
        |
        +---- invoice_number
        +---- invoice_date
        +---- vendor_name
        +---- customer_name
        +---- total_amount

The model stores both the extracted value and its provenance.
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
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ExtractedField(Base):
    """
    Persisted individual field extracted from a document.

    Each row represents one field belonging to an ExtractionResult.
    """

    __tablename__ = "extracted_fields"

    # ------------------------------------------------------------------
    # Primary key
    # ------------------------------------------------------------------

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # ------------------------------------------------------------------
    # Extraction result
    #
    # Multiple fields can belong to one extraction result.
    # ------------------------------------------------------------------

    extraction_result_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "extraction_results.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Field identity
    #
    # Examples:
    #
    #     invoice_number
    #     invoice_date
    #     vendor_name
    #     total_amount
    # ------------------------------------------------------------------

    field_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Extracted value
    #
    # JSONB allows:
    #
    #     strings
    #     numbers
    #     booleans
    #     arrays
    #     objects
    #
    # Example:
    #
    #     "INV-1001"
    #
    #     12500.0
    #
    #     ["item1", "item2"]
    # ------------------------------------------------------------------

    value: Mapped[Any] = mapped_column(
        JSONB,
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Confidence
    #
    # Canonical range:
    #
    #     0.0 <= confidence <= 1.0
    # ------------------------------------------------------------------

    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    # ------------------------------------------------------------------
    # Normalized value
    #
    # Example:
    #
    #     value:
    #         "$12,500.00"
    #
    #     normalized_value:
    #         12500.0
    #
    # Another example:
    #
    #     value:
    #         "31/08/2026"
    #
    #     normalized_value:
    #         "2026-08-31"
    # ------------------------------------------------------------------

    normalized_value: Mapped[Any] = mapped_column(
        JSONB,
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Extraction source
    #
    # Provider-independent logical source.
    #
    # Examples:
    #
    #     ocr
    #     text
    #     layout
    #     llm
    #     rule
    #     hybrid
    #
    # Do not use this field for provider names such as:
    #
    #     paddle
    #     tesseract
    #     openai
    #
    # Provider details belong in processing metadata.
    # ------------------------------------------------------------------

    source: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Page provenance
    # ------------------------------------------------------------------

    page_number: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Bounding box
    #
    # Canonical structure:
    #
    # {
    #     "x": 120,
    #     "y": 240,
    #     "width": 180,
    #     "height": 30
    # }
    #
    # Coordinates should use the coordinate system defined by the
    # processing pipeline.
    # ------------------------------------------------------------------

    bounding_box: Mapped[
        dict[str, Any] | None
    ] = mapped_column(
        JSONB,
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Field metadata
    #
    # Provider-independent metadata.
    #
    # Examples:
    #
    # {
    #     "data_type": "currency",
    #     "unit": "USD",
    #     "normalized": true
    # }
    #
    # Do not use the attribute name "metadata" because SQLAlchemy's
    # declarative Base already exposes metadata-related functionality.
    # ------------------------------------------------------------------

    field_metadata: Mapped[
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
            confidence >= 0
            AND confidence <= 1
            """,
            name="ck_extracted_fields_confidence",
        ),
        CheckConstraint(
            """
            page_number IS NULL
            OR page_number >= 1
            """,
            name="ck_extracted_fields_page_number",
        ),
        Index(
            "ix_extracted_fields_extraction_result_id",
            "extraction_result_id",
        ),
        Index(
            "ix_extracted_fields_field_name",
            "field_name",
        ),
    )

    # ------------------------------------------------------------------
    # Representation
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            "<ExtractedField("
            f"id={self.id}, "
            f"extraction_result_id={self.extraction_result_id}, "
            f"field_name={self.field_name!r}, "
            f"confidence={self.confidence:.2f}, "
            f"source={self.source!r}, "
            f"page_number={self.page_number}"
            ")>"
        )


__all__ = [
    "ExtractedField",
]