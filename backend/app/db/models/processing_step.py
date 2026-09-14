"""
app/db/models/processing_step.py

Represents one independently observable stage of a ProcessingJob.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database  import Base


if TYPE_CHECKING:
    from app.db.models.processing_job import ProcessingJob


class ProcessingStep(Base):
    """Represents one stage of a document-processing pipeline."""

    __tablename__ = "processing_steps"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    processing_job_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "processing_jobs.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------------
    # Step identity
    # ------------------------------------------------------------------

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    step_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        server_default="pending",
        index=True,
    )

    # ------------------------------------------------------------------
    # Provider
    # ------------------------------------------------------------------

    provider: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    provider_operation: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    attempt_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    duration_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    input_metadata: Mapped[dict] = mapped_column(
        MutableDict.as_mutable(JSONB),
        nullable=False,
        default=dict,
        server_default="{}",
    )

    output_metadata: Mapped[dict] = mapped_column(
        MutableDict.as_mutable(JSONB),
        nullable=False,
        default=dict,
        server_default="{}",
    )

    # ------------------------------------------------------------------
    # Errors
    # ------------------------------------------------------------------

    error_code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
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

    processing_job: Mapped["ProcessingJob"] = relationship(
        "ProcessingJob",
        back_populates="steps",
    )

    def __repr__(self) -> str:
        return (
            f"<ProcessingStep("
            f"id={self.id!r}, "
            f"processing_job_id={self.processing_job_id!r}, "
            f"name={self.name!r}, "
            f"status={self.status!r}, "
            f"step_order={self.step_order}"
            f")>"
        )