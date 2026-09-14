"""
app/services/llm_manager.py

Canonical LLM execution manager for Orion AI.

Architecture
------------

    AssistantOrchestrator
            |
            v
       PromptBuilder
            |
            v
       LLMManager
            |
            v
       ModelRouter
            |
            v
     OpenRouterProvider
            |
            v
        OpenRouter
            |
            v
          Model

Responsibilities
----------------
- Normalize LLM requests.
- Normalize chat messages.
- Build prompts when PromptBuilder is supplied.
- Resolve providers.
- Route models through ModelRouter.
- Execute OpenRouter through the canonical provider interface.
- Prevent empty-message requests.
- Never pass application context directly to providers.
- Normalize provider responses.
- Support controlled model fallbacks.
- Preserve compatibility with existing callers.
- Expose health/status information.

IMPORTANT
---------

Application context belongs to PromptBuilder.

Provider calls receive only provider-supported data:

    messages
    model
    temperature
    max_tokens
    metadata

The manager NEVER calls:

    provider(..., context=context)

This prevents errors such as:

    unexpected keyword argument 'context'

"""

from __future__ import annotations

import inspect
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from app.llm.providers import OpenRouterProvider
from app.llm.router import ModelRouter
from app.llm.schemas import (
    LLMMessage as ProviderLLMMessage,
    LLMRequest as ProviderLLMRequest,
    LLMResponse as ProviderLLMResponse,
    LLMAuthenticationError as ProviderAuthenticationError,
    LLMConfigurationError as ProviderConfigurationError,
    LLMProviderError as ProviderError,
    LLMRateLimitError as ProviderRateLimitError,
)

logger = logging.getLogger(__name__)


# ============================================================================
# TYPES
# ============================================================================

Message = dict[str, str]


@dataclass(slots=True)
class LLMRequest:
    """
    Canonical application-level LLM request.

    This request is intentionally independent from any provider SDK.
    """

    messages: list[Message]

    model: str | None = None
    provider: str | None = None

    temperature: float = 0.2
    max_tokens: int | None = 2048

    task: str = "chat"

    context: dict[str, Any] | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass(slots=True)
