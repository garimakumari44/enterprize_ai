from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReviewStatus(str, Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"
    CANCELLED = "cancelled"


# ------------------------------------------------------------------
# Create
# ------------------------------------------------------------------


class ReviewCreate(BaseModel):
    execution_id: UUID
    workflow_id: UUID
    document_id: Optional[UUID] = None

    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    priority: int = Field(default=3, ge=1, le=5)


# ------------------------------------------------------------------
# Update
# ------------------------------------------------------------------


class ReviewUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    priority: Optional[int] = Field(default=None, ge=1, le=5)
    status: Optional[ReviewStatus] = None


# ------------------------------------------------------------------
# Response
# ------------------------------------------------------------------


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID

    execution_id: UUID
    workflow_id: UUID
    document_id: Optional[UUID]

    title: str
    description: Optional[str]

    priority: int
    status: ReviewStatus

    created_by: UUID

    created_at: datetime
    updated_at: datetime


# ------------------------------------------------------------------
# List Response
# ------------------------------------------------------------------


class ReviewListResponse(BaseModel):
    total: int
    items: list[ReviewResponse]