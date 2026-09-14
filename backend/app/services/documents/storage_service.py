"""
app/services/documents/storage_service.py

Compatibility wrapper for the canonical application storage service.

The canonical storage implementation is:

    app.storage.service.StorageService

This module exists so older imports do not accidentally use the
legacy local-filesystem implementation.
"""

from __future__ import annotations

from app.storage.service import StorageService

__all__ = [
    "StorageService",
]