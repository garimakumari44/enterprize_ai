from __future__ import annotations

from pathlib import Path

from app.ocr.base import (
    BaseOCR,
    OCRPage,
    OCRResult,
)


class PaddleOCRProvider(BaseOCR):
    """
    PaddleOCR implementation.

    pip install paddleocr paddlepaddle
    """

    def __init__(self):
        self._engine = None

    def _load(self):
        if self._engine is None:
            from paddleocr import PaddleOCR

            self._engine = PaddleOCR(
                use_angle_cls=True,
                lang="en",
            )

    async def extract(
        self,
        file_path: str,
    ) -> OCRResult:

        self._load()

        result = self._engine.ocr(
            str(Path(file_path)),
            cls=True,
        )

        pages = []
        all_text = []

        for page_index, page in enumerate(result, start=1):

            lines = []

            if page:
                for line in page:
                    text = line[1][0]
                    lines.append(text)

            page_text = "\n".join(lines)

            pages.append(
                OCRPage(
                    page_number=page_index,
                    text=page_text,
                )
            )

            all_text.append(page_text)

        return OCRResult(
            text="\n".join(all_text),
            pages=pages,
            metadata={
                "engine": "PaddleOCR",
            },
        )