"""
app/schemas/executions.py

Pydantic schemas for Execution History.

Execution History is a presentation/API layer over the existing
ProcessingJob and ProcessingStep records.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


# ============================================================
# Execution Step
# ============================================================


class ExecutionStepResponse(BaseModel):
    """
    A single processing step belonging to an execution.
    """

    model_config = ConfigDict(from_attributes=True)

    name: str
    step_order: int
    status: str

    provider: str | None = None
    provider_operation: str | None = None

    attempt_count: int = 0

    duration_ms: int | None = None

    error_code: str | None = None
    error_message: str | None = None

    created_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


# ============================================================
# Execution Summary
# ============================================================


class ExecutionSummaryResponse(BaseModel):
    """
    Lightweight representation used by the Execution History
    listing page.
    """

    processing_id: uuid.UUID

    document_id: uuid.UUID | None = None
    document_version_id: uuid.UUID | None = None

    document_name: str | None = None
    workflow_name: str | None = None

    status: str

    progress: int = 0

    current_stage: str | None = None

    error: str | None = None

    started_at: datetime | None = None
    completed_at: datetime | None = None

    duration_seconds: float | None = None

    steps_completed: int = 0
    steps_total: int = 0


# ============================================================
# Execution Detail
# ============================================================


class ExecutionDetailResponse(BaseModel):
    """
    Full execution result used by the Execution Details /
    Processing Result page.
    """

    processing_id: uuid.UUID

    document_id: uuid.UUID | None = None
    document_version_id: uuid.UUID | None = None

    document_name: str | None = None
    workflow_name: str | None = None

    status: str

    progress: int = 0

    current_stage: str | None = None

    error: str | None = None

    started_at: datetime | None = None
    completed_at: datetime | None = None

    duration_seconds: float | None = None

    result: dict[str, Any] | None = None

    steps: list[ExecutionStepResponse] = []


# ============================================================
# Paginated Execution History
# ============================================================


class ExecutionListResponse(BaseModel):
    """
    Paginated Execution History response.
    """

    items: list[ExecutionSummaryResponse]

    page: int
    page_size: int

    total: int

    pages: int