
"""
app.processing.providers.layout

Canonical contract for document layout analysis.

Layout analysis identifies spatial regions such as:

    text blocks
    headings
    tables
    images
    lists
    headers
    footers
    signatures

The implementation can later be backed by:

    - local computer vision models
    - PDF geometry
    - OCR engines
    - Azure Document Intelligence
    - other enterprise document AI providers
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
class BoundingBox:
    """
    Normalized rectangular region.

    Coordinates are represented as floats.

    By convention:

        x1, y1 = top-left
        x2, y2 = bottom-right
    """

    x1: float
    y1: float
    x2: float
    y2: float

    def __post_init__(self) -> None:
        self.x1 = float(self.x1)
        self.y1 = float(self.y1)
        self.x2 = float(self.x2)
        self.y2 = float(self.y2)

        if self.x2 < self.x1:
            raise ValueError(
                "BoundingBox x2 cannot be smaller than x1."
            )

        if self.y2 < self.y1:
            raise ValueError(
                "BoundingBox y2 cannot be smaller than y1."
            )

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        return self.y2 - self.y1

    @property
    def area(self) -> float:
        return self.width * self.height

    def to_dict(self) -> dict[str, float]:
        return {
            "x1": self.x1,
            "y1": self.y1,
            "x2": self.x2,
            "y2": self.y2,
        }


@dataclass(slots=True)
class LayoutBlock:
    """
    One detected document region.
    """

    block_id: str

    block_type: str

    page_number: int

    bounding_box: BoundingBox | None = None

    text: str = ""

    confidence: float | None = None

    reading_order: int | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    children: list[str] = field(
        default_factory=list
    )

    def __post_init__(self) -> None:
        if not self.block_id.strip():
            raise ValueError(
                "block_id cannot be empty."
            )

        if not self.block_type.strip():
            raise ValueError(
                "block_type cannot be empty."
            )

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
            "block_id": self.block_id,
            "block_type": self.block_type,
            "page_number": self.page_number,
            "bounding_box": (
                self.bounding_box.to_dict()
                if self.bounding_box
                else None
            ),
            "text": self.text,
            "confidence": self.confidence,
            "reading_order": self.reading_order,
            "metadata": dict(self.metadata),
            "children": list(self.children),
        }


@dataclass(slots=True)
class LayoutPage:
    """
    Layout information for one page.
    """

    page_number: int

    width: float | None = None

    height: float | None = None

    blocks: list[LayoutBlock] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "page_number": self.page_number,
            "width": self.width,
            "height": self.height,
            "blocks": [
                block.to_dict()
                for block in self.blocks
            ],
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True)
class LayoutAnalysisResult:
    """
    Canonical output from layout analysis.
    """

    document_id: str | None = None

    pages: list[LayoutPage] = field(
        default_factory=list
    )

    blocks: list[LayoutBlock] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    warnings: list[str] = field(
        default_factory=list
    )

    model: str | None = None

    @property
    def block_count(self) -> int:
        return len(self.blocks)

    @property
    def page_count(self) -> int:
        return len(self.pages)

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "pages": [
                page.to_dict()
                for page in self.pages
            ],
            "blocks": [
                block.to_dict()
                for block in self.blocks
            ],
            "metadata": dict(self.metadata),
            "warnings": list(self.warnings),
            "model": self.model,
            "page_count": self.page_count,
            "block_count": self.block_count,
        }


@dataclass(slots=True)
class LayoutAnalysisRequest:
    """
    Input contract for layout analysis.
    """

    document_id: str | None = None

    pages: Sequence[Mapping[str, Any]] = field(
        default_factory=list
    )

    text: str = ""

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
            self.pages,
            Sequence,
        ):
            raise TypeError(
                "pages must be a sequence."
            )


class BaseLayoutProvider(
    BaseProcessingProvider
):
    """
    Base contract for layout providers.
    """

    PROVIDER_TYPE = "layout"

    PROCESSING_STAGE = "layout_analysis"

    def capabilities(self) -> set[str]:
        return {
            ProviderCapability.LAYOUT_ANALYSIS.value,
            ProviderCapability.BLOCK_DETECTION.value,
        }

    @abstractmethod
    async def analyze(
        self,
        request: LayoutAnalysisRequest,
    ) -> LayoutAnalysisResult:
        """
        Analyze document layout.
        """

        raise NotImplementedError

    async def process(
        self,
        request: LayoutAnalysisRequest,
    ) -> ProviderResult:
        request.validate()

        result = await self.analyze(
            request
        )

        return ProviderResult.ok(
            provider=self.name,
            operation="analyze_layout",
            data=result.to_dict(),
            metadata={
                "document_id": result.document_id,
                "page_count": result.page_count,
                "block_count": result.block_count,
                "model": result.model,
            },
            warnings=result.warnings,
        )

    def supported_block_types(
        self,
    ) -> Sequence[str]:
        return ()

    def supports_block_type(
        self,
        block_type: str,
    ) -> bool:
        if not isinstance(
            block_type,
            str,
        ):
            return False

        normalized = (
            block_type.strip().lower()
        )

        return normalized in {
            item.lower()
            for item in self.supported_block_types()
        }

