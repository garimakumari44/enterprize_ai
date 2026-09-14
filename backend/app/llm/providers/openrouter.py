"""
app/llm/providers/openrouter.py

OpenRouter provider implementation.

OpenRouter exposes an OpenAI-compatible chat completion API.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.llm.schemas.llm import (
    LLMAuthenticationError,
    LLMConfigurationError,
    LLMProviderError,
    LLMRateLimitError,
    LLMRequest,
    LLMResponse,
)

logger = logging.getLogger(__name__)


class OpenRouterProvider:
    """
    OpenRouter LLM provider.

    The provider accepts only the canonical LLMRequest object.
    Application context is intentionally not accepted here.
    """

    name = "openrouter"

    DEFAULT_BASE_URL = (
        "https://openrouter.ai/api/v1"
    )

    DEFAULT_TIMEOUT = 60.0

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        site_url: str | None = None,
        app_name: str | None = None,
    ) -> None:
        if not api_key or not api_key.strip():
            raise LLMConfigurationError(
                "OPENROUTER_API_KEY is not configured."
            )

        self.api_key = api_key.strip()

        self.base_url = (
            base_url or self.DEFAULT_BASE_URL
        ).rstrip("/")

        self.timeout = float(timeout)

        if self.timeout <= 0:
            raise LLMConfigurationError(
                "OpenRouter timeout must be greater than zero."
            )

        self.site_url = site_url

        self.app_name = app_name

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    async def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
        """
        Generate a completion through OpenRouter.
        """

        self._validate_request(
            request
        )

        payload: dict[str, Any] = {
            "model": request.model,
            "messages": [
                {
                    "role": message.role,
                    "content": message.content,
                }
                for message in request.messages
            ],
            "temperature": request.temperature,
        }

        if request.max_tokens is not None:
            payload["max_tokens"] = (
                request.max_tokens
            )

        headers = {
            "Authorization": (
                f"Bearer {self.api_key}"
            ),
            "Content-Type": "application/json",
        }

        # Optional OpenRouter attribution.
        if self.site_url:
            headers["HTTP-Referer"] = (
                self.site_url
            )

        if self.app_name:
            headers["X-Title"] = (
                self.app_name
            )

        url = (
            f"{self.base_url}"
            "/chat/completions"
        )

        logger.debug(
            "Sending request to OpenRouter | model=%s",
            request.model,
        )

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout
            ) as client:
                response = await client.post(
                    url,
                    headers=headers,
                    json=payload,
                )

        except httpx.TimeoutException as exc:
            raise LLMProviderError(
                "OpenRouter request timed out."
            ) from exc

        except httpx.RequestError as exc:
            raise LLMProviderError(
                f"OpenRouter network error: {exc}"
            ) from exc

        except httpx.HTTPError as exc:
            raise LLMProviderError(
                f"OpenRouter HTTP error: {exc}"
            ) from exc

        # ====================================================================
        # HTTP ERROR HANDLING
        # ====================================================================

        if response.status_code == 401:
            raise LLMAuthenticationError(
                "OpenRouter authentication failed. "
                "Check OPENROUTER_API_KEY."
            )

        if response.status_code == 403:
            raise LLMAuthenticationError(
                "OpenRouter rejected the request."
            )

        if response.status_code == 429:
            detail = self._extract_error(
                response
            )

            raise LLMRateLimitError(
                f"OpenRouter rate limit exceeded: "
                f"{detail}"
            )

        if response.status_code == 402:
            detail = self._extract_error(
                response
            )

            raise LLMProviderError(
                f"OpenRouter credits/billing error: "
                f"{detail}"
            )

        if response.status_code >= 400:
            detail = self._extract_error(
                response
            )

            raise LLMProviderError(
                f"OpenRouter request failed "
                f"with HTTP {response.status_code}: "
                f"{detail}"
            )

        # ====================================================================
        # JSON
        # ====================================================================

        try:
            data = response.json()

        except ValueError as exc:
            raise LLMProviderError(
                "OpenRouter returned invalid JSON."
            ) from exc

        if not isinstance(
            data,
            dict,
        ):
            raise LLMProviderError(
                "OpenRouter returned an invalid response."
            )

        # ====================================================================
        # ERROR OBJECT INSIDE RESPONSE
        # ====================================================================

        error = data.get(
            "error"
        )

        if error:
            if isinstance(
                error,
                dict,
            ):
                message = error.get(
                    "message"
                ) or str(error)

                code = error.get(
                    "code"
                )

                if code == 429:
                    raise LLMRateLimitError(
                        str(message)
                    )

                raise LLMProviderError(
                    str(message)
                )

            raise LLMProviderError(
                str(error)
            )

        # ====================================================================
        # CHOICES
        # ====================================================================

        choices = data.get(
            "choices"
        )

        if not isinstance(
            choices,
            list,
        ) or not choices:
            raise LLMProviderError(
                "OpenRouter returned no completion choices."
            )

        choice = choices[0]

        if not isinstance(
            choice,
            dict,
        ):
            raise LLMProviderError(
                "OpenRouter returned an invalid completion choice."
            )

        message = choice.get(
            "message"
        )

        if not isinstance(
            message,
            dict,
        ):
            raise LLMProviderError(
                "OpenRouter response contains no message."
            )

        content = message.get(
            "content"
        )

        if content is None:
            raise LLMProviderError(
                "OpenRouter returned empty content."
            )

        content = str(
            content
        ).strip()

        if not content:
            raise LLMProviderError(
                "OpenRouter returned empty content."
            )

        # ====================================================================
        # RESPONSE NORMALIZATION
        # ====================================================================

        model = str(
            data.get(
                "model"
            )
            or request.model
            or ""
        )

        finish_reason = choice.get(
            "finish_reason"
        )

        usage = data.get(
            "usage"
        )

        if not isinstance(
            usage,
            dict,
        ):
            usage = {}

        return LLMResponse(
            content=content,
            model=model,
            provider=self.name,
            finish_reason=(
                str(finish_reason)
                if finish_reason
                else None
            ),
            usage=dict(
                usage
            ),
            raw=data,
        )

    # ========================================================================
    # VALIDATION
    # ========================================================================

    @staticmethod
    def _validate_request(
        request: LLMRequest,
    ) -> None:
        if not request.messages:
            raise ValueError(
                "messages cannot be empty."
            )

        if not request.model:
            raise LLMConfigurationError(
                "OpenRouter model is not configured."
            )

        if not (
            0.0
            <= request.temperature
            <= 2.0
        ):
            raise ValueError(
                "temperature must be between 0.0 and 2.0."
            )

        if (
            request.max_tokens is not None
            and request.max_tokens <= 0
        ):
            raise ValueError(
                "max_tokens must be greater than zero."
            )

    # ========================================================================
    # ERROR EXTRACTION
    # ========================================================================

    @staticmethod
    def _extract_error(
        response: httpx.Response,
    ) -> str:
        try:
            data = response.json()

        except ValueError:
            text = response.text.strip()

            return (
                text[:1000]
                if text
                else "Unknown OpenRouter error."
            )

        if isinstance(
            data,
            dict,
        ):
            error = data.get(
                "error"
            )

            if isinstance(
                error,
                dict,
            ):
                message = error.get(
                    "message"
                )

                if message:
                    return str(
                        message
                    )

                return str(
                    error
                )

            if error:
                return str(
                    error
                )

        return (
            response.text[:1000]
            or "Unknown OpenRouter error."
        )

    # ========================================================================
    # HEALTH
    # ========================================================================

    async def health_check(
        self,
    ) -> dict[str, Any]:
        """
        Lightweight configuration health check.

        Does not call a model and therefore does not consume
        model credits.
        """

        if not self.api_key:
            return {
                "status": "unhealthy",
                "provider": self.name,
                "error": "API key is missing.",
            }

        return {
            "status": "configured",
            "provider": self.name,
            "base_url": self.base_url,
        }


__all__ = [
    "OpenRouterProvider",
]