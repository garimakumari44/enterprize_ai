"""
app/db/models/folder.py

Folder model.

A Folder is currently an independent organizational entity.

The current document schema does not contain a folder_id foreign key,
so Folder does not define a relationship to Document.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.database  import Base


class Folder(Base):
    """
    Represents a logical folder.

    Note:
        The current documents table does not contain folder_id.
        Therefore this model intentionally does not define
        Folder.documents.
    """

    __tablename__ = "folders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return (
            f"<Folder("
            f"id={self.id!r}, "
            f"name={self.name!r}"
            f")>"
        )