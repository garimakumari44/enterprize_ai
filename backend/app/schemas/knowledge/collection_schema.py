"""
Knowledge Collection Schemas

Pydantic schemas for creating, updating, and returning
knowledge collections.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CollectionBase(BaseModel):
    """Base collection schema."""

    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    embedding_model: Optional[str] = None
    vector_store: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class CollectionCreate(CollectionBase):
    """Schema used when creating a collection."""

    pass


class CollectionUpdate(BaseModel):
    """Schema used when updating a collection."""

    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    embedding_model: Optional[str] = None
    vector_store: Optional[str] = None
    metadata: Optional[dict] = None


class CollectionResponse(CollectionBase):
    """Schema returned to API clients."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    created_by: UUID

    total_documents: int
    total_chunks: int

    created_at: datetime
    updated_at: datetime


class CollectionListResponse(BaseModel):
    """Paginated collection list."""

    total: int
    items: list[CollectionResponse]