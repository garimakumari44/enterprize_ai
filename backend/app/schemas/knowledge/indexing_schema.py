"""
Knowledge Indexing Schemas
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class IndexingRequest(BaseModel):
    """Request to index a document."""

    document_id: UUID

    collection_id: UUID

    embedding_model: str

    chunk_size: int = Field(default=1000, ge=100)

    chunk_overlap: int = Field(default=200, ge=0)

    generate_embeddings: bool = True

    extract_entities: bool = True

    build_graph: bool = True

    metadata: dict = Field(default_factory=dict)


class IndexingStatus(BaseModel):
    """Current indexing status."""

    status: str

    progress: int = Field(..., ge=0, le=100)

    processed_chunks: int

    total_chunks: int

    message: Optional[str] = None


class IndexedDocumentResponse(BaseModel):
    """Indexed document response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID

    document_id: UUID

    collection_id: UUID

    index_name: str

    embedding_model: str

    chunk_count: int

    embedding_count: int

    status: str

    indexed_at: datetime

    created_at: datetime

    updated_at: datetime


class ReindexRequest(BaseModel):
    """Re-index an existing document."""

    document_id: UUID

    force: bool = False

    rebuild_embeddings: bool = True

    rebuild_graph: bool = True


class DeleteIndexRequest(BaseModel):
    """Delete document index."""

    document_id: UUID

    remove_vectors: bool = True

    remove_graph: bool = True