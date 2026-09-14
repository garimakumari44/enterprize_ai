from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class RecommendationItem(BaseModel):
    title: str
    description: str

    score: float

    confidence: float

    category: str

    metadata: Optional[Dict[str, Any]] = None


class RecommendationRequest(BaseModel):
    entity_id: str

    entity_type: str

    context: Optional[Dict[str, Any]] = None


class RecommendationResponse(BaseModel):
    recommendations: List[RecommendationItem]

    total: int