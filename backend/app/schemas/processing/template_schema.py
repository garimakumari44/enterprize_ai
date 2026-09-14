from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class ProcessingTemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)

    description: Optional[str] = None

    document_type: Optional[str] = Field(default=None, max_length=100)

    configuration: dict[str, Any] = Field(default_factory=dict)


class ProcessingTemplateUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)

    description: Optional[str] = None

    document_type: Optional[str] = Field(default=None, max_length=100)

    configuration: Optional[dict[str, Any]] = None


class ProcessingTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID

    name: str

    description: Optional[str]

    document_type: Optional[str]

    configuration: dict[str, Any]

    created_at: datetime

    updated_at: datetime


class ProcessingTemplateList(BaseModel):
    items: list[ProcessingTemplateResponse]
    total: int