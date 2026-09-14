from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuditLogCreate(BaseModel):
    organization_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    user_id: Optional[UUID] = None

    action: str
    resource_type: str
    resource_id: Optional[str] = None

    status: str = "SUCCESS"

    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    metadata: dict[str, Any] = {}


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID

    organization_id: Optional[UUID]
    project_id: Optional[UUID]
    user_id: Optional[UUID]

    action: str
    resource_type: str
    resource_id: Optional[str]

    status: str

    ip_address: Optional[str]
    user_agent: Optional[str]

    metadata: dict[str, Any]

    created_at: datetime


class AuditLogFilter(BaseModel):
    organization_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    user_id: Optional[UUID] = None

    action: Optional[str] = None
    resource_type: Optional[str] = None
    status: Optional[str] = None

    limit: int = 100
    offset: int = 0