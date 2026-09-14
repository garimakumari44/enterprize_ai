
"""
app/db/models/collection.py

Logical collection of documents/chunks used for organization and
knowledge retrieval.

A Collection is intentionally independent from Chunk for now.
Documents/chunks can be associated with collections later through
an explicit relationship or mapping table.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Collection(Base):
    """
    Logical grouping of documents for Knowledge Search.

    Examples:
        - Finance Documents
        - Legal Contracts
        - HR Resumes
        - Research Papers
    """

    __tablename__ = "collections"

    # ------------------------------------------------------------------
    # IDENTITY
    # ------------------------------------------------------------------

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
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

    # ------------------------------------------------------------------
    # OPTIONAL METADATA
    # ------------------------------------------------------------------

    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        server_default="'{}'::jsonb",
    )

    # ------------------------------------------------------------------
    # STATUS
    # ------------------------------------------------------------------

    is_active: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
        server_default="true",
        index=True,
    )

    # ------------------------------------------------------------------
    # TIMESTAMPS
    # ------------------------------------------------------------------

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
            f"<Collection("
            f"id={self.id!r}, "
            f"name={self.name!r}, "
            f"is_active={self.is_active!r}"
            f")>"
        )


__all__ = ["Collection"]
