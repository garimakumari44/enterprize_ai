from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PolicyBase(BaseModel):
    name: str = Field(..., max_length=150)
    effect: str = Field(..., description="allow or deny")
    description: str | None = None

    conditions: dict | None = None


class PolicyCreate(PolicyBase):
    pass


class PolicyUpdate(BaseModel):
    name: str | None = None
    effect: str | None = None
    description: str | None = None
    conditions: dict | None = None


class PolicyResponse(PolicyBase):
    id: UUID

    organization_id: UUID | None = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)