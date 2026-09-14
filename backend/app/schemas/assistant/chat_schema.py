"""
app/schemas/assistant/chat_schema.py

Pydantic schemas for assistant chat operations.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ChatMessage(BaseModel):
    """
    A single conversational message.
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
        min_length=1,
        description="Message content.",
    )

    created_at: Optional[datetime] = Field(
        default=None,
        description="Message creation timestamp.",
    )

    message_id: Optional[UUID] = Field(
        default=None,
        description="Unique message identifier.",
    )

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        value = value.strip().lower()

        allowed_roles = {
            "user",
            "assistant",
            "system",
        }

        if value not in allowed_roles:
            raise ValueError(
                "role must be one of: user, assistant, system"
            )

        return value

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "content cannot be empty"
            )

        return value


class AssistantRequest(BaseModel):
    """
    Request body for sending a message to the assistant.
    """

    model_config = ConfigDict(
        extra="ignore",
    )

    session_id: Optional[UUID] = Field(
        default=None,
        description=(
            "Existing assistant session. "
            "If omitted, a new session is created."
        ),
    )

    message: str = Field(
        ...,
        min_length=1,
        description="User message sent to the assistant.",
        examples=[
            "Analyze the latest financial performance of Apple."
        ],
    )

    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "Optional application context available to the assistant."
        ),
        examples=[
            {
                "company": "Apple Inc.",
                "ticker": "AAPL",
            }
        ],
    )

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "message cannot be empty"
            )

        return value


class AssistantResponse(BaseModel):
    """
    Response returned after an assistant turn.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    session_id: UUID = Field(
        ...,
        description="Assistant conversation session ID.",
    )

    message: ChatMessage = Field(
        ...,
        description="Assistant response message.",
    )

    model: Optional[str] = Field(
        default=None,
        description="Model used to generate the response.",
    )

    usage: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional model token/usage information.",
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional assistant execution metadata.",
    )


class ChatHistoryResponse(BaseModel):
    """
    Response containing conversation history.
    """

    session_id: UUID = Field(
        ...,
        description="Conversation session ID.",
    )

    messages: List[ChatMessage] = Field(
        default_factory=list,
        description="Conversation messages.",
    )

    total: int = Field(
        default=0,
        ge=0,
        description="Number of messages returned.",
    )