"""
app/api/v1/assistant/sessions.py

Assistant session API routes.

Responsibilities
----------------
- Create assistant sessions.
- List assistant sessions.
- Retrieve assistant sessions.
- Retrieve conversation history.
- Delete assistant sessions.

AssistantService is request-scoped.

Application-scoped resources such as PromptBuilder and LLMManager
are reused through the assistant dependency.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Query,
    status,
)

from app.api.v1.assistant.dependencies import (
    get_assistant_service,
)
from app.schemas.assistant.session_schema import (
    ChatHistoryResponse,
    SessionCreateRequest,
    SessionListResponse,
    SessionResponse,
)
from app.services.assistant_service import AssistantService


router = APIRouter(
    prefix="/assistant/sessions",
    tags=["Assistant Sessions"],
)


# ============================================================================
# CREATE SESSION
# ============================================================================


@router.post(
    "",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_session(
    request: SessionCreateRequest,
    assistant_service: AssistantService = Depends(
        get_assistant_service,
    ),
) -> SessionResponse:
    """
    Create a new assistant session.
    """

    return await assistant_service.create_session(
        context=request.context,
    )


# ============================================================================
# LIST SESSIONS
# ============================================================================


@router.get(
    "",
    response_model=SessionListResponse,
)
async def list_sessions(
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
    assistant_service: AssistantService = Depends(
        get_assistant_service,
    ),
) -> SessionListResponse:
    """
    List assistant sessions.
    """

    return await assistant_service.list_sessions(
        limit=limit,
    )


# ============================================================================
# GET SESSION
# ============================================================================


@router.get(
    "/{session_id}",
    response_model=SessionResponse,
)
async def get_session(
    session_id: UUID,
    assistant_service: AssistantService = Depends(
        get_assistant_service,
    ),
) -> SessionResponse:
    """
    Retrieve a single assistant session.
    """

    return await assistant_service.get_session(
        session_id=session_id,
    )


# ============================================================================
# GET HISTORY
# ============================================================================


@router.get(
    "/{session_id}/history",
    response_model=ChatHistoryResponse,
)
async def get_history(
    session_id: UUID,
    assistant_service: AssistantService = Depends(
        get_assistant_service,
    ),
) -> ChatHistoryResponse:
    """
    Retrieve conversation history for a session.
    """

    return await assistant_service.get_history(
        session_id=session_id,
    )


# ============================================================================
# DELETE SESSION
# ============================================================================


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_session(
    session_id: UUID,
    assistant_service: AssistantService = Depends(
        get_assistant_service,
    ),
) -> None:
    """
    Delete an assistant session.
    """

    await assistant_service.delete_session(
        session_id=session_id,
    )

    return None