
"""
app/db/models/ai_secret.py

Database model for AI provider credentials.

The actual credential is stored in encrypted form.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AISecret(Base):
    """
    Stores credentials associated with an AI provider.

    `encrypted_value` must contain an encrypted credential,
    never a plaintext API key.
    """

    __tablename__ = "ai_secrets"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    provider_id: Mapped[int] = mapped_column(
        ForeignKey(
            "ai_providers.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    encrypted_value: Mapped[str] = mapped_column(
        String(4096),
        nullable=False,
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

    provider: Mapped["AIProvider"] = relationship(
        "AIProvider",
        back_populates="secrets",
    )

    def __repr__(self) -> str:
        return (
            f"AISecret("
            f"id={self.id}, "
            f"name='{self.name}', "
            f"provider_id={self.provider_id}"
            f")"
        )

