from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AssignmentStatus(str, Enum):
    ASSIGNED = "assigned"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    COMPLETED = "completed"


# ---------------------------------------------------------
# Assign Reviewer
# ---------------------------------------------------------


class ReviewerAssignmentCreate(BaseModel):
    review_id: UUID
    reviewer_id: UUID


# ---------------------------------------------------------
# Update Assignment
# ---------------------------------------------------------


class ReviewerAssignmentUpdate(BaseModel):
    status: AssignmentStatus


# ---------------------------------------------------------
# Response
# ---------------------------------------------------------


class ReviewerAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID

    review_id: UUID
    reviewer_id: UUID

    status: AssignmentStatus

    assigned_at: datetime
    completed_at: datetime | None