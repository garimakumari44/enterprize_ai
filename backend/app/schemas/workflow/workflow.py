from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WorkflowBase(BaseModel):
    """
    Shared fields for workflow schemas.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    description: str | None = None

    workflow_type: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    is_active: bool = True

    config: dict[str, Any] = Field(
        default_factory=dict,
    )


class WorkflowCreate(WorkflowBase):
    """
    Request schema for creating a workflow.
    """

    pass


class WorkflowUpdate(BaseModel):
    """
    PATCH schema for workflows.

    All fields are optional.
    """

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    description: str | None = None

    workflow_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    is_active: bool | None = None

    config: dict[str, Any] | None = None


class WorkflowResponse(BaseModel):
    """
    Response returned by the workflow API.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID

    name: str

    description: str | None

    workflow_type: str

    version: int

    is_active: bool

    config: dict[str, Any] = Field(
        default_factory=dict,
    )

    created_at: datetime

    updated_at: datetime