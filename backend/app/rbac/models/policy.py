from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Policy(Base):
    """
    Attribute-Based Access Control (ABAC) policy.

    Example conditions:

    {
        "organization_only": true,
        "owner_only": true,
        "department": "finance",
        "max_amount": 10000
    }
    """

    __tablename__ = "policies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    role_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    permission_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        unique=True,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    resource: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    effect: Mapped[str] = mapped_column(
        String(20),
        default="allow",
        nullable=False,
    )

    conditions: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    priority: Mapped[int] = mapped_column(
        default=100,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return (
            f"<Policy(name='{self.name}', effect='{self.effect}')>"
        )