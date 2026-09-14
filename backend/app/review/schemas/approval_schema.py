from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ApprovalDecision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"


# ---------------------------------------------------------
# Submit Decision
# ---------------------------------------------------------


class ApprovalCreate(BaseModel):
    review_id: UUID

    decision: ApprovalDecision

    comments: Optional[str] = Field(
        default=None,
        max_length=5000,
    )


# ---------------------------------------------------------
# Response
# ---------------------------------------------------------


class ApprovalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID

    review_id: UUID

    reviewer_id: UUID

    decision: ApprovalDecision

    comments: Optional[str]

    created_at: datetime