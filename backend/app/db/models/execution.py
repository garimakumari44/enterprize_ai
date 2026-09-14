from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.constants.execution_status import ExecutionStatus
from app.db.database import Base


class Execution(Base):
    """
    Database model representing a single workflow execution.

    An execution tracks:
    - The workflow being executed
    - Current execution status
    - Input and output data
    - Execution context
    - Start and finish timestamps
    - Execution duration
    - Error information
    """

    __tablename__ = "executions"

    # ==========================================================
    # Primary Key
    # ==========================================================

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ==========================================================
    # Workflow
    # ==========================================================

    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "workflows.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # ==========================================================
    # Status
    # ==========================================================

    status: Mapped[ExecutionStatus] = mapped_column(
        default=ExecutionStatus.PENDING,
        nullable=False,
        index=True,
    )

    # ==========================================================
    # Execution Lifecycle
    # ==========================================================

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    duration_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # ==========================================================
    # Input / Output
    # ==========================================================

    input_data: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )

    output_data: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )

    # ==========================================================
    # Execution Context
    # ==========================================================

    context: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )

    # ==========================================================
    # Error
    # ==========================================================

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ==========================================================
    # Timestamps
    # ==========================================================

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

    # ==========================================================
    # Relationships
    # ==========================================================

    workflow: Mapped["Workflow"] = relationship(
        "Workflow",
        foreign_keys=[workflow_id],
    )

    # ==========================================================
    # Representation
    # ==========================================================

    def __repr__(self) -> str:
        return (
            f"<Execution("
            f"id={self.id}, "
            f"workflow_id={self.workflow_id}, "
            f"status={self.status}"
            f")>"
        )