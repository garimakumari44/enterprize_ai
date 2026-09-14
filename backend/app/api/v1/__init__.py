
"""
app/api/v1/__init__.py

Public API v1 router.

The complete API v1 route hierarchy is composed in:
    app.api.v1.router

This module provides the public `api_router` export used by
app.main.

Architecture
------------

    app.main
        |
        v
    api_router
        |
        v
    app.api.v1.router.router
        |
        +-- /health
        +-- /auth
        +-- /users
        +-- /documents
        +-- /processing
        |      +-- /jobs
        |      +-- /extractions
        |      +-- /validations
        |      +-- /reviews
        |      +-- /jobs/{processing_id}/intelligence
        |
        +-- /executions
        +-- /knowledge
        +-- /workflows

IMPORTANT
---------

Do not create another APIRouter() in this module.

The canonical v1 router lives in:
    app.api.v1.router
"""

from __future__ import annotations


# ============================================================================
# CANONICAL API V1 ROUTER
# ============================================================================

from app.api.v1.router import (
    router as api_router,
)


# ============================================================================
# PUBLIC EXPORTS
# ============================================================================

__all__ = [
    "api_router",
]

