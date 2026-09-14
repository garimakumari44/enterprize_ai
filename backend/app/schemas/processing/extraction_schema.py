from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class ExtractedFieldCreate(BaseModel):
    field_name: str = Field(..., min_length=1, max_length=200)

    field_value: Any

    page_number: Optional[int] = Field(default=None, ge=1)

    confidence_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
    )


class ExtractedFieldUpdate(BaseModel):
    field_value: Optional[Any] = None

    confidence_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
    )


class ExtractedFieldResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID

    extraction_result_id: uuid.UUID

    field_name: str

    field_value: Any

    page_number: Optional[int]

    confidence_score: Optional[float]

    created_at: datetime


class ExtractionResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID

    processing_job_id: uuid.UUID

    extracted_text: Optional[str]

    language: Optional[str]

    ocr_engine: Optional[str]

    created_at: datetime

    extracted_fields: list[ExtractedFieldResponse] = []