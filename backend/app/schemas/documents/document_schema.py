from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------
# Base
# ---------------------------------------------------------

class DocumentBase(BaseModel):
    filename: str = Field(..., max_length=255)
    original_filename: str = Field(..., max_length=255)

    mime_type: str
    file_size: int

    folder_id: UUID | None = None

    description: str | None = None


# ---------------------------------------------------------
# Create
# ---------------------------------------------------------

class DocumentCreate(DocumentBase):
    pass


# ---------------------------------------------------------
# Update
# ---------------------------------------------------------

class DocumentUpdate(BaseModel):
    filename: str | None = None
    folder_id: UUID | None = None
    description: str | None = None


# ---------------------------------------------------------
# Response
# ---------------------------------------------------------

class DocumentResponse(DocumentBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID

    storage_path: str

    version: int

    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------
# Metadata
# ---------------------------------------------------------

class DocumentMetadata(BaseModel):
    pages: int | None = None
    language: str | None = None
    author: str | None = None
    title: str | None = None


# ---------------------------------------------------------
# Search
# ---------------------------------------------------------

class DocumentSearch(BaseModel):
    query: str | None = None

    folder_id: UUID | None = None

    tag: str | None = None

    mime_type: str | None = None

    page: int = 1
    page_size: int = 20