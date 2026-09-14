from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WorkflowStepBase(BaseModel):
    """
    Shared fields for workflow step schemas.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    step_type: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    description: str | None = None

    step_order: int = Field(
        default=0,
        ge=0,
    )

    is_enabled: bool = True

    executor: str | None = Field(
        default=None,
        max_length=150,
    )

    config: dict[str, Any] = Field(
        default_factory=dict,
    )

    data_mapping: dict[str, Any] = Field(
        default_factory=dict,
    )


class WorkflowStepCreate(WorkflowStepBase):
    """
    Request schema for creating a workflow step.
    """

    workflow_id: UUID


class WorkflowStepUpdate(BaseModel):
    """
    Request schema for updating a workflow step.

    All fields are optional so PATCH requests can update
    only the fields supplied by the client.
    """

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    step_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    description: str | None = None

    step_order: int | None = Field(
        default=None,
        ge=0,
    )

    is_enabled: bool | None = None

    executor: str | None = Field(
        default=None,
        max_length=150,
    )

    config: dict[str, Any] | None = None

    data_mapping: dict[str, Any] | None = None


class WorkflowStepResponse(WorkflowStepBase):
    """
    Response schema returned by the API.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID

    workflow_id: UUID