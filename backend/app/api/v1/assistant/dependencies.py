"""
app/api/v1/assistant/dependencies.py

FastAPI dependency wiring for the assistant.

Responsibilities
----------------
- Provide the request-scoped AsyncSession.
- Construct AssistantRepository for that session.
- Construct ConversationManager.
- Construct ContextService for that session.
- Construct AssistantOrchestrator.
- Construct AssistantService.
- Reuse application-scoped PromptBuilder, LLMManager, and QueryRouter.

Important
---------
The database session is NEVER application-scoped.

Request-scoped:
    AsyncSession
    AssistantRepository
    ConversationManager
    ContextService
    AssistantOrchestrator
    AssistantService

Application-scoped:
    PromptBuilder
    LLMManager
    QueryRouter

Architecture
------------
The AssistantRepository is responsible only for conversation persistence.

Enterprise application context is retrieved by ContextService.

ContextService receives the current request-scoped AsyncSession so that
document and processing information can be queried safely without making
the database session application-scoped.
"""

from __future__ import annotations

from typing import Any

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.assistant.context_service import ContextService
from app.assistant.conversation_manager import ConversationManager
from app.assistant.orchestrator import AssistantOrchestrator
from app.db.session import get_async_db
from app.repositories.intelligence.assistant_repository import (
    AssistantRepository,
)
from app.services.assistant_service import AssistantService


# ============================================================================
# APPLICATION STATE HELPER
# ============================================================================


def _get_app_state_dependency(
    request: Request,
    name: str,
) -> Any:
    """
    Retrieve an application-scoped assistant dependency.

    Unlike ContextService, these dependencies do not require the
    request-scoped database session.
    """

    return getattr(
        request.app.state,
        name,
        None,
    )


# ============================================================================
# ASSISTANT SERVICE DEPENDENCY
# ============================================================================


def get_assistant_service(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
) -> AssistantService:
    """
    Construct the complete request-scoped AssistantService.

    Application-scoped dependencies:
        PromptBuilder
        LLMManager
        QueryRouter

    Request-scoped dependencies:
        AsyncSession
        AssistantRepository
        ConversationManager
        ContextService
        AssistantOrchestrator
        AssistantService
    """

    # ========================================================================
    # APPLICATION-SCOPED PROMPT BUILDER
    # ========================================================================

    prompt_builder = _get_app_state_dependency(
        request,
        "assistant_prompt_builder",
    )

    if prompt_builder is None:
        raise RuntimeError(
            "Assistant PromptBuilder has not been initialized."
        )

    # ========================================================================
    # APPLICATION-SCOPED LLM MANAGER
    # ========================================================================

    llm_manager = _get_app_state_dependency(
        request,
        "assistant_llm_manager",
    )

    if llm_manager is None:
        raise RuntimeError(
            "Assistant LLMManager has not been initialized."
        )

    # ========================================================================
    # APPLICATION-SCOPED QUERY ROUTER
    # ========================================================================

    query_router = _get_app_state_dependency(
        request,
        "assistant_query_router",
    )

    if query_router is None:
        raise RuntimeError(
            "Assistant QueryRouter has not been initialized."
        )

    # ========================================================================
    # REQUEST-SCOPED ASSISTANT REPOSITORY
    # ========================================================================

    repository = AssistantRepository(
        db=db,
    )

    # ========================================================================
    # REQUEST-SCOPED CONVERSATION MANAGER
    # ========================================================================

    conversation_manager = ConversationManager(
        repository=repository,
    )

    # ========================================================================
    # REQUEST-SCOPED CONTEXT SERVICE
    # ========================================================================
    #
    # IMPORTANT:
    #
    # ContextService MUST NOT be created in main.py.
    #
    # It needs the current AsyncSession so it can query:
    #
    #     ProcessingJob
    #          |
    #          v
    #     DocumentVersion
    #          |
    #          v
    #       Document
    #
    # The AsyncSession belongs to this HTTP request and is therefore passed
    # directly into ContextService.
    #
    # ========================================================================

    context_service = ContextService(
        db=db,
    )

    # ========================================================================
    # REQUEST-SCOPED ORCHESTRATOR
    # ========================================================================

    orchestrator = AssistantOrchestrator(
        conversation_manager=conversation_manager,
        prompt_builder=prompt_builder,
        llm_manager=llm_manager,
        query_router=query_router,
        context_service=context_service,
    )

    # ========================================================================
    # REQUEST-SCOPED SERVICE
    # ========================================================================

    return AssistantService(
        orchestrator=orchestrator,
    )


# ============================================================================
# EXPORTS
# ============================================================================


__all__ = [
    "get_assistant_service",
]