from __future__ import annotations

from pathlib import Path

import pytesseract
from PIL import Image

from app.ocr.base import (
    BaseOCR,
    OCRPage,
    OCRResult,
)


class TesseractOCRProvider(BaseOCR):
    """
    pip install pytesseract pillow

    Requires:
        Tesseract installed on machine.
    """

    async def extract(
        self,
        file_path: str,
    ) -> OCRResult:

        image = Image.open(Path(file_path))

        text = pytesseract.image_to_string(image)

        page = OCRPage(
            page_number=1,
            text=text,
        )

        return OCRResult(
            text=text,
            pages=[page],
            metadata={
                "engine": "Tesseract",
            },
        )