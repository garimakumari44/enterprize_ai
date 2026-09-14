
"""
app.processing.providers.classification

Canonical contract for document classification providers.

Classification determines the semantic/document type of an input
document, for example:

    invoice
    receipt
    contract
    purchase_order
    resume
    bank_statement
    report
    email
    unknown

The contract is provider-independent and contains no FastAPI,
database, or ML-library dependencies.
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
class ClassificationLabel:
    """
    One classification prediction.
    """

    label: str

    confidence: float

    rank: int = 1

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        self.label = str(self.label).strip()

        if not self.label:
            raise ValueError(
                "Classification label cannot be empty."
            )

        self.confidence = float(
            self.confidence
        )

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "Classification confidence must be between "
                "0.0 and 1.0."
            )

        if self.rank < 1:
            raise ValueError(
                "Classification rank must be >= 1."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "confidence": self.confidence,
            "rank": self.rank,
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True)
class ClassificationResult:
    """
    Canonical output of a classification provider.
    """

    document_id: str | None = None

    primary_label: str = "unknown"

    confidence: float = 0.0

    labels: list[ClassificationLabel] = field(
        default_factory=list
    )

    model: str | None = None

    version: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    warnings: list[str] = field(
        default_factory=list
    )

    @property
    def is_confident(
        self,
    ) -> bool:
        return self.confidence >= 0.80

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "primary_label": self.primary_label,
            "confidence": self.confidence,
            "labels": [
                label.to_dict()
                for label in self.labels
            ],
            "model": self.model,
            "version": self.version,
            "metadata": dict(self.metadata),
            "warnings": list(self.warnings),
            "is_confident": self.is_confident,
        }


@dataclass(slots=True)
class ClassificationRequest:
    """
    Input contract for document classification.
    """

    text: str = ""

    document_id: str | None = None

    filename: str | None = None

    mime_type: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
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

        if not self.text.strip() and not self.filename:
            raise ValueError(
                "ClassificationRequest requires text "
                "or filename."
            )

        if self.filename is not None and not isinstance(
            self.filename,
            str,
        ):
            raise TypeError(
                "filename must be a string or None."
            )

        if self.mime_type is not None and not isinstance(
            self.mime_type,
            str,
        ):
            raise TypeError(
                "mime_type must be a string or None."
            )


class BaseClassificationProvider(
    BaseProcessingProvider
):
    """
    Base contract for classification providers.
    """

    PROVIDER_TYPE = "classification"

    PROCESSING_STAGE = "classification"

    def capabilities(self) -> set[str]:
        return {
            ProviderCapability.DOCUMENT_CLASSIFICATION.value,
            ProviderCapability.CONFIDENCE_SCORING.value,
        }

    @abstractmethod
    async def classify(
        self,
        request: ClassificationRequest,
    ) -> ClassificationResult:
        """
        Classify a document.
        """

        raise NotImplementedError

    async def process(
        self,
        request: ClassificationRequest,
    ) -> ProviderResult:
        """
        Execute classification through the common provider interface.
        """

        request.validate()

        result = await self.classify(
            request
        )

        return ProviderResult.ok(
            provider=self.name,
            operation="classify",
            data=result.to_dict(),
            metadata={
                "document_id": result.document_id,
                "primary_label": result.primary_label,
                "confidence": result.confidence,
                "model": result.model,
                "version": result.version,
            },
            warnings=result.warnings,
        )

    def supported_labels(
        self,
    ) -> Sequence[str]:
        """
        Return labels supported by this provider.

        Empty means the provider does not expose a fixed label set.
        """

        return ()

    def supports_label(
        self,
        label: str,
    ) -> bool:
        if not isinstance(
            label,
            str,
        ):
            return False

        normalized = label.strip().lower()

        return normalized in {
            item.lower()
            for item in self.supported_labels()
        }

