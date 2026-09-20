"""
app/storage/models.py

Application-level models used by the storage layer.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class StorageObject(BaseModel):
    """
    Identifies an object inside object storage.
    """

    model_config = ConfigDict(extra="forbid")

    bucket: str = Field(min_length=1)
    key: str = Field(min_length=1)


class UploadResult(BaseModel):
    """
    Result returned after a successful upload.
    """

    model_config = ConfigDict(extra="forbid")

    bucket: str
    key: str

    etag: Optional[str] = None

    content_type: Optional[str] = None

    size_bytes: Optional[int] = None

    version_id: Optional[str] = None

    uploaded_at: Optional[datetime] = None


class ObjectMetadata(BaseModel):
    """
    Metadata describing an object stored in MinIO.
    """

    model_config = ConfigDict(extra="forbid")

    bucket: str
    key: str

    size_bytes: int = 0

    content_type: Optional[str] = None

    etag: Optional[str] = None

    last_modified: Optional[datetime] = None

    version_id: Optional[str] = None

    metadata: dict[str, str] = Field(default_factory=dict)


class StorageHealth(BaseModel):
    """
    Storage health information.
    """

    model_config = ConfigDict(extra="forbid")

    healthy: bool

    provider: str

    message: Optional[str] = None