class LLMResponse:
    """
    Canonical application-level LLM response.
    """

    content: str

    model: str | None = None
    provider: str | None = None

    finish_reason: str | None = None

    usage: dict[str, Any] = field(
        default_factory=dict
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    raw: Any = None

    @property
    def text(self) -> str:
        """
        Compatibility alias.
        """
        return self.content

    def to_dict(self) -> dict[str, Any]:
        """
        Convert response to a JSON-safe dictionary.
        """

        return {
            "content": self.content,
            "text": self.content,
            "model": self.model,
            "provider": self.provider,
            "finish_reason": self.finish_reason,
            "usage": self.usage,
            "metadata": self.metadata,
        }


# ============================================================================
# EXCEPTIONS
# ============================================================================


class LLMError(RuntimeError):
    """Base LLM execution error."""


class LLMConfigurationError(LLMError):
    """Raised when LLM configuration is invalid."""


class LLMValidationError(LLMError):
    """Raised when an LLM request is invalid."""


class LLMProviderError(LLMError):
    """Raised when an LLM provider fails."""


class LLMRateLimitError(LLMProviderError):
    """Raised when a provider rate-limits the request."""


class LLMCreditExhaustedError(LLMProviderError):
    """Raised when provider credits are exhausted."""


# ============================================================================
# MANAGER
# ============================================================================


class LLMManager:
    """
    Canonical application-level LLM manager.
    """

    DEFAULT_PROVIDER = "openrouter"

    DEFAULT_MODEL = "openrouter/free"

    DEFAULT_TEMPERATURE = 0.2

    DEFAULT_MAX_TOKENS = 2048

    MAX_MESSAGES = 100

    DEFAULT_FALLBACK_MODELS = (
        "meta-llama/llama-3.3-70b-instruct",
        "google/gemma-4-26b-a4b-it:free",
        "mistralai/mistral-small-3.2-24b-instruct:free",
        "deepseek/deepseek-chat-v3-0324:free",
    )

    def __init__(
        self,
        provider: Any | None = None,
        *,
        providers: Mapping[str, Any] | None = None,
        provider_name: str | None = None,
        model: str | None = None,
        default_model: str | None = None,
        fallback_models: Sequence[str] | None = None,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        prompt_builder: Any | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize LLMManager.

        Existing callers may still pass:

            provider=...
            providers=...
            model=...
            default_model=...
            prompt_builder=...

        Additional kwargs are retained for compatibility.
        """

        self.providers: dict[str, Any] = dict(
            providers or {}
        )

        self.provider_name = (
            provider_name
            or os.getenv("LLM_PROVIDER")
            or self.DEFAULT_PROVIDER
        )

        self.default_model = (
            model
            or default_model
            or os.getenv("LLM_MODEL")
            or os.getenv("OPENROUTER_MODEL")
            or self.DEFAULT_MODEL
        )

        self.temperature = self._validate_temperature(
            temperature
        )

        self.max_tokens = self._validate_max_tokens(
            max_tokens
        )

        self.prompt_builder = prompt_builder

        self.config = dict(kwargs)

        self.fallback_models = self._normalize_models(
            fallback_models
            if fallback_models is not None
            else self._models_from_environment()
        )

        # ---------------------------------------------------------------
        # Explicit provider supplied by dependency injection
        # ---------------------------------------------------------------

        if provider is not None:
            self.providers.setdefault(
                self.provider_name,
                provider,
            )

        # ---------------------------------------------------------------
        # Automatically create OpenRouter provider when configured
        # ---------------------------------------------------------------

        if (
            self.provider_name == "openrouter"
            and "openrouter" not in self.providers
        ):
            api_key = os.getenv(
                "OPENROUTER_API_KEY"
            )

            if api_key:
                try:
                    self.providers["openrouter"] = (
                        OpenRouterProvider(
                            api_key=api_key,
                            base_url=os.getenv(
                                "OPENROUTER_BASE_URL",
                                OpenRouterProvider.DEFAULT_BASE_URL,
                            ),
                            timeout=float(
                                os.getenv(
                                    "OPENROUTER_TIMEOUT",
                                    "60",
                                )
                            ),
                            site_url=os.getenv(
                                "OPENROUTER_SITE_URL"
                            ),
                            app_name=os.getenv(
                                "OPENROUTER_APP_NAME"
                            ),
                        )
                    )

                    logger.info(
                        "OpenRouter provider initialized."
                    )

                except Exception:
                    logger.exception(
                        "Failed to initialize OpenRouter provider."
                    )

        logger.info(
            "LLMManager initialized | provider=%s model=%s",
            self.provider_name,
            self.default_model,
        )

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    async def generate(
        self,
        prompt: str | None = None,
        *,
        messages: Sequence[Mapping[str, Any]] | None = None,
        model: str | None = None,
        provider: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        context: Mapping[str, Any] | None = None,
        task: str = "chat",
        system_prompt: str | None = None,
        metadata: Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Generate text.

        Compatibility examples:

            await manager.generate(
                "Explain this document."
            )

        or:

            await manager.generate(
                messages=[
                    {
                        "role": "user",
                        "content": "Hello",
                    }
                ]
            )
        """

        normalized_messages = self._prepare_messages(
            prompt=prompt,
            messages=messages,
            system_prompt=system_prompt,
            context=context,
        )

        response = await self.chat(
            messages=normalized_messages,
            model=model,
            provider=provider,
            temperature=temperature,
            max_tokens=max_tokens,
            task=task,
            metadata=metadata,
            **kwargs,
        )

        return response.content

    async def chat(
        self,
        messages: Sequence[Mapping[str, Any]] | None = None,
        *,
        model: str | None = None,
        provider: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        context: Mapping[str, Any] | None = None,
        task: str = "chat",
        system_prompt: str | None = None,
        metadata: Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Execute a chat request.

        `context` is used only while constructing prompts.

        It is never sent directly to the provider.
        """

        normalized_messages = self._prepare_messages(
            prompt=None,
            messages=messages,
            system_prompt=system_prompt,
            context=context,
        )

        request = LLMRequest(
            messages=normalized_messages,
            model=model or self.default_model,
            provider=provider or self.provider_name,
            temperature=(
                self.temperature
                if temperature is None
                else self._validate_temperature(
                    temperature
                )
            ),
            max_tokens=(
                self.max_tokens
                if max_tokens is None
                else self._validate_max_tokens(
                    max_tokens
                )
            ),
            task=task or "chat",
            context=(
                dict(context)
                if context
                else None
            ),
            metadata=dict(
                metadata or {}
            ),
        )

        self._validate_request(request)

        return await self._execute_with_fallback(
            request,
            **kwargs,
        )

    async def complete(
        self,
        prompt: str,
        *,
        model: str | None = None,
        provider: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        context: Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Compatibility alias for generate().
        """

        return await self.generate(
            prompt=prompt,
            model=model,
            provider=provider,
            temperature=temperature,
            max_tokens=max_tokens,
            context=context,
            **kwargs,
        )

    async def generate_response(
        self,
        prompt: str,
        *,
        context: Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Compatibility helper.
        """

        return await self.generate(
            prompt=prompt,
            context=context,
            **kwargs,
        )

    # ========================================================================
    # PROMPT PREPARATION
    # ========================================================================

    def _prepare_messages(
        self,
        *,
        prompt: str | None,
        messages: Sequence[Mapping[str, Any]] | None,
        system_prompt: str | None,
        context: Mapping[str, Any] | None,
    ) -> list[Message]:
        """
        Prepare final provider-ready messages.

        Priority:

        1. Explicit messages
        2. PromptBuilder
        3. Direct prompt construction
        """

        explicit_messages = self._normalize_messages(
            messages
        )

        if explicit_messages:
            return self._ensure_non_empty_messages(
                explicit_messages
            )

        if self.prompt_builder is not None:
            builder_messages = (
                self._build_with_prompt_builder(
                    prompt=prompt,
                    context=context,
                    system_prompt=system_prompt,
                )
            )

            if builder_messages:
                return self._ensure_non_empty_messages(
                    builder_messages
                )

        fallback_messages: list[Message] = []

        if system_prompt:
            normalized_system = str(
                system_prompt
            ).strip()

            if normalized_system:
                fallback_messages.append(
                    {
                        "role": "system",
                        "content": normalized_system,
                    }
                )

        if prompt is not None:
            normalized_prompt = str(
                prompt
            ).strip()

            if normalized_prompt:
                fallback_messages.append(
                    {
                        "role": "user",
                        "content": normalized_prompt,
                    }
                )

        return self._ensure_non_empty_messages(
            fallback_messages
        )

    def _build_with_prompt_builder(
        self,
        *,
        prompt: str | None,
        context: Mapping[str, Any] | None,
        system_prompt: str | None,
    ) -> list[Message]:
        """
        Use PromptBuilder without tightly coupling to its implementation.
        """

        builder = self.prompt_builder

        history: list[dict[str, Any]] = []

        if prompt:
            history.append(
                {
                    "role": "user",
                    "content": prompt,
                }
            )

        effective_context = dict(
            context or {}
        )

        if system_prompt:
            effective_context.setdefault(
                "_system_prompt",
                system_prompt,
            )

        try:
            build_messages = getattr(
                builder,
                "build_messages",
                None,
            )

            if callable(build_messages):
                result = build_messages(
                    history=history,
                    context=effective_context,
                )

                return self._normalize_messages(
                    result
                )

            build = getattr(
                builder,
                "build",
                None,
            )

            if callable(build):
                result = build(
                    history=history,
                    context=effective_context,
                )

                if hasattr(
                    result,
                    "as_messages",
                ):
                    result = result.as_messages()

                return self._normalize_messages(
                    result
                )

        except TypeError:
            logger.debug(
                "PromptBuilder signature mismatch.",
                exc_info=True,
            )

        except Exception:
            logger.warning(
                "PromptBuilder failed.",
                exc_info=True,
            )

        return []

    # ========================================================================
    # EXECUTION
    # ========================================================================

    async def _execute_with_fallback(
        self,
        request: LLMRequest,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Execute primary model followed by configured fallback models.
        """

        models = self._build_model_sequence(
            request.model
        )

        last_error: Exception | None = None

        for attempt, model_name in enumerate(
            models,
            start=1,
        ):
            attempt_request = LLMRequest(
                messages=list(
                    request.messages
                ),
                model=model_name,
                provider=request.provider,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                task=request.task,
                context=request.context,
                metadata=dict(
                    request.metadata
                ),
            )

            logger.info(
                "LLM execution attempt | "
                "provider=%s model=%s task=%s attempt=%s",
                attempt_request.provider,
                attempt_request.model,
                attempt_request.task,
                attempt,
            )

            started = time.perf_counter()

            try:
                response = await self._execute_provider(
                    attempt_request,
                    **kwargs,
                )

                elapsed_ms = (
                    time.perf_counter()
                    - started
                ) * 1000.0

                response.metadata.setdefault(
                    "latency_ms",
                    round(
                        elapsed_ms,
                        3,
                    ),
                )

                response.metadata.setdefault(
                    "attempt",
                    attempt,
                )

                return response

            except LLMValidationError:
                raise

            except LLMConfigurationError:
                raise

            except Exception as exc:
                last_error = exc

                logger.warning(
                    "LLM execution failed | "
                    "provider=%s model=%s attempt=%s error=%s",
                    attempt_request.provider,
                    attempt_request.model,
                    attempt,
                    exc,
                )

        attempted = ", ".join(
            f"{request.provider}/{model}"
            for model in models
        )

        message = (
            "All LLM execution attempts failed. "
            f"Attempted: {attempted}"
        )

        if last_error is not None:
            message = (
                f"{message}. "
                f"Last error: {last_error}"
            )

        raise LLMProviderError(
            message
        ) from last_error

    async def _execute_provider(
        self,
        request: LLMRequest,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Execute a provider request.

        Supports the new canonical provider interface:

            provider.generate(
                ProviderLLMRequest(...)
            )

        Also supports legacy providers exposing:

            provider.chat(...)
        """

        provider = self._resolve_provider(
            request.provider
        )

        # ------------------------------------------------------------------
        # New canonical provider interface
        # ------------------------------------------------------------------

        generate_method = getattr(
            provider,
            "generate",
            None,
        )

        if callable(generate_method):
            provider_request = ProviderLLMRequest(
                messages=[
                    ProviderLLMMessage(
                        role=message["role"],
                        content=message["content"],
                    )
                    for message in request.messages
                ],
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                metadata=dict(
                    request.metadata
                ),
            )

            try:
                result = generate_method(
                    provider_request
                )

                if inspect.isawaitable(result):
                    result = await result

            except Exception as exc:
                raise self._classify_provider_exception(
                    exc
                ) from exc

            return self._normalize_provider_response(
                result,
                request=request,
            )

        # ------------------------------------------------------------------
        # Legacy provider interface
        # ------------------------------------------------------------------

        chat_method = getattr(
            provider,
            "chat",
            None,
        )

        if callable(chat_method):
            provider_kwargs: dict[str, Any] = {
                "messages": request.messages,
                "model": request.model,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
            }

            provider_kwargs.update(
                self._filter_supported_kwargs(
                    chat_method,
                    kwargs,
                )
            )

            try:
                result = chat_method(
                    **provider_kwargs
                )

                if inspect.isawaitable(result):
                    result = await result

            except Exception as exc:
                raise self._classify_provider_exception(
                    exc
                ) from exc

            return self._normalize_provider_response(
                result,
                request=request,
            )

        raise LLMConfigurationError(
            f"Provider '{request.provider}' does not "
            "implement generate() or chat()."
        )

    # ========================================================================
    # PROVIDER RESOLUTION
    # ========================================================================

    def _resolve_provider(
        self,
        provider_name: str | None,
    ) -> Any:
        """
        Resolve provider instance.
        """

        name = (
            provider_name
            or self.provider_name
        ).strip()

        if name in self.providers:
            return self.providers[name]

        candidates = (
            name,
            name.replace("-", "_"),
        )

        for candidate in candidates:
            provider = getattr(
                self,
                candidate,
                None,
            )

            if provider is not None:
                return provider

        client = getattr(
            self,
            "client",
            None,
        )

        if client is not None:
            return client

        raise LLMConfigurationError(
            f"LLM provider '{name}' is not configured."
        )

    # ========================================================================
    # RESPONSE NORMALIZATION
    # ========================================================================

    def _normalize_provider_response(
        self,
        result: Any,
        *,
        request: LLMRequest,
    ) -> LLMResponse:
        """
        Normalize all supported provider response types.
        """

        if result is None:
            raise LLMProviderError(
                "LLM provider returned no response."
            )

        # ---------------------------------------------------------------
        # Application-level response
        # ---------------------------------------------------------------

        if isinstance(
            result,
            LLMResponse,
        ):
            if not result.content.strip():
                raise LLMProviderError(
                    "LLM provider returned empty content."
                )

            return result

        # ---------------------------------------------------------------
        # New provider response
        # ---------------------------------------------------------------

        if isinstance(
            result,
            ProviderLLMResponse,
        ):
            content = str(
                result.content or ""
            ).strip()

            if not content:
                raise LLMProviderError(
                    "LLM provider returned empty content."
                )

            return LLMResponse(
                content=content,
                model=result.model or request.model,
                provider=result.provider or request.provider,
                finish_reason=result.finish_reason,
                usage=dict(
                    result.usage or {}
                ),
                raw=result.raw or result,
            )

        # ---------------------------------------------------------------
        # String
        # ---------------------------------------------------------------

        if isinstance(
            result,
            str,
        ):
            content = result.strip()

            if not content:
                raise LLMProviderError(
                    "LLM provider returned empty content."
                )

            return LLMResponse(
                content=content,
                model=request.model,
                provider=request.provider,
                raw=result,
            )

        # ---------------------------------------------------------------
        # Mapping
        # ---------------------------------------------------------------

        if isinstance(
            result,
            Mapping,
        ):
            content = self._extract_content(
                result
            )

            if not content:
                raise LLMProviderError(
                    "LLM provider response contained "
                    "no usable content."
                )

            return LLMResponse(
                content=content,
                model=str(
                    result.get("model")
                    or request.model
                ),
                provider=str(
                    result.get("provider")
                    or request.provider
                ),
                finish_reason=self._extract_finish_reason(
                    result
                ),
                usage=self._extract_usage(
                    result
                ),
                raw=result,
            )

        # ---------------------------------------------------------------
        # Object response
        # ---------------------------------------------------------------

        content = self._extract_object_content(
            result
        )

        if not content:
            raise LLMProviderError(
                "Unable to extract content from provider "
                f"response type {type(result).__name__}."
            )

        usage = getattr(
            result,
            "usage",
            None,
        )

        if not isinstance(
            usage,
            Mapping,
        ):
            usage = {}

        return LLMResponse(
            content=content,
            model=str(
                getattr(
                    result,
                    "model",
                    None,
                )
                or request.model
            ),
            provider=str(
                getattr(
                    result,
                    "provider",
                    None,
                )
                or request.provider
            ),
            finish_reason=(
                str(
                    getattr(
                        result,
                        "finish_reason",
                        None,
                    )
                )
                if getattr(
                    result,
                    "finish_reason",
                    None,
                )
                else None
            ),
            usage=dict(
                usage
            ),
            raw=result,
        )

    @classmethod
    def _extract_content(
        cls,
        response: Mapping[str, Any],
    ) -> str:
        direct = response.get(
            "content"
        )

        if isinstance(
            direct,
            str,
        ) and direct.strip():
            return direct.strip()

        choices = response.get(
            "choices"
        )

        if isinstance(
            choices,
            Sequence,
        ) and not isinstance(
            choices,
            (str, bytes),
        ):
            for choice in choices:
                if not isinstance(
                    choice,
                    Mapping,
                ):
                    continue

                message = choice.get(
                    "message"
                )

                if isinstance(
                    message,
                    Mapping,
                ):
                    content = message.get(
                        "content"
                    )

                    if isinstance(
                        content,
                        str,
                    ) and content.strip():
                        return content.strip()

                text = choice.get(
                    "text"
                )

                if isinstance(
                    text,
                    str,
                ) and text.strip():
                    return text.strip()

        output = response.get(
            "output"
        )

        if isinstance(
            output,
            str,
        ) and output.strip():
            return output.strip()

        return ""

    @classmethod
    def _extract_object_content(
        cls,
        response: Any,
    ) -> str:
        content = getattr(
            response,
            "content",
            None,
        )

        if isinstance(
            content,
            str,
        ) and content.strip():
            return content.strip()

        choices = getattr(
            response,
            "choices",
            None,
        )

        if choices:
            for choice in choices:
                message = getattr(
                    choice,
                    "message",
                    None,
                )

                if message is not None:
                    message_content = getattr(
                        message,
                        "content",
                        None,
                    )

                    if isinstance(
                        message_content,
                        str,
                    ) and message_content.strip():
                        return message_content.strip()

                text = getattr(
                    choice,
                    "text",
                    None,
                )

                if isinstance(
                    text,
                    str,
                ) and text.strip():
                    return text.strip()

        output = getattr(
            response,
            "output",
            None,
        )

        if isinstance(
            output,
            str,
        ) and output.strip():
            return output.strip()

        return ""

    @staticmethod
    def _extract_usage(
        response: Mapping[str, Any],
    ) -> dict[str, Any]:
        usage = response.get(
            "usage"
        )

        if isinstance(
            usage,
            Mapping,
        ):
            return dict(
                usage
            )

        return {}

    @staticmethod
    def _extract_finish_reason(
        response: Mapping[str, Any],
    ) -> str | None:
        finish_reason = response.get(
            "finish_reason"
        )

        if finish_reason:
            return str(
                finish_reason
            )

        choices = response.get(
            "choices"
        )

        if isinstance(
            choices,
            Sequence,
        ) and not isinstance(
            choices,
            (str, bytes),
        ):
            for choice in choices:
                if isinstance(
                    choice,
                    Mapping,
                ):
                    value = choice.get(
                        "finish_reason"
                    )

                    if value:
                        return str(
                            value
                        )

        return None

    # ========================================================================
    # MESSAGE NORMALIZATION
    # ========================================================================

    @classmethod
    def _normalize_messages(
        cls,
        messages: Sequence[Mapping[str, Any]] | None,
    ) -> list[Message]:
        if not messages:
            return []

        normalized: list[Message] = []

        for raw_message in messages:
            if not isinstance(
                raw_message,
                Mapping,
            ):
                continue

            role = raw_message.get(
                "role"
            )

            content = raw_message.get(
                "content"
            )

            if not isinstance(
                role,
                str,
            ):
                continue

            if content is None:
                continue

            role = role.strip().lower()

            if role not in {
                "system",
                "user",
                "assistant",
            }:
                continue

            content = cls._content_to_string(
                content
            ).strip()

            if not content:
                continue

            normalized.append(
                {
                    "role": role,
                    "content": content,
                }
            )

        if len(normalized) > cls.MAX_MESSAGES:
            normalized = normalized[
                -cls.MAX_MESSAGES:
            ]

        return normalized

    @staticmethod
    def _content_to_string(
        content: Any,
    ) -> str:
        if isinstance(
            content,
            str,
        ):
            return content

        if isinstance(
            content,
            Sequence,
        ) and not isinstance(
            content,
            (str, bytes),
        ):
            parts: list[str] = []

            for item in content:
                if isinstance(
                    item,
                    Mapping,
                ):
                    text = item.get(
                        "text"
                    )

                    if text is not None:
                        parts.append(
                            str(text)
                        )
                    else:
                        parts.append(
                            str(item)
                        )
                else:
                    parts.append(
                        str(item)
                    )

            return "\n".join(
                parts
            )

        return str(content)

    # ========================================================================
    # VALIDATION
    # ========================================================================

    @classmethod
    def _ensure_non_empty_messages(
        cls,
        messages: list[Message],
    ) -> list[Message]:
        if not messages:
            raise LLMValidationError(
                "LLM request produced no messages. "
                "Provide a non-empty prompt or message list."
            )

        return messages

    @classmethod
    def _validate_request(
        cls,
        request: LLMRequest,
    ) -> None:
        if not request.messages:
            raise LLMValidationError(
                "messages cannot be empty."
            )

        if len(
            request.messages
        ) > cls.MAX_MESSAGES:
            raise LLMValidationError(
                f"Too many messages. Maximum is "
                f"{cls.MAX_MESSAGES}."
            )

        if not request.model:
            raise LLMConfigurationError(
                "LLM model is not configured."
            )

        if not request.provider:
            raise LLMConfigurationError(
                "LLM provider is not configured."
            )

        if not (
            0.0
            <= request.temperature
            <= 2.0
        ):
            raise LLMValidationError(
                "temperature must be between 0.0 and 2.0."
            )

        if request.max_tokens is not None:
            if request.max_tokens <= 0:
                raise LLMValidationError(
                    "max_tokens must be greater than zero."
                )

    # ========================================================================
    # MODEL ROUTING
    # ========================================================================

    def _build_model_sequence(
        self,
        primary_model: str | None,
    ) -> list[str]:
        """
        Use ModelRouter for deterministic model selection.
        """

        router = ModelRouter(
            default_model=(
                primary_model
                or self.default_model
            ),
            fallback_models=list(
                self.fallback_models
            ),
        )

        selected = router.select_model(
            primary_model
        )

        models = [
            selected,
            *router.get_fallback_models(
                selected
            ),
        ]

        deduplicated: list[str] = []

        for model in models:
            normalized = str(
                model
            ).strip()

            if normalized and normalized not in deduplicated:
                deduplicated.append(
                    normalized
                )

        if not deduplicated:
            raise LLMConfigurationError(
                "No LLM models are configured."
            )

        return deduplicated

    @classmethod
    def _models_from_environment(
        cls,
    ) -> tuple[str, ...]:
        raw = os.getenv(
            "LLM_FALLBACK_MODELS"
        )

        if not raw:
            return cls.DEFAULT_FALLBACK_MODELS

        return tuple(
            item.strip()
            for item in raw.split(",")
            if item.strip()
        )

    @staticmethod
    def _normalize_models(
        models: Sequence[str],
    ) -> tuple[str, ...]:
        return tuple(
            str(model).strip()
            for model in models
            if str(model).strip()
        )

    # ========================================================================
    # LEGACY PROVIDER KWARG FILTERING
    # ========================================================================

    @staticmethod
    def _filter_supported_kwargs(
        method: Any,
        kwargs: Mapping[str, Any],
    ) -> dict[str, Any]:
        try:
            signature = inspect.signature(
                method
            )
        except (
            TypeError,
            ValueError,
        ):
            return {
                key: value
                for key, value in kwargs.items()
                if key in {
                    "messages",
                    "model",
                    "temperature",
                    "max_tokens",
                }
            }

        parameters = signature.parameters

        has_var_kwargs = any(
            parameter.kind
            == inspect.Parameter.VAR_KEYWORD
            for parameter in parameters.values()
        )

        if has_var_kwargs:
            return dict(
                kwargs
            )

        return {
            key: value
            for key, value in kwargs.items()
            if key in parameters
        }

    # ========================================================================
    # ERROR CLASSIFICATION
    # ========================================================================

    @staticmethod
    def _classify_provider_exception(
        exc: Exception,
    ) -> Exception:
        """
        Normalize provider-specific errors.

        This also handles OpenRouter 401/402/429 errors.
        """

        # ---------------------------------------------------------------
        # Already normalized provider exceptions
        # ---------------------------------------------------------------

        if isinstance(
            exc,
            ProviderRateLimitError,
        ):
            return LLMRateLimitError(
                str(exc)
            )

        if isinstance(
            exc,
            ProviderAuthenticationError,
        ):
            return LLMConfigurationError(
                str(exc)
            )

        if isinstance(
            exc,
            ProviderConfigurationError,
        ):
            return LLMConfigurationError(
                str(exc)
            )

        if isinstance(
            exc,
            ProviderError,
        ):
            message = str(
                exc
            ).lower()

            if (
                "credit" in message
                or "credits" in message
                or "billing" in message
                or "insufficient" in message
                or "402" in message
            ):
                return LLMCreditExhaustedError(
                    str(exc)
                )

            if (
                "rate limit" in message
                or "429" in message
                or "free-models-per-day" in message
                or "too many requests" in message
            ):
                return LLMRateLimitError(
                    str(exc)
                )

            return LLMProviderError(
                str(exc)
            )

        message = str(
            exc
        ).lower()

        status_code = getattr(
            exc,
            "status_code",
            None,
        )

        response = getattr(
            exc,
            "response",
            None,
        )

        if status_code is None and response is not None:
            status_code = getattr(
                response,
                "status_code",
                None,
            )

        if status_code == 401:
            return LLMConfigurationError(
                str(exc)
            )

        if status_code == 402:
            return LLMCreditExhaustedError(
                str(exc)
            )

        if (
            status_code == 429
            or "rate limit" in message
            or "too many requests" in message
            or "free-models-per-day" in message
        ):
            return LLMRateLimitError(
                str(exc)
            )

        if (
            "credit" in message
            or "credits" in message
            or "insufficient funds" in message
            or "billing" in message
            or "quota" in message
        ):
            return LLMCreditExhaustedError(
                str(exc)
            )

        if (
            "messages cannot be empty"
            in message
            or "message cannot be empty"
            in message
        ):
            return LLMValidationError(
                str(exc)
            )

        return LLMProviderError(
            str(exc)
        )

    # ========================================================================
    # NUMERIC VALIDATION
    # ========================================================================

    @staticmethod
    def _validate_temperature(
        value: float,
    ) -> float:
        try:
            normalized = float(
                value
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise LLMValidationError(
                "temperature must be numeric."
            ) from exc

        if not (
            0.0
            <= normalized
            <= 2.0
        ):
            raise LLMValidationError(
                "temperature must be between 0.0 and 2.0."
            )

        return normalized

    @staticmethod
    def _validate_max_tokens(
        value: int | None,
    ) -> int | None:
        if value is None:
            return None

        try:
            normalized = int(
                value
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise LLMValidationError(
                "max_tokens must be an integer."
            ) from exc

        if normalized <= 0:
            raise LLMValidationError(
                "max_tokens must be greater than zero."
            )

        return normalized

    # ========================================================================
    # HEALTH
    # ========================================================================

    async def health_check(
        self,
    ) -> dict[str, Any]:
        """
        Return manager/provider health information.

        This does not consume LLM credits.
        """

        try:
            provider = self._resolve_provider(
                self.provider_name
            )

            health_method = getattr(
                provider,
                "health_check",
                None,
            )

            if callable(
                health_method
            ):
                result = health_method()

                if inspect.isawaitable(
                    result
                ):
                    result = await result

                if isinstance(
                    result,
                    Mapping,
                ):
                    return {
                        "status": result.get(
                            "status",
                            "healthy",
                        ),
                        "provider": self.provider_name,
                        "model": self.default_model,
                        **dict(result),
                    }

            return {
                "status": "configured",
                "provider": self.provider_name,
                "model": self.default_model,
            }

        except Exception as exc:
            return {
                "status": "unhealthy",
                "provider": self.provider_name,
                "model": self.default_model,
                "error": str(exc),
            }

    async def close(
        self,
    ) -> None:
        """
        Close providers when they expose close().
        """

        for provider in self.providers.values():
            close_method = getattr(
                provider,
                "close",
                None,
            )

            if not callable(
                close_method
            ):
                continue

            try:
                result = close_method()

                if inspect.isawaitable(
                    result
                ):
                    await result

            except Exception:
                logger.warning(
                    "Failed to close LLM provider.",
                    exc_info=True,
                )

    # ========================================================================
    # COMPATIBILITY
    # ========================================================================

    @property
    def llm(self) -> "LLMManager":
        return self

    @property
    def manager(self) -> "LLMManager":
        return self


__all__ = [
    "LLMManager",
    "LLMRequest",
    "LLMResponse",
    "LLMError",
    "LLMConfigurationError",
    "LLMValidationError",
    "LLMProviderError",
    "LLMRateLimitError",
    "LLMCreditExhaustedError",
]