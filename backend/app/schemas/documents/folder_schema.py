from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------
# Base
# ---------------------------------------------------------

class FolderBase(BaseModel):
    name: str
    parent_id: UUID | None = None


# ---------------------------------------------------------
# Create
# ---------------------------------------------------------

class FolderCreate(FolderBase):
    pass


# ---------------------------------------------------------
# Update
# ---------------------------------------------------------

class FolderUpdate(BaseModel):
    name: str | None = None
    parent_id: UUID | None = None


# ---------------------------------------------------------
# Response
# ---------------------------------------------------------

class FolderResponse(FolderBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID

    created_at: datetime
    updated_at: datetime