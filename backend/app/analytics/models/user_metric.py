from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserMetric(Base):
    """
    Tracks user activity statistics.
    """

    __tablename__ = "user_metrics"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    workflows_created: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    executions_started: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    executions_completed: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    failed_executions: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    login_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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