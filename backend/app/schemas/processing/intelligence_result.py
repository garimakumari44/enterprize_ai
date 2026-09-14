
"""
app/schemas/document_intelligence_result.py

Pydantic schemas for persisted Document Intelligence Results.

The database model lives in:

    app.db.models.document_intelligence_result

These schemas define the API representation only.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ============================================================================
# BASE
# ============================================================================


class DocumentIntelligenceResultBase(BaseModel):
    """
    Common Document Intelligence Result fields.
    """

    document_type: str | None = None

    classification_confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    structured_data: dict[str, Any] = Field(
        default_factory=dict,
    )

    validation_results: dict[str, Any] = Field(
        default_factory=dict,
    )

    artifacts: list[dict[str, Any]] = Field(
        default_factory=list,
    )

    knowledge: dict[str, Any] = Field(
        default_factory=dict,
    )

    raw_text: str | None = None


# ============================================================================
# CREATE
# ============================================================================


class DocumentIntelligenceResultCreate(
    DocumentIntelligenceResultBase,
):
    """
    Schema used when creating a Document Intelligence Result.
    """

    processing_id: UUID

    document_id: UUID

    document_version_id: UUID


# ============================================================================
# UPDATE
# ============================================================================


class DocumentIntelligenceResultUpdate(BaseModel):
    """
    Schema used to update an existing intelligence result.

    All fields are optional so callers can update only the fields
    they need.
    """

    document_type: str | None = None

    classification_confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    structured_data: dict[str, Any] | None = None

    validation_results: dict[str, Any] | None = None

    artifacts: list[dict[str, Any]] | None = None

    knowledge: dict[str, Any] | None = None

    raw_text: str | None = None


# ============================================================================
# RESPONSE
# ============================================================================


class DocumentIntelligenceResultResponse(
    DocumentIntelligenceResultBase,
):
    """
    API response representing a persisted Document Intelligence Result.
    """

    id: UUID

    processing_id: UUID

    document_id: UUID

    document_version_id: UUID

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


# ============================================================================
# DETAIL RESPONSE
# ============================================================================


class DocumentIntelligenceResultDetail(
    DocumentIntelligenceResultResponse,
):
    """
    Detailed API representation.

    Kept as a separate schema so additional detail can be added later
    without breaking the basic response contract.
    """

    pass


# ============================================================================
# EXPORTS
# ============================================================================


__all__ = [
    "DocumentIntelligenceResultBase",
    "DocumentIntelligenceResultCreate",
    "DocumentIntelligenceResultUpdate",
    "DocumentIntelligenceResultResponse",
    "DocumentIntelligenceResultDetail",
]

