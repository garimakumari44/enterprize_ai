from __future__ import annotations

from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ProcessingStage
from app.processing.pipeline.context import ProcessingContext
from app.processing.pipeline.pipeline import DocumentProcessingStage


class TextExtractionStage(DocumentProcessingStage):
    """
    Extract textual content from the source document.

    Supported directly:
        - TXT
        - PDF
        - DOCX

    The database session is accepted to conform to the shared pipeline
    stage contract, but is not required by this stage.
    """

    @property
    def name(self) -> str:
        return ProcessingStage.TEXT_EXTRACTION.value

    async def process(
        self,
        data: ProcessingContext,
        session: AsyncSession | None = None,
    ) -> ProcessingContext:
        if not data.file_path:
            raise ValueError(
                "file_path is required for text extraction"
            )

        path = Path(data.file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Document file does not exist: {path}"
            )

        suffix = path.suffix.lower()

        if suffix == ".txt":
            text = self._extract_txt(path)

        elif suffix == ".pdf":
            text = self._extract_pdf(path)

        elif suffix == ".docx":
            text = self._extract_docx(path)

        else:
            raise ValueError(
                f"Unsupported document format: {suffix}"
            )

        data.raw_text = text

        data.set_extracted_data(
            "text_extraction",
            {
                "characters": len(text),
                "words": len(text.split()),
                "format": suffix,
            },
        )

        return data

    @staticmethod
    def _extract_txt(
        path: Path,
    ) -> str:
        return path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

    @staticmethod
    def _extract_pdf(
        path: Path,
    ) -> str:
        from pypdf import PdfReader

        reader = PdfReader(str(path))

        pages: list[str] = []

        for page in reader.pages:
            pages.append(
                page.extract_text() or ""
            )

        return "\n\n".join(pages)

    @staticmethod
    def _extract_docx(
        path: Path,
    ) -> str:
        from docx import Document

        document = Document(str(path))

        return "\n".join(
            paragraph.text
            for paragraph in document.paragraphs
            if paragraph.text.strip()
        )


__all__ = [
    "TextExtractionStage",
]