
"""
app.processing.providers.factory

Provider factory and registration helpers.

The factory is responsible for creating provider instances from
configuration without making the processing pipeline aware of concrete
implementations.

Architecture
------------

    Pipeline
       |
       v
    ProviderFactory
       |
       v
    ProviderRegistry
       |
       v
    Concrete Provider
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from threading import RLock
from typing import Any, TypeVar

from .base import BaseProvider
from .registry import ProviderRegistry


logger = logging.getLogger(__name__)


ProviderT = TypeVar(
    "ProviderT",
    bound=BaseProvider,
)


ProviderConstructor = Callable[
    [dict[str, Any]],
    BaseProvider,
]


@dataclass(slots=True)
class ProviderDefinition:
    """
    Definition describing how a provider is constructed.
    """

    name: str

    provider_type: str

    constructor: ProviderConstructor

    description: str | None = None

    defaults: dict[str, Any] | None = None

    aliases: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        self.name = self.name.strip().lower()

        self.provider_type = (
            self.provider_type.strip().lower()
        )

        if not self.name:
            raise ValueError(
                "Provider definition name cannot be empty."
            )

        if not self.provider_type:
            raise ValueError(
                "Provider definition type cannot be empty."
            )

        if self.defaults is None:
            self.defaults = {}

    def build(
        self,
        config: Mapping[str, Any] | None = None,
    ) -> BaseProvider:
        """
        Construct a provider instance.

        Configuration supplied by the caller overrides defaults.
        """

        merged_config = dict(
            self.defaults or {}
        )

        if config:
            merged_config.update(
                dict(config)
            )

        provider = self.constructor(
            merged_config
        )

        if not isinstance(
            provider,
            BaseProvider,
        ):
            raise TypeError(
                f"Provider constructor '{self.name}' "
                "did not return a BaseProvider."
            )

        return provider


class ProviderFactory:
    """
    Factory responsible for provider definitions and instances.

    Definitions describe how providers are created.

    The registry stores actual provider instances.

    This distinction allows the application to have:

        - reusable provider definitions
        - configurable instances
        - multiple instances of the same provider
        - provider aliases
    """

    def __init__(
        self,
        registry: ProviderRegistry | None = None,
    ) -> None:
        self.registry = (
            registry
            if registry is not None
            else ProviderRegistry()
        )

        self._definitions: dict[
            str,
            ProviderDefinition,
        ] = {}

        self._aliases: dict[
            str,
            str,
        ] = {}

        self._lock = RLock()

    @staticmethod
    def _normalize(
        value: str,
    ) -> str:
        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                "Provider name must be a string."
            )

        normalized = value.strip().lower()

        if not normalized:
            raise ValueError(
                "Provider name cannot be empty."
            )

        return normalized

    def register_definition(
        self,
        definition: ProviderDefinition,
        *,
        replace: bool = False,
    ) -> ProviderDefinition:
        """
        Register a provider definition.
        """

        if not isinstance(
            definition,
            ProviderDefinition,
        ):
            raise TypeError(
                "definition must be ProviderDefinition."
            )

        name = self._normalize(
            definition.name
        )

        with self._lock:
            if (
                name in self._definitions
                and not replace
            ):
                raise ValueError(
                    f"Provider definition '{name}' "
                    "is already registered."
                )

            self._definitions[name] = (
                definition
            )

            for alias in definition.aliases:
                normalized_alias = (
                    self._normalize(alias)
                )

                existing = self._aliases.get(
                    normalized_alias
                )

                if (
                    existing is not None
                    and existing != name
                    and not replace
                ):
                    raise ValueError(
                        f"Provider alias "
                        f"'{normalized_alias}' "
                        "is already registered."
                    )

                self._aliases[
                    normalized_alias
                ] = name

        logger.info(
            "Registered provider definition: %s",
            name,
        )

        return definition

    def unregister_definition(
        self,
        name: str,
    ) -> ProviderDefinition | None:
        """
        Remove a provider definition.
        """

        normalized = self._normalize(
            name
        )

        with self._lock:
            canonical_name = (
                self._aliases.get(
                    normalized,
                    normalized,
                )
            )

            definition = (
                self._definitions.pop(
                    canonical_name,
                    None,
                )
            )

            if definition is None:
                return None

            for alias in definition.aliases:
                self._aliases.pop(
                    self._normalize(alias),
                    None,
                )

        logger.info(
            "Unregistered provider definition: %s",
            canonical_name,
        )

        return definition

    def resolve_definition(
        self,
        name: str,
    ) -> ProviderDefinition:
        """
        Resolve a provider name or alias.
        """

        normalized = self._normalize(
            name
        )

        with self._lock:
            canonical_name = (
                self._aliases.get(
                    normalized,
                    normalized,
                )
            )

            try:
                return self._definitions[
                    canonical_name
                ]
            except KeyError:
                available = ", ".join(
                    sorted(
                        self._definitions
                    )
                )

                raise KeyError(
                    f"Provider definition '{normalized}' "
                    f"is not registered. "
                    f"Available definitions: "
                    f"{available or 'none'}"
                ) from None

    def create(
        self,
        name: str,
        config: Mapping[str, Any] | None = None,
        *,
        register: bool = False,
        registry_name: str | None = None,
        replace: bool = False,
    ) -> BaseProvider:
        """
        Create a provider from a registered definition.

        Args:
            name:
                Provider definition name or alias.

            config:
                Runtime provider configuration.

            register:
                Whether the created provider should also be added
                to the ProviderRegistry.

            registry_name:
                Optional registry key.

            replace:
                Whether an existing registry provider may be replaced.
        """

        definition = self.resolve_definition(
            name
        )

        provider = definition.build(
            config
        )

        if register:
            key = (
                registry_name
                if registry_name is not None
                else definition.name
            )

            self.registry.register(
                key,
                provider,
                replace=replace,
            )

        logger.info(
            "Created provider '%s' of type '%s'",
            definition.name,
            definition.provider_type,
        )

        return provider

    def create_and_register(
        self,
        name: str,
        config: Mapping[str, Any] | None = None,
        *,
        registry_name: str | None = None,
        replace: bool = False,
    ) -> BaseProvider:
        """
        Convenience wrapper around create(..., register=True).
        """

        return self.create(
            name,
            config,
            register=True,
            registry_name=registry_name,
            replace=replace,
        )

    def has_definition(
        self,
        name: str,
    ) -> bool:
        try:
            self.resolve_definition(name)
            return True
        except KeyError:
            return False

    def definitions(
        self,
    ) -> list[ProviderDefinition]:
        with self._lock:
            return list(
                self._definitions.values()
            )

    def definition_names(
        self,
    ) -> list[str]:
        with self._lock:
            return sorted(
                self._definitions.keys()
            )

    def clear_definitions(self) -> None:
        with self._lock:
            self._definitions.clear()
            self._aliases.clear()

    def info(self) -> list[dict[str, Any]]:
        """
        Return factory metadata.
        """

        with self._lock:
            return [
                {
                    "name": definition.name,
                    "provider_type": (
                        definition.provider_type
                    ),
                    "description": (
                        definition.description
                    ),
                    "aliases": list(
                        definition.aliases
                    ),
                    "defaults": dict(
                        definition.defaults or {}
                    ),
                }
                for definition in self._definitions.values()
            ]


def constructor_from_class(
    provider_class: type[ProviderT],
) -> ProviderConstructor:
    """
    Convert a provider class into the standard factory constructor.

    The provider must accept a dictionary configuration.
    """

    if not isinstance(
        provider_class,
        type,
    ):
        raise TypeError(
            "provider_class must be a class."
        )

    def constructor(
        config: dict[str, Any],
    ) -> BaseProvider:
        return provider_class(
            config=config
        )

    return constructor


def register_provider_class(
    factory: ProviderFactory,
    *,
    name: str,
    provider_type: str,
    provider_class: type[ProviderT],
    description: str | None = None,
    defaults: Mapping[str, Any] | None = None,
    aliases: tuple[str, ...] = (),
    replace: bool = False,
) -> ProviderDefinition:
    """
    Register a concrete provider class with the factory.
    """

    definition = ProviderDefinition(
        name=name,
        provider_type=provider_type,
        constructor=constructor_from_class(
            provider_class
        ),
        description=description,
        defaults=dict(
            defaults or {}
        ),
        aliases=aliases,
    )

    return factory.register_definition(
        definition,
        replace=replace,
    )


# Application-level factory.

provider_factory = ProviderFactory()

