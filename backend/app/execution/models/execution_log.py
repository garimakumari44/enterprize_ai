"""
Execution log model.

Stores logs generated during workflow execution.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

from app.execution.constants.execution_status import LogLevel


class ExecutionLog(Base):
    """
    Stores a single execution log entry.
    """

    __tablename__ = "execution_logs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    execution_id: Mapped[int] = mapped_column(
        ForeignKey("executions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    node_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
    )

    node_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    node_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=LogLevel.INFO.value,
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    details: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:
        return (
            f"<ExecutionLog("
            f"id={self.id}, "
            f"execution_id={self.execution_id}, "
            f"level={self.level}"
            f")>"
        )