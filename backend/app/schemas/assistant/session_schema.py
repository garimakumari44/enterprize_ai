"""
app/schemas/assistant/session_schema.py

Pydantic schemas for assistant conversation sessions.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ---------------------------------------------------------------------------
# Chat Message
# ---------------------------------------------------------------------------


class ChatMessage(BaseModel):
    """
    A single message in an assistant conversation.
    """

    model_config = ConfigDict(
        extra="ignore",
    )

    role: str = Field(
        ...,
        description="Message role.",
        examples=["user", "assistant", "system"],
    )

    content: str = Field(
        ...,
        description="Message content.",
    )


# ---------------------------------------------------------------------------
# Session Creation
# ---------------------------------------------------------------------------


class SessionCreateRequest(BaseModel):
    """
    Request for creating an assistant session.
    """

    model_config = ConfigDict(
        extra="ignore",
    )

    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "Optional application context associated with the session."
        ),
        examples=[
            {
                "company": "Apple Inc.",
                "ticker": "AAPL",
            }
        ],
    )


# ---------------------------------------------------------------------------
# Session Response
# ---------------------------------------------------------------------------


class SessionResponse(BaseModel):
    """
    Assistant session response.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    session_id: UUID = Field(
        ...,
        description="Unique assistant session ID.",
    )

    created_at: datetime = Field(
        ...,
        description="Session creation timestamp.",
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Session metadata.",
    )


# ---------------------------------------------------------------------------
# Session List Response
# ---------------------------------------------------------------------------


class SessionListResponse(BaseModel):
    """
    Response containing multiple assistant sessions.

    The canonical API representation is:

        {
            "sessions": [...],
            "total": 0
        }

    For backwards compatibility, a raw list returned by the service is also
    accepted and normalized into the canonical representation.
    """

    sessions: List[SessionResponse] = Field(
        default_factory=list,
        description="Assistant sessions.",
    )

    total: int = Field(
        default=0,
        ge=0,
        description="Number of sessions returned.",
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_list_response(
        cls,
        value: Any,
    ) -> Any:
        """
        Normalize a raw list returned by the service.

        Example:

            []

        becomes:

            {
                "sessions": [],
                "total": 0,
            }

        And:

            [session1, session2]

        becomes:

            {
                "sessions": [session1, session2],
                "total": 2,
            }
        """

        if isinstance(value, list):
            return {
                "sessions": value,
                "total": len(value),
            }

        return value


# ---------------------------------------------------------------------------
# Chat History Response
# ---------------------------------------------------------------------------


class ChatHistoryResponse(BaseModel):
    """
    Response containing the conversation history for an assistant session.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    session_id: UUID = Field(
        ...,
        description="Unique assistant session ID.",
    )

    messages: List[ChatMessage] = Field(
        default_factory=list,
        description="Messages belonging to the assistant session.",
    )

    total: int = Field(
        default=0,
        ge=0,
        description="Number of messages in the conversation history.",
    )