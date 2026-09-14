from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DocumentIntelligenceArtifact(BaseModel):
    """
    Reference to an artifact generated during document intelligence processing.
    """

    id: str
    type: str
    status: str = "available"
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentIntelligenceValidation(BaseModel):
    """
    Validation information produced by the intelligence pipeline.
    """

    valid: bool = True
    checks: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class DocumentIntelligenceKnowledge(BaseModel):
    """
    Knowledge/index information generated for the document.
    """

    indexed: bool = False
    index_id: str | None = None
    chunk_count: int | None = None
    embedding_count: int | None = None


class DocumentIntelligenceResultResponse(BaseModel):
    """
    Business-level result produced by processing a document.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    processing_id: uuid.UUID
    document_id: uuid.UUID
    document_version_id: uuid.UUID

    document_type: str | None = None
    confidence: float | None = None

    structured_data: dict[str, Any] = Field(
        default_factory=dict,
    )

    validation_results: dict[str, Any] = Field(
        default_factory=dict,
    )

    artifacts: list[DocumentIntelligenceArtifact] = Field(
        default_factory=list,
    )

    knowledge: dict[str, Any] = Field(
        default_factory=dict,
    )

    raw_text: str | None = None

    created_at: datetime
    updated_at: datetime