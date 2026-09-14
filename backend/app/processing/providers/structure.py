
"""
app.processing.providers.structure

Canonical contract for document structure detection.

Structure detection converts layout/text information into a semantic
hierarchy.

Example:

    Document
      |
      +-- Section
      |     |
      |     +-- Heading
      |     +-- Paragraph
      |     +-- List
      |
      +-- Section
            |
            +-- Heading
            +-- Table

This layer is intentionally independent from OCR, LLMs, databases,
and specific document-processing libraries.
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
class StructureNode:
    """
    One node in the document's semantic hierarchy.
    """

    node_id: str

    node_type: str

    title: str | None = None

    text: str = ""

    page_number: int | None = None

    parent_id: str | None = None

    children: list[str] = field(
        default_factory=list
    )

    level: int = 0

    order: int = 0

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    confidence: float | None = None

    def __post_init__(self) -> None:
        if not self.node_id.strip():
            raise ValueError(
                "node_id cannot be empty."
            )

        if not self.node_type.strip():
            raise ValueError(
                "node_type cannot be empty."
            )

        if self.level < 0:
            raise ValueError(
                "level cannot be negative."
            )

        if self.order < 0:
            raise ValueError(
                "order cannot be negative."
            )

        if self.page_number is not None:
            if self.page_number < 1:
                raise ValueError(
                    "page_number must be >= 1."
                )

        if self.confidence is not None:
            self.confidence = float(
                self.confidence
            )

            if not 0.0 <= self.confidence <= 1.0:
                raise ValueError(
                    "confidence must be between 0 and 1."
                )

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "title": self.title,
            "text": self.text,
            "page_number": self.page_number,
            "parent_id": self.parent_id,
            "children": list(self.children),
            "level": self.level,
            "order": self.order,
            "metadata": dict(self.metadata),
            "confidence": self.confidence,
        }


@dataclass(slots=True)
class DocumentStructure:
    """
    Canonical semantic structure of a document.
    """

    document_id: str | None = None

    root_id: str | None = None

    nodes: list[StructureNode] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    warnings: list[str] = field(
        default_factory=list
    )

    def get_node(
        self,
        node_id: str,
    ) -> StructureNode | None:
        for node in self.nodes:
            if node.node_id == node_id:
                return node

        return None

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def section_count(self) -> int:
        return sum(
            1
            for node in self.nodes
            if node.node_type.lower()
            in {
                "section",
                "heading",
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "root_id": self.root_id,
            "nodes": [
                node.to_dict()
                for node in self.nodes
            ],
            "metadata": dict(self.metadata),
            "warnings": list(self.warnings),
            "node_count": self.node_count,
            "section_count": self.section_count,
        }


@dataclass(slots=True)
class StructureDetectionRequest:
    """
    Input contract for structure detection.
    """

    document_id: str | None = None

    text: str = ""

    blocks: Sequence[Mapping[str, Any]] = field(
        default_factory=list
    )

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

        if not isinstance(
            self.blocks,
            Sequence,
        ):
            raise TypeError(
                "blocks must be a sequence."
            )


class BaseStructureProvider(
    BaseProcessingProvider
):
    """
    Base contract for structure detection providers.
    """

    PROVIDER_TYPE = "structure"

    PROCESSING_STAGE = "structure_detection"

    def capabilities(self) -> set[str]:
        return {
            ProviderCapability.STRUCTURE_DETECTION.value,
            ProviderCapability.HEADING_DETECTION.value,
            ProviderCapability.SECTION_DETECTION.value,
        }

    @abstractmethod
    async def detect_structure(
        self,
        request: StructureDetectionRequest,
    ) -> DocumentStructure:
        """
        Detect semantic document structure.
        """

        raise NotImplementedError

    async def process(
        self,
        request: StructureDetectionRequest,
    ) -> ProviderResult:
        request.validate()

        result = await self.detect_structure(
            request
        )

        return ProviderResult.ok(
            provider=self.name,
            operation="detect_structure",
            data=result.to_dict(),
            metadata={
                "document_id": result.document_id,
                "root_id": result.root_id,
                "node_count": result.node_count,
                "section_count": result.section_count,
            },
            warnings=result.warnings,
        )

    def supported_node_types(
        self,
    ) -> Sequence[str]:
        return ()

    def supports_node_type(
        self,
        node_type: str,
    ) -> bool:
        if not isinstance(
            node_type,
            str,
        ):
            return False

        normalized = (
            node_type.strip().lower()
        )

        return normalized in {
            item.lower()
            for item in self.supported_node_types()
        }

