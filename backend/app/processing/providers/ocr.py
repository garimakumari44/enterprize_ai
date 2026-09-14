
"""
app.processing.providers.ocr

Canonical provider contract for OCR providers.

OCR converts images/scanned pages into machine-readable text.

Possible implementations:

    - Tesseract
    - PaddleOCR
    - Azure Document Intelligence
    - other local/cloud OCR engines

The contract supports page-level results, confidence scores,
bounding boxes, and detected languages.
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
from .layout import BoundingBox


@dataclass(slots=True)
class OCRWord:
    """
    One OCR-recognized word/token.
    """

    text: str

    confidence: float | None = None

    bounding_box: BoundingBox | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        self.text = str(
            self.text
        ).strip()

        if not self.text:
            raise ValueError(
                "OCRWord text cannot be empty."
            )

        if self.confidence is not None:
            self.confidence = float(
                self.confidence
            )

            if not 0.0 <= self.confidence <= 1.0:
                raise ValueError(
                    "OCR confidence must be between 0 and 1."
                )

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "confidence": self.confidence,
            "bounding_box": (
                self.bounding_box.to_dict()
                if self.bounding_box
                else None
            ),
            "metadata": dict(
                self.metadata
            ),
        }


@dataclass(slots=True)
class OCRLine:
    """
    One OCR-recognized line.
    """

    text: str

    confidence: float | None = None

    bounding_box: BoundingBox | None = None

    words: list[OCRWord] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        self.text = str(
            self.text
        ).strip()

        if self.confidence is not None:
            self.confidence = float(
                self.confidence
            )

            if not 0.0 <= self.confidence <= 1.0:
                raise ValueError(
                    "OCR confidence must be between 0 and 1."
                )

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "confidence": self.confidence,
            "bounding_box": (
                self.bounding_box.to_dict()
                if self.bounding_box
                else None
            ),
            "words": [
                word.to_dict()
                for word in self.words
            ],
            "metadata": dict(
                self.metadata
            ),
        }


@dataclass(slots=True)
class OCRPageResult:
    """
    OCR result for one page/image.
    """

    page_number: int

    text: str = ""

    lines: list[OCRLine] = field(
        default_factory=list
    )

    language: str | None = None

    confidence: float | None = None

    width: float | None = None

    height: float | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
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
                    "OCR confidence must be between 0 and 1."
                )

    def to_dict(self) -> dict[str, Any]:
        return {
            "page_number": self.page_number,
            "text": self.text,
            "lines": [
                line.to_dict()
                for line in self.lines
            ],
            "language": self.language,
            "confidence": self.confidence,
            "width": self.width,
            "height": self.height,
            "metadata": dict(
                self.metadata
            ),
        }


@dataclass(slots=True)
class OCRRequest:
    """
    Input contract for OCR providers.
    """

    document_id: str | None = None

    source_path: str | None = None

    content: bytes | None = None

    pages: Sequence[Any] = field(
        default_factory=list
    )

    language: str | None = None

    languages: Sequence[str] = field(
        default_factory=list
    )

    options: dict[str, Any] = field(
        default_factory=dict
    )

    def validate(self) -> None:
        if (
            self.source_path is None
            and self.content is None
            and not self.pages
        ):
            raise ValueError(
                "OCRRequest requires source_path, content, "
                "or pages."
            )

        if self.content is not None:
            if not isinstance(
                self.content,
                bytes,
            ):
                raise TypeError(
                    "content must be bytes or None."
                )


@dataclass(slots=True)
class OCRResult:
    """
    Canonical OCR output.
    """

    document_id: str | None = None

    pages: list[OCRPageResult] = field(
        default_factory=list
    )

    text: str = ""

    languages: list[str] = field(
        default_factory=list
    )

    confidence: float | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    warnings: list[str] = field(
        default_factory=list
    )

    @property
    def page_count(self) -> int:
        return len(self.pages)

    @property
    def has_text(self) -> bool:
        return bool(
            self.text.strip()
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "pages": [
                page.to_dict()
                for page in self.pages
            ],
            "text": self.text,
            "languages": list(
                self.languages
            ),
            "confidence": self.confidence,
            "metadata": dict(
                self.metadata
            ),
            "warnings": list(
                self.warnings
            ),
            "page_count": self.page_count,
            "has_text": self.has_text,
        }


class BaseOCRProvider(
    BaseProcessingProvider
):
    """
    Base contract for OCR providers.
    """

    PROVIDER_TYPE = "ocr"

    PROCESSING_STAGE = "ocr"

    def capabilities(self) -> set[str]:
        return {
            ProviderCapability.OCR.value,
            ProviderCapability.CONFIDENCE_SCORING.value,
        }

    @abstractmethod
    async def recognize(
        self,
        request: OCRRequest,
    ) -> OCRResult:
        """
        Perform OCR.
        """

        raise NotImplementedError

    async def process(
        self,
        request: OCRRequest,
    ) -> ProviderResult:
        request.validate()

        result = await self.recognize(
            request
        )

        return ProviderResult.ok(
            provider=self.name,
            operation="ocr",
            data=result.to_dict(),
            metadata={
                "document_id": result.document_id,
                "page_count": result.page_count,
                "confidence": result.confidence,
                "languages": list(
                    result.languages
                ),
            },
            warnings=result.warnings,
        )

    def supported_languages(
        self,
    ) -> Sequence[str]:
        return ()

    def supports_language(
        self,
        language: str,
    ) -> bool:
        if not language:
            return False

        normalized = (
            language.strip().lower()
        )

        supported = {
            item.lower()
            for item in self.supported_languages()
        }

        return (
            not supported
            or normalized in supported
        )

