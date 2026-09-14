"""
app/api/v1/router.py

Root API router for API version 1.

Responsibilities
----------------
- Compose all API domain routers.
- Keep domain-specific prefixes isolated.
- Expose one canonical APIRouter to app.main.

Final API structure
-------------------

/api/v1
    /health

    /auth
        ...

    /users
        ...

    /documents
        ...

    /processing
        /jobs
            POST /
            GET /{processing_id}
            POST /{processing_id}/cancel
            GET /{processing_id}/intelligence

        /extractions
            ...

        /validations
            ...

        /reviews
            ...

    /executions
        ...

    /knowledge
        POST /
        POST /hybrid
        GET /history
        GET /similar/{document_id}

    /assistant
        /chat
        /sessions
            POST /
            GET /{session_id}
            GET /{session_id}/history
            DELETE /{session_id}

    /workflows
        ...

Important
---------
The processing router already owns the `/processing` prefix.

The assistant routers also own their prefixes:

    app.api.v1.assistant.chat
        APIRouter(prefix="/assistant")

    app.api.v1.assistant.sessions
        APIRouter(prefix="/assistant/sessions")

Therefore this root router MUST NOT add another prefix for
processing or assistant when including those routers.

Knowledge is different:

    app.api.v1.knowledge.search

currently does NOT own a `/knowledge` prefix.

It exposes the search routes at the router root, so this
root router owns the `/knowledge` prefix.

The resulting knowledge endpoints are:

    POST /api/v1/knowledge/
    POST /api/v1/knowledge/hybrid
    GET  /api/v1/knowledge/history
    GET  /api/v1/knowledge/similar/{document_id}
"""

from __future__ import annotations

from fastapi import APIRouter


# ============================================================================
# CORE API
# ============================================================================

from app.api.v1.auth import (
    router as auth_router,
)

from app.api.v1.health import (
    router as health_router,
)

from app.api.v1.users import (
    router as users_router,
)


# ============================================================================
# DOCUMENTS
# ============================================================================

from app.api.v1.documents import (
    router as documents_router,
)


# ============================================================================
# PROCESSING
# ============================================================================

from app.api.v1.processing import (
    router as processing_router,
)


# ============================================================================
# EXECUTIONS
# ============================================================================

from app.api.v1.executions import (
    router as executions_router,
)


# ============================================================================
# KNOWLEDGE
# ============================================================================

from app.api.v1.knowledge.search import (
    router as knowledge_search_router,
)


# ============================================================================
# ASSISTANT
# ============================================================================

from app.api.v1.assistant.chat import (
    router as assistant_chat_router,
)

from app.api.v1.assistant.sessions import (
    router as assistant_sessions_router,
)


# ============================================================================
# WORKFLOWS
# ============================================================================

from app.api.v1.workflows.workflow_routes import (
    router as workflow_router,
)


# ============================================================================
# ROOT V1 ROUTER
# ============================================================================

router = APIRouter()


# ============================================================================
# HEALTH
# ============================================================================

router.include_router(
    health_router,
    tags=["Health"],
)


# ============================================================================
# AUTHENTICATION
# ============================================================================

router.include_router(
    auth_router,
    tags=["Authentication"],
)


# ============================================================================
# USERS
# ============================================================================

router.include_router(
    users_router,
    prefix="/users",
    tags=["Users"],
)


# ============================================================================
# DOCUMENTS
# ============================================================================

router.include_router(
    documents_router,
    prefix="/documents",
    tags=["Documents"],
)


# ============================================================================
# PROCESSING
# ============================================================================

# IMPORTANT:
#
# processing_router already owns:
#
#     prefix="/processing"
#
# Therefore DO NOT add another `/processing` prefix here.
#
# Final API paths remain:
#
#     /api/v1/processing/...
#
router.include_router(
    processing_router,
    tags=["Processing"],
)


# ============================================================================
# EXECUTIONS
# ============================================================================

router.include_router(
    executions_router,
    tags=["Executions"],
)


# ============================================================================
# KNOWLEDGE
# ============================================================================

# IMPORTANT:
#
# knowledge_search_router currently does NOT own the `/knowledge`
# prefix.
#
# Its routes are declared at the router root.
#
# Therefore this root router owns `/knowledge`.
#
# Final API paths:
#
#     POST /api/v1/knowledge/
#     POST /api/v1/knowledge/hybrid
#     GET  /api/v1/knowledge/history
#     GET  /api/v1/knowledge/similar/{document_id}
#
# DO NOT document or expect:
#
#     /api/v1/knowledge/search/
#     /api/v1/knowledge/search/hybrid
#     /api/v1/knowledge/search/history
#     /api/v1/knowledge/search/similar/{document_id}
#
router.include_router(
    knowledge_search_router,
    prefix="/knowledge",
    tags=["Knowledge Search"],
)


# ============================================================================
# ASSISTANT CHAT
# ============================================================================

# assistant/chat.py already owns:
#
#     prefix="/assistant"
#
# Therefore DO NOT add another `/assistant` prefix here.
#
# Final routes are determined by the routes declared in chat.py.
#
router.include_router(
    assistant_chat_router,
    tags=["Assistant Chat"],
)


# ============================================================================
# ASSISTANT SESSIONS
# ============================================================================

# assistant/sessions.py already owns:
#
#     prefix="/assistant/sessions"
#
# Therefore DO NOT add another `/assistant` prefix here.
#
# Final routes include:
#
#     POST   /api/v1/assistant/sessions
#     GET    /api/v1/assistant/sessions
#     GET    /api/v1/assistant/sessions/{session_id}
#     GET    /api/v1/assistant/sessions/{session_id}/history
#     DELETE /api/v1/assistant/sessions/{session_id}
#
router.include_router(
    assistant_sessions_router,
    tags=["Assistant Sessions"],
)


# ============================================================================
# WORKFLOWS
# ============================================================================

router.include_router(
    workflow_router,
    tags=["Workflows"],
)


# ============================================================================
# PUBLIC EXPORTS
# ============================================================================

__all__ = [
    "router",
]