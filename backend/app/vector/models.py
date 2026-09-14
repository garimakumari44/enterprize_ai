from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class VectorRecord(BaseModel):
    """
    Represents a vector stored in the vector database.
    """

    model_config = ConfigDict(extra="allow")

    id: str
    document_id: str | None = None
    chunk_id: str | None = None

    embedding: list[float]

    metadata: dict[str, Any] = Field(default_factory=dict)

    content: str | None = None


class VectorSearchRequest(BaseModel):
    """
    Parameters for similarity search.
    """

    embedding: list[float]

    top_k: int = Field(default=10, ge=1, le=100)

    document_id: str | None = None

    metadata_filter: dict[str, Any] = Field(default_factory=dict)

    score_threshold: float | None = None


class VectorSearchResult(BaseModel):
    """
    Single similarity-search result.
    """

    id: str
    document_id: str | None = None
    chunk_id: str | None = None

    score: float

    content: str | None = None

    metadata: dict[str, Any] = Field(default_factory=dict)


class VectorSearchResponse(BaseModel):
    """
    Complete similarity-search response.
    """

    results: list[VectorSearchResult] = Field(default_factory=list)

    total: int = 0


class VectorUpsertRequest(BaseModel):
    """
    Request for inserting/updating vectors.
    """

    records: list[VectorRecord] = Field(min_length=1)


class VectorDeleteRequest(BaseModel):
    """
    Request for deleting vectors.
    """

    ids: list[str] = Field(min_length=1)