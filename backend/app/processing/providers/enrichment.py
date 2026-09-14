
"""
app.processing.providers.enrichment

Canonical provider contract for document metadata enrichment.

Enrichment adds useful information to documents and chunks, such as:

    language
    entities
    keywords
    dates
    document identifiers
    source metadata
    classification metadata
    processing metadata

This layer does not require an LLM. Rule-based and ML-based
implementations can both satisfy this contract.
"""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from .base import (
    BaseProcessingProvider,
    ProviderResult,
)
from .capabilities import ProviderCapability


@dataclass(slots=True)
class EnrichmentField:
    """
    One extracted/enriched metadata field.
    """

    name: str

    value: Any

    confidence: float | None = None

    source: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        self.name = str(
            self.name
        ).strip()

        if not self.name:
            raise ValueError(
                "Enrichment field name cannot be empty."
            )

        if self.confidence is not None:
            self.confidence = float(
                self.confidence
            )

            if not 0.0 <= self.confidence <= 1.0:
                raise ValueError(
                    "Enrichment confidence must be between "
                    "0.0 and 1.0."
                )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "confidence": self.confidence,
            "source": self.source,
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True)
class Entity:
    """
    Canonical representation of an extracted entity.
    """

    text: str

    entity_type: str

    start: int | None = None

    end: int | None = None

    confidence: float | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        self.text = str(
            self.text
        ).strip()

        self.entity_type = str(
            self.entity_type
        ).strip()

        if not self.text:
            raise ValueError(
                "Entity text cannot be empty."
            )

        if not self.entity_type:
            raise ValueError(
                "Entity type cannot be empty."
            )

        if self.start is not None and self.start < 0:
            raise ValueError(
                "Entity start cannot be negative."
            )

        if self.end is not None and self.end < 0:
            raise ValueError(
                "Entity end cannot be negative."
            )

        if (
            self.start is not None
            and self.end is not None
            and self.end < self.start
        ):
            raise ValueError(
                "Entity end cannot be before start."
            )

        if self.confidence is not None:
            self.confidence = float(
                self.confidence
            )

            if not 0.0 <= self.confidence <= 1.0:
                raise ValueError(
                    "Entity confidence must be between "
                    "0.0 and 1.0."
                )

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "entity_type": self.entity_type,
            "start": self.start,
            "end": self.end,
            "confidence": self.confidence,
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True)
class EnrichmentRequest:
    """
    Input contract for enrichment providers.
    """

    text: str = ""

    document_id: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    chunks: Sequence[Mapping[str, Any]] = field(
        default_factory=list
    )

    options: dict[str, Any] = field(
        default_factory=dict
    )

    def validate(self) -> None:
        if not isinstance(
            self.text,
            str,
        ):
            raise TypeError(
                "text must be a string."
            )

        if not self.text.strip():
            raise ValueError(
                "EnrichmentRequest text cannot be empty."
            )

        if not isinstance(
            self.metadata,
            dict,
        ):
            raise TypeError(
                "metadata must be a dictionary."
            )


@dataclass(slots=True)
class EnrichmentResult:
    """
    Canonical output from metadata enrichment.
    """

    document_id: str | None = None

    fields: list[EnrichmentField] = field(
        default_factory=list
    )

    entities: list[Entity] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    language: str | None = None

    keywords: list[str] = field(
        default_factory=list
    )

    warnings: list[str] = field(
        default_factory=list
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "fields": [
                field.to_dict()
                for field in self.fields
            ],
            "entities": [
                entity.to_dict()
                for entity in self.entities
            ],
            "metadata": dict(self.metadata),
            "language": self.language,
            "keywords": list(self.keywords),
            "warnings": list(self.warnings),
        }


class BaseEnrichmentProvider(
    BaseProcessingProvider
):
    """
    Base contract for metadata enrichment providers.
    """

    PROVIDER_TYPE = "enrichment"

    PROCESSING_STAGE = "metadata_enrichment"

    def capabilities(self) -> set[str]:
        return {
            ProviderCapability.METADATA_ENRICHMENT.value,
            ProviderCapability.ENTITY_EXTRACTION.value,
        }

    @abstractmethod
    async def enrich(
        self,
        request: EnrichmentRequest,
    ) -> EnrichmentResult:
        """
        Enrich document metadata.
        """

        raise NotImplementedError

    async def process(
        self,
        request: EnrichmentRequest,
    ) -> ProviderResult:
        request.validate()

        result = await self.enrich(
            request
        )

        return ProviderResult.ok(
            provider=self.name,
            operation="enrich",
            data=result.to_dict(),
            metadata={
                "document_id": result.document_id,
                "field_count": len(
                    result.fields
                ),
                "entity_count": len(
                    result.entities
                ),
                "language": result.language,
            },
            warnings=result.warnings,
        )

