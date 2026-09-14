"""
app/db/database.py

Central SQLAlchemy database definitions.

This module contains ONLY the declarative Base.

IMPORTANT:
    Do not import ORM models from this file.

    ORM models import Base from here, while the model registry
    imports all ORM models separately.
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Shared SQLAlchemy declarative base.

    All ORM models inherit from this Base.
    """

    pass


__all__ = [
    "Base",
]