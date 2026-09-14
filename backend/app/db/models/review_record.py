"""
app/db/models/review_record.py

Human review records for Document Intelligence results.

A ReviewRecord captures a human decision made against the
business-level intelligence produced by document processing.

ProcessingJob / ProcessingStep:
    How the document was processed.

DocumentIntelligenceResult:
    What the system concluded.

ReviewRecord:
    What a human reviewer decided about that conclusion.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class ReviewStatus(str, Enum):
    """Lifecycle state of a human review."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"
    CANCELLED = "cancelled"


class ReviewDecision(str, Enum):
    """Final decision made by the reviewer."""

    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_CHANGES = "request_changes"


class ReviewRecord(Base):
    """
    Human review/audit record for a Document Intelligence result.

    A single intelligence result may have multiple review records,
    for example when a result is rejected and subsequently reviewed
    again.

    The model intentionally keeps reviewer-specific information
    separate from the processing pipeline.
    """

    __tablename__ = "review_records"

    __table_args__ = (
        Index(
            "ix_review_records_intelligence_result_id",
            "intelligence_result_id",
        ),
        Index(
            "ix_review_records_status",
            "status",
        ),
        Index(
            "ix_review_records_reviewer_id",
            "reviewer_id",
        ),
        Index(
            "ix_review_records_created_at",
            "created_at",
        ),
    )

    # ------------------------------------------------------------------
    # Primary key
    # ------------------------------------------------------------------

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ------------------------------------------------------------------
    # Intelligence result being reviewed
    # ------------------------------------------------------------------

    intelligence_result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "document_intelligence_results.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Reviewer
    # ------------------------------------------------------------------

    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    reviewer_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    reviewer_email: Mapped[str | None] = mapped_column(
        String(320),
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Review lifecycle
    # ------------------------------------------------------------------

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=ReviewStatus.PENDING.value,
    )

    decision: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Review content
    # ------------------------------------------------------------------

    comments: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    reviewer_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Corrections / overrides
    # ------------------------------------------------------------------

    corrections: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    overridden_fields: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Review metadata
    # ------------------------------------------------------------------

    review_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Timestamps
    # ------------------------------------------------------------------

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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

    intelligence_result = relationship(
        "DocumentIntelligenceResult",
        back_populates="review_records",
        lazy="selectin",
    )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def approve(
        self,
        *,
        comments: str | None = None,
    ) -> None:
        """Mark the review as approved."""

        self.status = ReviewStatus.APPROVED.value
        self.decision = ReviewDecision.APPROVE.value
        self.comments = comments
        self.completed_at = datetime.utcnow()

    def reject(
        self,
        *,
        comments: str | None = None,
        corrections: dict[str, Any] | None = None,
    ) -> None:
        """Mark the review as rejected."""

        self.status = ReviewStatus.REJECTED.value
        self.decision = ReviewDecision.REJECT.value
        self.comments = comments
        self.corrections = corrections
        self.completed_at = datetime.utcnow()

    def request_changes(
        self,
        *,
        comments: str | None = None,
        corrections: dict[str, Any] | None = None,
    ) -> None:
        """Request corrections to the intelligence result."""

        self.status = ReviewStatus.CHANGES_REQUESTED.value
        self.decision = ReviewDecision.REQUEST_CHANGES.value
        self.comments = comments
        self.corrections = corrections
        self.completed_at = datetime.utcnow()

    def __repr__(self) -> str:
        return (
            f"<ReviewRecord("
            f"id={self.id}, "
            f"intelligence_result_id={self.intelligence_result_id}, "
            f"status={self.status}, "
            f"decision={self.decision}"
            f")>"
        )