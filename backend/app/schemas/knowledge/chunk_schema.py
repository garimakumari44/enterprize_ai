"""
Document Chunk Schemas
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ChunkBase(BaseModel):
    """Base chunk schema."""

    chunk_index: int
    content: str = Field(..., min_length=1)

    token_count: int = 0
    character_count: int = 0

    page_number: Optional[int] = None

    metadata: dict = Field(default_factory=dict)


class ChunkCreate(ChunkBase):
    """Chunk creation schema."""

    document_id: UUID


class ChunkUpdate(BaseModel):
    """Chunk update schema."""

    content: Optional[str] = None
    metadata: Optional[dict] = None


class ChunkResponse(ChunkBase):
    """Chunk response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID

    document_id: UUID

    embedding_id: Optional[UUID] = None

    created_at: datetime
    updated_at: datetime


class ChunkListResponse(BaseModel):
    total: int
    items: list[ChunkResponse]