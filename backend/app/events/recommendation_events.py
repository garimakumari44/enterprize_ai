from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class RecommendationEvent(BaseModel):
    """Base recommendation event."""

    event_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime = Field(default_factory=datetime.utcnow)
    event_type: str


class RecommendationGeneratedEvent(RecommendationEvent):
    event_type: str = "recommendation.generated"

    recommendation_id: UUID
    user_id: UUID
    recommendation_type: str
    confidence: float


class RecommendationAcceptedEvent(RecommendationEvent):
    event_type: str = "recommendation.accepted"

    recommendation_id: UUID
    user_id: UUID


class RecommendationRejectedEvent(RecommendationEvent):
    event_type: str = "recommendation.rejected"

    recommendation_id: UUID
    user_id: UUID
    reason: str | None = None