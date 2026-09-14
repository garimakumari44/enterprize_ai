
"""
app.processing.providers.base

Canonical base contracts for document-processing providers.

Provider architecture
---------------------

    Processing Stage
          |
          v
    Provider Contract
          |
          v
    Concrete Provider
          |
          +--> Local implementation
          +--> Cloud implementation
          +--> Database implementation

Providers are intentionally independent from:
    - FastAPI
    - SQLAlchemy
    - PostgreSQL
    - Celery
    - HTTP APIs

The provider layer should expose deterministic contracts that can be
used by the processing pipeline and provider factory/registry.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import uuid4


def utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class ProviderResult:
    """
    Standard result returned by a processing provider.

    The payload is intentionally generic because different providers
    produce different data structures.

    Examples:

        extraction:
            {
                "text": "...",
                "pages": 10,
                "language": "en"
            }

        classification:
            {
                "document_type": "invoice",
                "confidence": 0.97
            }

        embedding:
            {
                "embeddings": [...]
            }
    """

    success: bool = True

    provider: str = ""

    operation: str = ""

    data: dict[str, Any] = field(default_factory=dict)

    metadata: dict[str, Any] = field(default_factory=dict)

    error: str | None = None

    warnings: list[str] = field(default_factory=list)

    started_at: datetime | None = None

    completed_at: datetime | None = None

    duration_ms: float | None = None

    request_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    @classmethod
    def ok(
        cls,
        *,
        provider: str,
        operation: str,
        data: Mapping[str, Any] | None = None,
        metadata: Mapping[str, Any] | None = None,
        warnings: list[str] | None = None,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
    ) -> "ProviderResult":
        """Create a successful provider result."""

        result = cls(
            success=True,
            provider=provider,
            operation=operation,
            data=dict(data or {}),
            metadata=dict(metadata or {}),
            warnings=list(warnings or []),
            started_at=started_at,
            completed_at=completed_at,
        )

        result._calculate_duration()

        return result

    @classmethod
    def failure(
        cls,
        *,
        provider: str,
        operation: str,
        error: str,
        metadata: Mapping[str, Any] | None = None,
        warnings: list[str] | None = None,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
    ) -> "ProviderResult":
        """Create a failed provider result."""

        result = cls(
            success=False,
            provider=provider,
            operation=operation,
            metadata=dict(metadata or {}),
            error=str(error),
            warnings=list(warnings or []),
            started_at=started_at,
            completed_at=completed_at,
        )

        result._calculate_duration()

        return result

    def _calculate_duration(self) -> None:
        """Calculate execution duration when timestamps are available."""

        if (
            self.started_at is not None
            and self.completed_at is not None
        ):
            duration = (
                self.completed_at - self.started_at
            ).total_seconds() * 1000

            self.duration_ms = max(
                0.0,
                duration,
            )

    def with_metadata(
        self,
        **values: Any,
    ) -> "ProviderResult":
        """Add metadata to the result and return itself."""

        self.metadata.update(values)

        return self

    def add_warning(
        self,
        warning: str,
    ) -> "ProviderResult":
        """Add a warning to the result."""

        if warning:
            self.warnings.append(str(warning))

        return self


class ProviderError(RuntimeError):
    """Base exception for provider failures."""


class ProviderConfigurationError(ProviderError):
    """Raised when provider configuration is invalid."""


class ProviderUnavailableError(ProviderError):
    """Raised when a provider cannot currently be used."""


class BaseProvider(ABC):
    """
    Base interface for every processing provider.

    Concrete providers should define:

        PROVIDER_NAME
        PROVIDER_TYPE

    and implement `health_check()`.

    Providers may expose additional domain-specific methods.

    Example:

        class PdfExtractor(BaseProvider):

            PROVIDER_NAME = "pdf_extractor"
            PROVIDER_TYPE = "extraction"

            async def extract(...):
                ...

    The base class deliberately does not know about FastAPI,
    databases, object storage, or specific ML libraries.
    """

    PROVIDER_NAME: str = "base"

    PROVIDER_TYPE: str = "generic"

    VERSION: str = "1.0"

    def __init__(
        self,
        *,
        config: Mapping[str, Any] | None = None,
    ) -> None:
        self.config: dict[str, Any] = dict(
            config or {}
        )

    @property
    def name(self) -> str:
        """Return canonical provider name."""

        return self.PROVIDER_NAME

    @property
    def provider_type(self) -> str:
        """Return provider category."""

        return self.PROVIDER_TYPE

    @property
    def version(self) -> str:
        """Return provider version."""

        return self.VERSION

    def configure(
        self,
        **config: Any,
    ) -> None:
        """
        Update provider configuration.

        Concrete providers may override this when configuration
        requires validation or resource initialization.
        """

        self.config.update(config)

    def get_config(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """Read a configuration value."""

        return self.config.get(
            key,
            default,
        )

    def capabilities(self) -> set[str]:
        """
        Return provider capabilities.

        Concrete providers should override this.
        """

        return set()

    def supports(
        self,
        capability: str,
    ) -> bool:
        """Return whether the provider supports a capability."""

        return capability in self.capabilities()

    def info(self) -> dict[str, Any]:
        """Return provider metadata."""

        return {
            "name": self.name,
            "type": self.provider_type,
            "version": self.version,
            "capabilities": sorted(
                self.capabilities()
            ),
        }

    def validate_config(self) -> None:
        """
        Validate provider configuration.

        The default implementation accepts all configuration.
        Concrete providers can override it.
        """

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check whether the provider is usable.

        Returns:
            True when the provider is available.
        """

        raise NotImplementedError

    async def startup(self) -> None:
        """
        Optional provider startup hook.

        Providers that need to load models, establish connections,
        or initialize resources can override this.
        """

        self.validate_config()

    async def shutdown(self) -> None:
        """
        Optional provider shutdown hook.

        Providers can override this to release resources.
        """

    async def close(self) -> None:
        """Alias for shutdown."""

        await self.shutdown()


class BaseProcessingProvider(BaseProvider):
    """
    Base class for document-processing providers.

    This is the preferred parent for:

        - extraction
        - OCR
        - classification
        - layout
        - structure
        - chunking
        - enrichment
        - embedding
        - indexing
    """

    PROCESSING_STAGE: str = ""

    @property
    def processing_stage(self) -> str:
        """Return the pipeline stage implemented by this provider."""

        return self.PROCESSING_STAGE

    def info(self) -> dict[str, Any]:
        """Return provider metadata including processing stage."""

        result = super().info()

        result["processing_stage"] = (
            self.processing_stage
        )

        return result

