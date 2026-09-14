"""
app/llm

Canonical LLM infrastructure package.
"""

from app.llm.providers import (
    OpenRouterProvider,
)

from app.llm.router import (
    ModelRouter,
)

from app.llm.schemas import (
    LLMAuthenticationError,
    LLMConfigurationError,
    LLMMessage,
    LLMProviderError,
    LLMRateLimitError,
    LLMRequest,
    LLMResponse,
)

__all__ = [
    "OpenRouterProvider",
    "ModelRouter",
    "LLMMessage",
    "LLMRequest",
    "LLMResponse",
    "LLMProviderError",
    "LLMRateLimitError",
    "LLMAuthenticationError",
    "LLMConfigurationError",
]