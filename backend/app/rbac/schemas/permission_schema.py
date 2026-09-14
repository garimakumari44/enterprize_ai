from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PermissionBase(BaseModel):
    resource: str = Field(..., max_length=100)
    action: str = Field(..., max_length=100)
    description: str | None = None


class PermissionCreate(PermissionBase):
    pass


class PermissionUpdate(BaseModel):
    resource: str | None = None
    action: str | None = None
    description: str | None = None


class PermissionResponse(PermissionBase):
    id: UUID

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)