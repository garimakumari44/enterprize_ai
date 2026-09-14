from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class AssistantEvent(BaseModel):
    """Base assistant event."""

    event_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime = Field(default_factory=datetime.utcnow)
    event_type: str


class AssistantSessionStartedEvent(AssistantEvent):
    event_type: str = "assistant.session.started"

    session_id: UUID
    user_id: UUID


class AssistantMessageCreatedEvent(AssistantEvent):
    event_type: str = "assistant.message.created"

    session_id: UUID
    message_id: UUID
    role: str
    content: str


class AssistantResponseGeneratedEvent(AssistantEvent):
    event_type: str = "assistant.response.generated"

    session_id: UUID
    message_id: UUID
    response: str
    tokens_used: int
    latency_ms: float


class AssistantToolCalledEvent(AssistantEvent):
    event_type: str = "assistant.tool.called"

    session_id: UUID
    tool_name: str
    parameters: dict[str, Any]
    success: bool