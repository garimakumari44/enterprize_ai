from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Numeric,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CostType(str, Enum):
    LLM = "llm"
    EMBEDDING = "embedding"
    OCR = "ocr"
    STORAGE = "storage"
    VECTOR_DB = "vector_db"
    COMPUTE = "compute"
    API = "api"
    OTHER = "other"


class UsageCost(Base):
    """
    Tracks every billable action performed by the platform.
    """

    __tablename__ = "usage_costs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    execution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    provider: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    service: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    model_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    cost_type: Mapped[CostType] = mapped_column(
        SQLEnum(CostType),
        nullable=False,
    )

    usage_quantity: Mapped[Decimal] = mapped_column(
        Numeric(18, 6),
        default=0,
        nullable=False,
    )

    unit: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(18, 8),
        default=0,
        nullable=False,
    )

    total_cost: Mapped[Decimal] = mapped_column(
        Numeric(18, 8),
        default=0,
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        default="USD",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )