# app/review/events/review_events.py

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class ReviewEventType(str, Enum):
    TASK_CREATED = "review.task.created"
    TASK_ASSIGNED = "review.task.assigned"
    TASK_REASSIGNED = "review.task.reassigned"

    TASK_STARTED = "review.task.started"
    TASK_COMPLETED = "review.task.completed"

    APPROVED = "review.task.approved"
    REJECTED = "review.task.rejected"
    RETURNED = "review.task.returned"

    COMMENT_ADDED = "review.comment.added"

    ESCALATED = "review.task.escalated"
    CANCELLED = "review.task.cancelled"


@dataclass(slots=True)
class ReviewEvent:
    """
    Base event emitted from the Review domain.
    """

    event_id: UUID = field(default_factory=uuid4)
    event_type: ReviewEventType = ReviewEventType.TASK_CREATED

    review_task_id: UUID | None = None
    assignment_id: UUID | None = None

    user_id: UUID | None = None
    organization_id: UUID | None = None
    workflow_execution_id: UUID | None = None

    timestamp: datetime = field(default_factory=datetime.utcnow)

    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------
# Factory Functions
# ---------------------------------------------------------------------

def task_created(
    *,
    review_task_id: UUID,
    organization_id: UUID,
    workflow_execution_id: UUID | None = None,
) -> ReviewEvent:
    return ReviewEvent(
        event_type=ReviewEventType.TASK_CREATED,
        review_task_id=review_task_id,
        organization_id=organization_id,
        workflow_execution_id=workflow_execution_id,
    )


def task_assigned(
    *,
    review_task_id: UUID,
    assignment_id: UUID,
    reviewer_id: UUID,
) -> ReviewEvent:
    return ReviewEvent(
        event_type=ReviewEventType.TASK_ASSIGNED,
        review_task_id=review_task_id,
        assignment_id=assignment_id,
        user_id=reviewer_id,
    )


def task_reassigned(
    *,
    review_task_id: UUID,
    assignment_id: UUID,
    reviewer_id: UUID,
) -> ReviewEvent:
    return ReviewEvent(
        event_type=ReviewEventType.TASK_REASSIGNED,
        review_task_id=review_task_id,
        assignment_id=assignment_id,
        user_id=reviewer_id,
    )


def task_started(
    *,
    review_task_id: UUID,
    reviewer_id: UUID,
) -> ReviewEvent:
    return ReviewEvent(
        event_type=ReviewEventType.TASK_STARTED,
        review_task_id=review_task_id,
        user_id=reviewer_id,
    )


def task_completed(
    *,
    review_task_id: UUID,
    reviewer_id: UUID,
) -> ReviewEvent:
    return ReviewEvent(
        event_type=ReviewEventType.TASK_COMPLETED,
        review_task_id=review_task_id,
        user_id=reviewer_id,
    )


def approved(
    *,
    review_task_id: UUID,
    reviewer_id: UUID,
    comment: str | None = None,
) -> ReviewEvent:
    return ReviewEvent(
        event_type=ReviewEventType.APPROVED,
        review_task_id=review_task_id,
        user_id=reviewer_id,
        metadata={
            "comment": comment,
        },
    )


def rejected(
    *,
    review_task_id: UUID,
    reviewer_id: UUID,
    reason: str,
) -> ReviewEvent:
    return ReviewEvent(
        event_type=ReviewEventType.REJECTED,
        review_task_id=review_task_id,
        user_id=reviewer_id,
        metadata={
            "reason": reason,
        },
    )


def returned(
    *,
    review_task_id: UUID,
    reviewer_id: UUID,
    comment: str,
) -> ReviewEvent:
    return ReviewEvent(
        event_type=ReviewEventType.RETURNED,
        review_task_id=review_task_id,
        user_id=reviewer_id,
        metadata={
            "comment": comment,
        },
    )


def comment_added(
    *,
    review_task_id: UUID,
    reviewer_id: UUID,
    comment: str,
) -> ReviewEvent:
    return ReviewEvent(
        event_type=ReviewEventType.COMMENT_ADDED,
        review_task_id=review_task_id,
        user_id=reviewer_id,
        metadata={
            "comment": comment,
        },
    )


def escalated(
    *,
    review_task_id: UUID,
    reviewer_id: UUID,
    escalation_level: int,
) -> ReviewEvent:
    return ReviewEvent(
        event_type=ReviewEventType.ESCALATED,
        review_task_id=review_task_id,
        user_id=reviewer_id,
        metadata={
            "level": escalation_level,
        },
    )


def cancelled(
    *,
    review_task_id: UUID,
    user_id: UUID,
) -> ReviewEvent:
    return ReviewEvent(
        event_type=ReviewEventType.CANCELLED,
        review_task_id=review_task_id,
        user_id=user_id,
    )