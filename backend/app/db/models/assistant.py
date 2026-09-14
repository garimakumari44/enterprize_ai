
"""
app/db/models/assistant.py

Database models for the Assistant subsystem.

Models
------
AssistantSession
    Represents one assistant conversation.

AssistantMessage
    Represents one message inside an assistant session.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AssistantSession(Base):
    """
    Represents an Assistant conversation session.
    """

    __tablename__ = "assistant_sessions"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    user_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    title: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    metadata_json: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
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

    messages: Mapped[list["AssistantMessage"]] = relationship(
        "AssistantMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="AssistantMessage.created_at",
    )


class AssistantMessage(Base):
    """
    Represents one message in an Assistant session.
    """

    __tablename__ = "assistant_messages"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    session_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "assistant_sessions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    metadata_json: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    session: Mapped["AssistantSession"] = relationship(
        "AssistantSession",
        back_populates="messages",
    )

