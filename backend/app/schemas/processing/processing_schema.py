"""
app/schemas/processing.py

Pydantic schemas for document-processing jobs.

These schemas are shared by:

    - Processing API
    - Execution History UI
    - Processing status endpoints
    - Processing job creation
    - Processing job/step responses

Architecture:

    ProcessingJob
        |
        +--- ProcessingStep
        +--- ProcessingStep
        +--- ProcessingStep
        +--- ...

The schemas intentionally mirror the persistence model while
keeping API concerns separate from SQLAlchemy models.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ============================================================================
# PROCESSING STATUS
# ============================================================================


class ProcessingStatus(str, Enum):
    """
    Overall status of a document-processing job.
    """

    PENDING = "pending"

    QUEUED = "queued"

    RUNNING = "running"

    # Kept because some pipeline/processor code may use it.
    PROCESSING = "processing"

    COMPLETED = "completed"

    FAILED = "failed"

    CANCELLED = "cancelled"

    REVIEW_REQUIRED = "review_required"


# ============================================================================
# PROCESSING STEP STATUS
# ============================================================================


class ProcessingStepStatus(str, Enum):
    """
    Status of an individual processing pipeline stage.
    """

    PENDING = "pending"

    QUEUED = "queued"

    RUNNING = "running"

    # The current ProcessingJobRunner uses "processing" when
    # a stage is actively executing.
    PROCESSING = "processing"

    COMPLETED = "completed"

    FAILED = "failed"

    CANCELLED = "cancelled"

    SKIPPED = "skipped"


# ============================================================================
# START PROCESSING REQUEST
# ============================================================================


class ProcessingJobCreate(BaseModel):
    """
    Request to start document processing.

    Example:

        {
            "document_id": "...",
            "force": false
        }

    `template_id` is optional and retained for compatibility with
    workflow/template-driven processing.
    """

    document_id: UUID

    template_id: UUID | None = None

    force: bool = False


# ============================================================================
# PROCESSING UPDATE
# ============================================================================


class ProcessingJobUpdate(BaseModel):
    """
    Optional processing-job update payload.

    This schema is intended for internal/service-level update
    operations and should not be used as the primary execution
    endpoint response.
    """

    status: ProcessingStatus | None = None

    current_stage: str | None = None

    progress: int | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    started_at: datetime | None = None

    completed_at: datetime | None = None

    error_code: str | None = None

    error_message: str | None = None

    result: dict[str, Any] | None = None


# ============================================================================
# PROCESSING STEP RESPONSE
# ============================================================================


class ProcessingStepResponse(BaseModel):
    """
    API representation of one processing pipeline stage.

    Example:

        {
            "id": "...",
            "name": "ocr",
            "step_order": 4,
            "status": "completed",
            "attempt_count": 1,
            "duration_ms": 2100
        }

    This is designed to be directly consumable by the
    Execution History UI.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    # ------------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------------

    id: UUID

    name: str

    step_order: int

    # ------------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------------

    status: ProcessingStepStatus

    # ------------------------------------------------------------------------
    # Provider
    # ------------------------------------------------------------------------

    provider: str | None = None

    provider_operation: str | None = None

    # ------------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------------

    attempt_count: int = 0

    duration_ms: int | None = None

    # ------------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------------

    input_metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

    output_metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

    # ------------------------------------------------------------------------
    # Errors
    # ------------------------------------------------------------------------

    error_code: str | None = None

    error_message: str | None = None

    # ------------------------------------------------------------------------
    # Timestamps
    # ------------------------------------------------------------------------

    created_at: datetime

    started_at: datetime | None = None

    completed_at: datetime | None = None

    updated_at: datetime


# ============================================================================
# PROCESSING JOB RESPONSE
# ============================================================================


