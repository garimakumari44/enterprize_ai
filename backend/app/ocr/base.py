from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class OCRWord:
    text: str
    confidence: float
    bbox: list[int] = field(default_factory=list)


@dataclass(slots=True)
class OCRPage:
    page_number: int
    text: str
    words: list[OCRWord] = field(default_factory=list)


@dataclass(slots=True)
class OCRResult:
    text: str
    pages: list[OCRPage]
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseOCR(ABC):
    """
    Abstract OCR engine.
    """

    @abstractmethod
    async def extract(
        self,
        file_path: str,
    ) -> OCRResult:
        """
        Extract text from a document.

        Returns:
            OCRResult
        """
        raise NotImplementedError