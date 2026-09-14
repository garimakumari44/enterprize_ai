# app/review/models/reviewer_assignment.py

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class AssignmentStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DECLINED = "declined"
    CANCELLED = "cancelled"


class ReviewerAssignment(Base):
    """
    Assigns a review task to a reviewer.

    One ReviewTask can have multiple ReviewerAssignments.
    """

    __tablename__ = "reviewer_assignments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    review_task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("review_tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    reviewer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    assigned_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    status: Mapped[AssignmentStatus] = mapped_column(
        Enum(AssignmentStatus),
        default=AssignmentStatus.PENDING,
        nullable=False,
        index=True,
    )

    notes: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

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

    # Relationships
    review_task = relationship(
        "ReviewTask",
        back_populates="assignments",
    )

    reviewer = relationship(
        "User",
        foreign_keys=[reviewer_id],
    )

    assigned_by_user = relationship(
        "User",
        foreign_keys=[assigned_by],
    )

    def __repr__(self) -> str:
        return (
            f"<ReviewerAssignment("
            f"id={self.id}, "
            f"reviewer={self.reviewer_id}, "
            f"status={self.status.value})>"
        )