class ProcessingJobResponse(BaseModel):
    """
    Complete processing-job API response.

    This is the main schema for the Execution History UI.

    It contains:

        ProcessingJob
            |
            +-- metadata
            +-- status
            +-- progress
            +-- errors
            +-- result
            +-- steps[]
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    # ------------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------------

    id: UUID

    document_id: UUID

    document_version_id: UUID

    template_id: UUID | None = None

    # ------------------------------------------------------------------------
    # Job state
    # ------------------------------------------------------------------------

    status: ProcessingStatus

    current_stage: str | None = None

    progress: int = Field(
        default=0,
        ge=0,
        le=100,
    )

    # ------------------------------------------------------------------------
    # Timing
    # ------------------------------------------------------------------------

    started_at: datetime | None = None

    completed_at: datetime | None = None

    created_at: datetime

    updated_at: datetime

    # ------------------------------------------------------------------------
    # Errors
    # ------------------------------------------------------------------------

    error_code: str | None = None

    error_message: str | None = None

    # ------------------------------------------------------------------------
    # Result
    # ------------------------------------------------------------------------

    result: dict[str, Any] = Field(
        default_factory=dict,
    )

    # ------------------------------------------------------------------------
    # Pipeline steps
    # ------------------------------------------------------------------------

    steps: list[ProcessingStepResponse] = Field(
        default_factory=list,
    )


# ============================================================================
# PROCESSING JOB LIST RESPONSE
# ============================================================================


class ProcessingJobList(BaseModel):
    """
    Paginated processing-job response.
    """

    items: list[ProcessingJobResponse] = Field(
        default_factory=list,
    )

    total: int

    page: int = 1

    page_size: int = 20


# ============================================================================
# PROCESSING START RESPONSE
# ============================================================================


class ProcessingStartResponse(BaseModel):
    """
    Lightweight response returned immediately after a processing
    job is created.

    This is useful for:

        POST /processing/jobs
    """

    processing_id: UUID

    document_id: UUID

    document_version_id: UUID

    status: ProcessingStatus

    message: str


# ============================================================================
# PROCESSING STATUS RESPONSE
# ============================================================================


class ProcessingStatusResponse(BaseModel):
    """
    Lightweight current-status response.

    Used by:

        GET /processing/{processing_id}

    This is intentionally smaller than ProcessingJobResponse and
    is suitable for polling.
    """

    processing_id: UUID

    document_id: UUID

    document_version_id: UUID

    status: ProcessingStatus

    current_stage: str | None = None

    progress: int = Field(
        default=0,
        ge=0,
        le=100,
    )

    error: str | None = None


# ============================================================================
# EXECUTION HISTORY RESPONSE
# ============================================================================


class ExecutionHistoryResponse(BaseModel):
    """
    Response specifically designed for the Execution History UI.

    This provides the frontend with the execution identity,
    current state, progress, errors, and complete stage history.
    """

    processing_id: UUID

    document_id: UUID

    document_version_id: UUID

    status: ProcessingStatus

    current_stage: str | None = None

    progress: int = Field(
        default=0,
        ge=0,
        le=100,
    )

    error: str | None = None

    steps: list[ProcessingStepResponse] = Field(
        default_factory=list,
    )


# ============================================================================
# EXECUTION HISTORY LIST
# ============================================================================


class ExecutionHistoryList(BaseModel):
    """
    List response for the Execution History page.
    """

    items: list[ExecutionHistoryResponse] = Field(
        default_factory=list,
    )

    total: int

    page: int = 1

    page_size: int = 20


# ============================================================================
# EXPORTS
# ============================================================================


__all__ = [
    "ProcessingStatus",
    "ProcessingStepStatus",
    "ProcessingJobCreate",
    "ProcessingJobUpdate",
    "ProcessingStepResponse",
    "ProcessingJobResponse",
    "ProcessingJobList",
    "ProcessingStartResponse",
    "ProcessingStatusResponse",
    "ExecutionHistoryResponse",
    "ExecutionHistoryList",
]