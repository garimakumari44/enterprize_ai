"""
app/api/v1/assistant/chat.py

Assistant chat API endpoints.
"""

from __future__ import annotations

import logging

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from app.api.v1.assistant.dependencies import (
    get_assistant_service,
)
from app.schemas.assistant.chat_schema import (
    AssistantRequest,
    AssistantResponse,
    ChatMessage,
)
from app.services.assistant_service import (
    AssistantService,
)


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/assistant",
    tags=["Assistant Chat"],
)


@router.post(
    "/chat",
    response_model=AssistantResponse,
    status_code=status.HTTP_200_OK,
)
async def chat(
    payload: AssistantRequest,
    service: AssistantService = Depends(
        get_assistant_service,
    ),
) -> AssistantResponse:
    """
    Send a message to the assistant and receive a response.

    The API layer is intentionally thin.

    Flow:

        HTTP Request
            ↓
        AssistantService
            ↓
        AssistantOrchestrator
            ↓
        QueryRouter
            ↓
        ContextService
            ↓
        PromptBuilder
            ↓
        LLMManager
            ↓
        AssistantResponse
    """

    try:
        result = await service.chat(
            message=payload.message,
            session_id=payload.session_id,
            context=payload.context,
        )

        return AssistantResponse(
            session_id=result.session_id,
            message=ChatMessage(
                role=result.role,
                content=result.content,
            ),
            model=result.model,
            usage=result.usage,
            metadata=result.metadata or {},
        )

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except TypeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        # Keep the real exception in server logs rather than exposing
        # internal implementation details to the client.
        logger.exception(
            "Assistant request failed: %s",
            exc,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Assistant request failed.",
        ) from exc


__all__ = [
    "router",
]