"""
Embedding Schemas
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EmbeddingBase(BaseModel):
    """Embedding metadata."""

    model_name: str

    dimension: int = Field(..., gt=0)

    vector_store: str

    vector_id: Optional[str] = None

    metadata: dict = Field(default_factory=dict)


class EmbeddingCreate(EmbeddingBase):
    """Create embedding."""

    chunk_id: UUID


class EmbeddingUpdate(BaseModel):
    """Update embedding."""

    vector_id: Optional[str] = None
    metadata: Optional[dict] = None


class EmbeddingResponse(EmbeddingBase):
    """Embedding response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID

    chunk_id: UUID

    created_at: datetime
    updated_at: datetime


class EmbeddingListResponse(BaseModel):
    total: int
    items: list[EmbeddingResponse]