from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(
        ...,
        description="Message role: system, user, assistant"
    )

    content: str


class ChatRequest(BaseModel):
    provider: str = Field(
        default="openai",
        description="AI provider name"
    )

    model: str = Field(
        ...,
        description="Model name e.g gpt-4.1, claude-3"
    )

    messages: List[ChatMessage]

    temperature: Optional[float] = Field(
        default=0.7,
        ge=0,
        le=2
    )

    max_tokens: Optional[int] = None

    metadata: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):

    id: str

    model: str

    message: ChatMessage

    usage: Optional[Dict[str, int]] = None

    metadata: Optional[Dict[str, Any]] = None