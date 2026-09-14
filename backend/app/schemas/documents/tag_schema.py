from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------
# Base
# ---------------------------------------------------------

class TagBase(BaseModel):
    name: str


# ---------------------------------------------------------
# Create
# ---------------------------------------------------------

class TagCreate(TagBase):
    pass


# ---------------------------------------------------------
# Update
# ---------------------------------------------------------

class TagUpdate(BaseModel):
    name: str | None = None


# ---------------------------------------------------------
# Response
# ---------------------------------------------------------

class TagResponse(TagBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID

    created_at: datetime