"""
app/db/models/workflow_run.py

Workflow run persistence model.

A WorkflowRun represents one execution of a Workflow.

Example:

    Workflow
        |
        +── WorkflowRun #1
        |
        +── WorkflowRun #2
        |
        +── WorkflowRun #3

The Workflow defines what should happen.
The WorkflowRun records one actual execution.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class WorkflowRunStatus(str, Enum):
    """
    Lifecycle state of a workflow execution.
    """

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowRun(Base):
    """
    Represents one execution of a Workflow.

    A WorkflowRun stores execution-level information such as:

    - which workflow was executed
    - current status
    - start/end timestamps
    - input data
    - output data
    - error information
    - execution metadata
    """

    __tablename__ = "workflow_runs"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    workflow_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status: Mapped[WorkflowRunStatus] = mapped_column(
        String(32),
        nullable=False,
        default=WorkflowRunStatus.PENDING,
        index=True,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    input_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    output_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    error_type: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

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

    workflow: Mapped["Workflow"] = relationship(
        "Workflow",
        back_populates="runs",
    )

    def mark_running(self) -> None:
        """Mark the workflow run as started."""

        self.status = WorkflowRunStatus.RUNNING
        self.started_at = datetime.now().astimezone()
        self.error_message = None
        self.error_type = None

    def mark_completed(
        self,
        output_data: dict[str, Any] | None = None,
    ) -> None:
        """Mark the workflow run as successfully completed."""

        self.status = WorkflowRunStatus.COMPLETED
        self.completed_at = datetime.now().astimezone()

        if output_data is not None:
            self.output_data = output_data

        self.error_message = None
        self.error_type = None

    def mark_failed(
        self,
        error: Exception,
    ) -> None:
        """Mark the workflow run as failed."""

        self.status = WorkflowRunStatus.FAILED
        self.completed_at = datetime.now().astimezone()

        self.error_type = type(error).__name__
        self.error_message = str(error)

    def mark_cancelled(self) -> None:
        """Mark the workflow run as cancelled."""

        self.status = WorkflowRunStatus.CANCELLED
        self.completed_at = datetime.now().astimezone()

    @property
    def is_finished(self) -> bool:
        """Return True when the run has reached a terminal state."""

        return self.status in {
            WorkflowRunStatus.COMPLETED,
            WorkflowRunStatus.FAILED,
            WorkflowRunStatus.CANCELLED,
        }

    @property
    def duration_seconds(self) -> float | None:
        """Return execution duration in seconds when available."""

        if self.started_at is None or self.completed_at is None:
            return None

        return (
            self.completed_at - self.started_at
        ).total_seconds()


# Avoid circular imports at runtime.
from app.db.models.workflow import Workflow