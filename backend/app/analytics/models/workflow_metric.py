from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WorkflowMetric(Base):
    """
    Stores aggregated execution metrics for workflows.
    """

    __tablename__ = "workflow_metrics"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    workflow_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    execution_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    success_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    failure_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    average_duration: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    last_execution_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    period: Mapped[str] = mapped_column(
        String(20),
        default="daily",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )