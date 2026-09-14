from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class RiskEvent(BaseModel):
    """Base risk event."""

    event_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime = Field(default_factory=datetime.utcnow)
    event_type: str


class RiskScoreCalculatedEvent(RiskEvent):
    event_type: str = "risk.score.calculated"

    entity_id: UUID
    score: float
    risk_level: str


class FraudDetectedEvent(RiskEvent):
    event_type: str = "risk.fraud.detected"

    entity_id: UUID
    score: float
    description: str


class AnomalyDetectedEvent(RiskEvent):
    event_type: str = "risk.anomaly.detected"

    entity_id: UUID
    anomaly_type: str
    confidence: float