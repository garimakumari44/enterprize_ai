from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    DateTime,
    Float,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UsageMetric(Base):
    """
    Platform-wide usage metrics collected periodically.
    """

    __tablename__ = "usage_metrics"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    metric_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    metric_value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    unit: Mapped[str] = mapped_column(
        String(30),
        default="count",
        nullable=False,
    )

    period: Mapped[str] = mapped_column(
        String(20),
        default="daily",
        nullable=False,
    )

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    sample_size: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )