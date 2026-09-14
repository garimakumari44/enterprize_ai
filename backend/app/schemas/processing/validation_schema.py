from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ValidationStatus(str, Enum):
    """
    Overall result of a business validation rule.
    """

    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    REVIEW_REQUIRED = "review_required"


class ValidationResultCreate(BaseModel):
    """
    Schema used when creating a validation result.

    A validation result belongs to an ExtractionResult and represents
    the outcome of one business or data-quality rule.
    """

    extraction_result_id: uuid.UUID

    status: ValidationStatus

    rule_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name of the validation/business rule executed.",
    )

    message: Optional[str] = Field(
        default=None,
        description="Human-readable explanation of the validation result.",
    )


class ValidationResultUpdate(BaseModel):
    """
    Schema used to update an existing validation result.
    """

    status: Optional[ValidationStatus] = None

    message: Optional[str] = Field(
        default=None,
        description="Updated validation message.",
    )


class ValidationResultResponse(BaseModel):
    """
    API representation of a persisted validation result.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID

    extraction_result_id: uuid.UUID

    status: ValidationStatus

    rule_name: str

    message: Optional[str] = None

    created_at: datetime

    updated_at: datetime


class ValidationResultList(BaseModel):
    """
    Paginated/list response for validation results.
    """

    items: list[ValidationResultResponse] = Field(default_factory=list)

    total: int = Field(
        default=0,
        ge=0,
    )