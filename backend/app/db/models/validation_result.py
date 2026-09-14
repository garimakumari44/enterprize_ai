"""
app/db/models/validation_result.py

Persisted validation result for an extracted field.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ValidationStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"


class ValidationResult(Base):
    """
    Result of validating a single extracted field.

    Extraction determines WHAT was found.
    Validation determines WHETHER the value is acceptable.
    """

    __tablename__ = "validation_results"

    # ------------------------------------------------------------------
    # Primary key
    # ------------------------------------------------------------------

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ------------------------------------------------------------------
    # Extraction result
    # ------------------------------------------------------------------

    extraction_result_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "extraction_results.id",
            ondelete="CASCADE",
        ),
        nullable=True,
        index=True,
    )

    # ------------------------------------------------------------------
    # Field
    # ------------------------------------------------------------------

    field_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------------
    # Validation status
    # ------------------------------------------------------------------

    status: Mapped[ValidationStatus] = mapped_column(
        String(32),
        nullable=False,
        default=ValidationStatus.PASSED,
    )

    passed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    rule_name: Mapped[str | None] = mapped_column(
        String(255),
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
    # Representation
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            "<ValidationResult("
            f"id={self.id}, "
            f"field_name={self.field_name!r}, "
            f"status={self.status!r}, "
            f"passed={self.passed}"
            ")>"
        )


__all__ = [
    "ValidationResult",
    "ValidationStatus",
]