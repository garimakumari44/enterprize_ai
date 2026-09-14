"""
app/db/base.py

Compatibility layer for the application's SQLAlchemy Base.

IMPORTANT:
    This file must NOT import ORM models.

    Importing models here creates circular imports because individual
    model files themselves import Base from app.db.base.

The model registry is responsible for importing all models.
"""

from __future__ import annotations

from app.db.database import Base


__all__ = [
    "Base",
]