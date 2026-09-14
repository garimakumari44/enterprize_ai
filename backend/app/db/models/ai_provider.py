
"""
app/db/models/ai_provider.py

Database model for configured AI providers.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AIProvider(Base):
    """
    Represents a configured AI provider.

    Examples:
        openrouter
        ollama
        anthropic
        google
        local
    """

    __tablename__ = "ai_providers"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    endpoint: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
    )

    default_model: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    config: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        index=True,
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

    secrets: Mapped[List["AISecret"]] = relationship(
        "AISecret",
        back_populates="provider",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"AIProvider("
            f"id={self.id}, "
            f"name='{self.name}', "
            f"type='{self.type}', "
            f"is_active={self.is_active}"
            f")"
        )

