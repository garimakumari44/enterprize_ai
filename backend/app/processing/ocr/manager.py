from __future__ import annotations

from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ProcessingStage
from app.processing.pipeline.context import ProcessingContext
from app.processing.pipeline.pipeline import DocumentProcessingStage


class OCRProvider(Protocol):
    async def extract_text(
        self,
        file_path: str,
    ) -> str:
        ...


class OCRStage(DocumentProcessingStage):
    """
    OCR processing stage.

    OCR is executed when:

        - force_ocr is enabled, or
        - extracted text is effectively empty.

    An OCR provider can be injected.

    The database session is accepted to conform to the shared
    pipeline stage contract but is not required by this stage.
    """

    def __init__(
        self,
        provider: OCRProvider | None = None,
    ) -> None:
        self.provider = provider

    @property
    def name(self) -> str:
        return ProcessingStage.OCR.value

    async def process(
        self,
        data: ProcessingContext,
        session: AsyncSession | None = None,
    ) -> ProcessingContext:
        raw_text = data.raw_text or ""

        force_ocr = bool(
            data.metadata.get(
                "force_ocr",
                False,
            )
        )

        requires_ocr = (
            force_ocr
            or len(raw_text.strip()) < 20
        )

        if not requires_ocr:
            data.stage_results[
                self.name
            ] = {
                "status": "skipped",
                "reason": "text_already_available",
            }

            return data

        if self.provider is None:
            data.add_warning(
                "OCR was required but no OCR provider is configured."
            )

            data.stage_results[
                self.name
            ] = {
                "status": "skipped",
                "reason": "provider_not_configured",
            }

            return data

        if not data.file_path:
            raise ValueError(
                "file_path is required for OCR"
            )

        text = await self.provider.extract_text(
            data.file_path,
        )

        if text.strip():
            data.raw_text = text

        data.stage_results[
            self.name
        ] = {
            "status": "completed",
            "characters": len(text),
        }

        return data


__all__ = [
    "OCRProvider",
    "OCRStage",
]