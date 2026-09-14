"""
Knowledge Relation Schemas
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RelationBase(BaseModel):
    """Base relation schema."""

    source_chunk_id: UUID

    target_chunk_id: UUID

    relation_type: str = Field(..., min_length=2, max_length=100)

    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

    metadata: dict = Field(default_factory=dict)


class RelationCreate(RelationBase):
    """Create relation."""

    pass


class RelationUpdate(BaseModel):
    """Update relation."""

    relation_type: Optional[str] = None

    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)

    metadata: Optional[dict] = None


class RelationResponse(RelationBase):
    """Relation response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID

    created_at: datetime

    updated_at: datetime


class RelationListResponse(BaseModel):
    """Paginated relation list."""

    total: int

    items: list[RelationResponse]