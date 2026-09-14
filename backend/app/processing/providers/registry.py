
"""
app.processing.providers.registry

Provider registry for the document-processing system.

Responsibilities
----------------

    - register providers
    - unregister providers
    - retrieve providers
    - discover providers by type
    - discover providers by capability
    - expose provider metadata
    - prevent accidental duplicate registration

The registry is intentionally independent from FastAPI and the
application dependency-injection system.
"""

from __future__ import annotations

import logging
from threading import RLock
from typing import Iterable, TypeVar

from .base import BaseProvider
from .capabilities import (
    normalize_capability,
)

logger = logging.getLogger(__name__)

ProviderT = TypeVar(
    "ProviderT",
    bound=BaseProvider,
)


class ProviderRegistry:
    """
    Central registry for processing providers.

    Example:

        registry = ProviderRegistry()

        registry.register(
            "pdf",
            PdfExtractor()
        )

        provider = registry.get("pdf")
    """

    def __init__(self) -> None:
        self._providers: dict[
            str,
            BaseProvider,
        ] = {}

        self._lock = RLock()

    @staticmethod
    def _normalize_name(
        name: str,
    ) -> str:
        if not isinstance(
            name,
            str,
        ):
            raise TypeError(
                "Provider name must be a string."
            )

        normalized = name.strip().lower()

        if not normalized:
            raise ValueError(
                "Provider name cannot be empty."
            )

        return normalized

    def register(
        self,
        name: str,
        provider: BaseProvider,
        *,
        replace: bool = False,
    ) -> BaseProvider:
        """
        Register a provider.

        Args:
            name:
                Registry key.

            provider:
                Provider instance.

            replace:
                Whether an existing provider may be replaced.
        """

        normalized_name = (
            self._normalize_name(name)
        )

        if not isinstance(
            provider,
            BaseProvider,
        ):
            raise TypeError(
                "provider must inherit from BaseProvider."
            )

        with self._lock:
            if (
                normalized_name in self._providers
                and not replace
            ):
                raise ValueError(
                    f"Provider '{normalized_name}' "
                    "is already registered."
                )

            self._providers[
                normalized_name
            ] = provider

        logger.info(
            "Registered provider: %s (%s)",
            normalized_name,
            provider.provider_type,
        )

        return provider

    def unregister(
        self,
        name: str,
    ) -> BaseProvider | None:
        """
        Remove a provider from the registry.
        """

        normalized_name = (
            self._normalize_name(name)
        )

        with self._lock:
            provider = self._providers.pop(
                normalized_name,
                None,
            )

        if provider is not None:
            logger.info(
                "Unregistered provider: %s",
                normalized_name,
            )

        return provider

    def get(
        self,
        name: str,
    ) -> BaseProvider:
        """
        Retrieve a registered provider.

        Raises:
            KeyError:
                If no provider is registered under the name.
        """

        normalized_name = (
            self._normalize_name(name)
        )

        with self._lock:
            try:
                return self._providers[
                    normalized_name
                ]
            except KeyError:
                available = ", ".join(
                    sorted(
                        self._providers
                    )
                )

                raise KeyError(
                    f"Provider '{normalized_name}' "
                    f"is not registered. "
                    f"Available providers: "
                    f"{available or 'none'}"
                ) from None

    def get_optional(
        self,
        name: str,
    ) -> BaseProvider | None:
        """Return a provider or None."""

        normalized_name = (
            self._normalize_name(name)
        )

        with self._lock:
            return self._providers.get(
                normalized_name
            )

    def contains(
        self,
        name: str,
    ) -> bool:
        """Return whether a provider is registered."""

        normalized_name = (
            self._normalize_name(name)
        )

        with self._lock:
            return normalized_name in (
                self._providers
            )

    def all(
        self,
    ) -> list[BaseProvider]:
        """Return all registered providers."""

        with self._lock:
            return list(
                self._providers.values()
            )

    def names(self) -> list[str]:
        """Return all provider names."""

        with self._lock:
            return sorted(
                self._providers.keys()
            )

    def by_type(
        self,
        provider_type: str,
    ) -> list[BaseProvider]:
        """Return providers matching a provider type."""

        normalized_type = (
            provider_type.strip().lower()
        )

        with self._lock:
            return [
                provider
                for provider in self._providers.values()
                if provider.provider_type.lower()
                == normalized_type
            ]

    def by_capability(
        self,
        capability: str,
    ) -> list[BaseProvider]:
        """Return providers supporting a capability."""

        normalized = normalize_capability(
            capability
        )

        with self._lock:
            return [
                provider
                for provider in self._providers.values()
                if provider.supports(
                    normalized
                )
            ]

    def find(
        self,
        *,
        provider_type: str | None = None,
        capability: str | None = None,
    ) -> list[BaseProvider]:
        """
        Find providers matching optional criteria.

        Both filters are ANDed together.
        """

        providers = self.all()

        if provider_type is not None:
            normalized_type = (
                provider_type.strip().lower()
            )

            providers = [
                provider
                for provider in providers
                if provider.provider_type.lower()
                == normalized_type
            ]

        if capability is not None:
            normalized_capability = (
                normalize_capability(
                    capability
                )
            )

            providers = [
                provider
                for provider in providers
                if provider.supports(
                    normalized_capability
                )
            ]

        return providers

    def info(self) -> list[dict]:
        """
        Return metadata for all providers.
        """

        with self._lock:
            return [
                {
                    "registry_name": name,
                    **provider.info(),
                }
                for name, provider
                in sorted(
                    self._providers.items()
                )
            ]

    def clear(self) -> None:
        """Remove all registered providers."""

        with self._lock:
            self._providers.clear()

        logger.info(
            "Provider registry cleared."
        )

    def __len__(self) -> int:
        with self._lock:
            return len(
                self._providers
            )

    def __contains__(
        self,
        name: str,
    ) -> bool:
        return self.contains(name)

    def __iter__(
        self,
    ) -> Iterable[BaseProvider]:
        return iter(
            self.all()
        )


# Application-level registry instance.

provider_registry = ProviderRegistry()

