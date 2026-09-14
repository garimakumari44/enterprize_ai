# app/review/models/review_action.py

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    JSON,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class ReviewActionType(str, enum.Enum):
    COMMENT = "comment"
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_CHANGES = "request_changes"
    REASSIGN = "reassign"
    ESCALATE = "escalate"
    STATUS_CHANGE = "status_change"
    ATTACHMENT = "attachment"


class ReviewAction(Base):
    """
    Immutable audit trail of actions taken during a review.

    Every user interaction with a review task should create
    a ReviewAction record.
    """

    __tablename__ = "review_actions"

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

    assignment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reviewer_assignments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    action_type: Mapped[ReviewActionType] = mapped_column(
        Enum(ReviewActionType),
        nullable=False,
        index=True,
    )

    comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    metadata: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    review_task = relationship(
        "ReviewTask",
        back_populates="actions",
    )

    assignment = relationship(
        "ReviewerAssignment",
    )

    actor = relationship(
        "User",
        foreign_keys=[actor_id],
    )

    def __repr__(self) -> str:
        return (
            f"<ReviewAction("
            f"id={self.id}, "
            f"action={self.action_type.value}, "
            f"actor={self.actor_id})>"
        )