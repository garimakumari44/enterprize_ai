
"""
app/schemas/processing/review.py

Schemas for processing-result human review.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.db.models.review_record import (
    ReviewDecision,
    ReviewStatus,
)


class ReviewCorrection(BaseModel):
    field: str
    value: Any = None
    reason: str | None = None


class ReviewSubmitRequest(BaseModel):
    decision: str = Field(
        ...,
        description="approve, reject, or request_changes",
    )

    comments: str | None = None

    corrections: list[ReviewCorrection] = Field(
        default_factory=list
    )


class ReviewResponse(BaseModel):
    id: UUID

    intelligence_result_id: UUID

    reviewer_id: UUID | None = None
    reviewer_name: str | None = None
    reviewer_email: str | None = None

    status: str
    decision: str | None = None

    comments: str | None = None
    reviewer_notes: str | None = None

    corrections: dict[str, Any] | None = None
    overridden_fields: dict[str, Any] | None = None
    review_metadata: dict[str, Any] | None = None

    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {
        "from_attributes": True,
    }

