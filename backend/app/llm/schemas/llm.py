"""
app/llm/schemas/llm.py

Provider-neutral LLM request and response schemas.

These schemas are used between LLMManager and individual providers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class LLMMessage:
    """A single chat message."""

    role: str
    content: str


@dataclass(slots=True)
class LLMRequest:
    """
    Provider-neutral LLM request.

    The provider receives this object rather than arbitrary
    application-specific arguments.
    """

    messages: list[LLMMessage]

    model: str | None = None

    temperature: float = 0.2

    max_tokens: int | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass(slots=True)
class LLMResponse:
    """
    Provider-neutral LLM response.
    """

    content: str

    model: str

    provider: str

    finish_reason: str | None = None

    usage: dict[str, Any] = field(
        default_factory=dict
    )

    raw: dict[str, Any] | None = None


class LLMProviderError(Exception):
    """Base provider error."""


class LLMRateLimitError(LLMProviderError):
    """Provider rate-limit error."""


class LLMAuthenticationError(LLMProviderError):
    """Provider authentication error."""


class LLMConfigurationError(LLMProviderError):
    """Provider configuration error."""


__all__ = [
    "LLMMessage",
    "LLMRequest",
    "LLMResponse",
    "LLMProviderError",
    "LLMRateLimitError",
    "LLMAuthenticationError",
    "LLMConfigurationError",
]