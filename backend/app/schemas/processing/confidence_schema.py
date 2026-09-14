from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ConfidenceScoreCreate(BaseModel):
    extracted_field_id: uuid.UUID

    overall_score: float = Field(..., ge=0, le=1)

    model_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
    )

    ocr_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
    )

    validation_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
    )


class ConfidenceScoreUpdate(BaseModel):
    overall_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
    )

    model_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
    )

    ocr_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
    )

    validation_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
    )


class ConfidenceScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID

    extracted_field_id: uuid.UUID

    overall_score: float

    model_score: Optional[float]

    ocr_score: Optional[float]

    validation_score: Optional[float]

    created_at: datetime

    updated_at: datetime