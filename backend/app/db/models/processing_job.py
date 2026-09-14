"""
app/db/models/processing_job.py

Represents one complete processing execution for a DocumentVersion.

Pipeline:

    DocumentVersion
          |
          v
    ProcessingJob
          |
          +── classification
          +── extraction
          +── chunking
          +── embeddings
          +── indexing
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
    from app.db.models.document_version import DocumentVersion
    from app.db.models.processing_step import ProcessingStep


class ProcessingJob(Base):
    """
    One complete processing execution for a DocumentVersion.
    """

    __tablename__ = "processing_jobs"

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

    # ------------------------------------------------------------------
    # Job identity
    # ------------------------------------------------------------------

    job_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="document_processing",
        server_default="document_processing",
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="queued",
        server_default="queued",
        index=True,
    )

    # ------------------------------------------------------------------
    # Execution control
    # ------------------------------------------------------------------

    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    attempt_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    max_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3,
        server_default="3",
    )

    worker_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Progress
    # ------------------------------------------------------------------

    current_step: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    progress: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
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
    # Processing configuration
    # ------------------------------------------------------------------

    config: Mapped[dict] = mapped_column(
        MutableDict.as_mutable(JSONB),
        nullable=False,
        default=dict,
        server_default="{}",
    )

    # ------------------------------------------------------------------
    # Processing result
    # ------------------------------------------------------------------

    result: Mapped[dict] = mapped_column(
        MutableDict.as_mutable(JSONB),
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

    document_version: Mapped["DocumentVersion"] = relationship(
        "DocumentVersion",
        back_populates="processing_jobs",
    )

    steps: Mapped[list["ProcessingStep"]] = relationship(
        "ProcessingStep",
        back_populates="processing_job",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ProcessingStep.step_order",
    )

    def __repr__(self) -> str:
        return (
            f"<ProcessingJob("
            f"id={self.id!r}, "
            f"document_version_id={self.document_version_id!r}, "
            f"status={self.status!r}, "
            f"progress={self.progress}"
            f")>"
        )