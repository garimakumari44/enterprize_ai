from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., examples=["user", "assistant", "system"])
    content: str


class AssistantRequest(BaseModel):
    session_id: Optional[UUID] = None
    message: str
    context: Optional[Dict[str, Any]] = None
    history: List[ChatMessage] = []


class ToolCall(BaseModel):
    tool: str
    arguments: Dict[str, Any]


class AssistantResponse(BaseModel):
    session_id: UUID
    answer: str
    reasoning: Optional[str] = None

    tools_used: List[ToolCall] = []

    citations: List[str] = []

    execution_time_ms: Optional[int] = None

    created_at: datetime