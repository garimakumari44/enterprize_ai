from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.models.processing.extraction_result import ExtractionResult


class BaseExtractor(ABC):
    """
    Base interface for all document extractors.

    Every extractor receives OCR text and returns
    a standardized ExtractionResult.
    """

    supported_document_type: str = "generic"

    @abstractmethod
    async def extract(
        self,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> ExtractionResult:
        """
        Extract structured information from OCR text.
        """
        raise NotImplementedError

    async def validate(
        self,
        text: str,
    ) -> bool:
        """
        Verify that this extractor can process the document.
        """
        return True