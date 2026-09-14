"""
Execution Pydantic schemas.

Used for:
- Run workflow
- Execution details
- Execution listing
- Execution logs
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.constants.execution_status import ExecutionStatus


# ==========================================================
# Base
# ==========================================================

class ExecutionBase(BaseModel):
    """Base execution schema."""

    workflow_id: int
    input_data: dict[str, Any] = Field(default_factory=dict)


# ==========================================================
# Create / Run
# ==========================================================

class ExecutionCreate(ExecutionBase):
    """Request schema for starting an execution."""

    pass


# ==========================================================
# Response
# ==========================================================

class ExecutionResponse(BaseModel):
    """Execution response."""

    id: int

    workflow_id: int

    status: ExecutionStatus

    started_at: datetime | None = None
    finished_at: datetime | None = None

    duration_ms: int | None = None

    input_data: dict[str, Any]
    output_data: dict[str, Any]

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# Detail
# ==========================================================

class ExecutionDetailResponse(ExecutionResponse):
    """Detailed execution response."""

    context: dict[str, Any]
    error_message: str | None = None


# ==========================================================
# Log
# ==========================================================

class ExecutionLogResponse(BaseModel):
    """Execution log entry."""

    id: int

    execution_id: int

    node_id: int | None = None

    level: str

    message: str

    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# List
# ==========================================================

class ExecutionListResponse(BaseModel):
    """Execution list response."""

    items: list[ExecutionResponse]

    total: int


# ==========================================================
# Cancel
# ==========================================================

class ExecutionCancelResponse(BaseModel):
    """Execution cancellation response."""

    success: bool

    message: str


# ==========================================================
# Restart
# ==========================================================

class ExecutionRestartResponse(BaseModel):
    """Execution restart response."""

    execution_id: int

    new_execution_id: int

    message: str