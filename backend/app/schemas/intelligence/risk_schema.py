from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class RiskFactor(BaseModel):
    name: str

    impact: float

    explanation: str


class RiskRequest(BaseModel):
    entity_id: str

    entity_type: str

    payload: Optional[Dict[str, Any]] = None


class RiskResponse(BaseModel):
    overall_risk_score: float

    risk_level: str

    confidence: float

    factors: List[RiskFactor]

    recommendations: List[str]