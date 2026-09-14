from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RoleBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: str | None = None
    is_system: bool = False


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = None
    is_system: bool | None = None


class RoleResponse(RoleBase):
    id: UUID
    organization_id: UUID | None = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)