
from __future__ import annotations

import re

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ProcessingStage
from app.processing.pipeline.context import ProcessingContext
from app.processing.pipeline.pipeline import DocumentProcessingStage


class CleaningStage(DocumentProcessingStage):
    """
    Normalize extracted document text.

    This stage is intentionally database-independent. The processing
    pipeline provides a job-scoped database session to all stages for a
    consistent stage interface, but this implementation does not require
    database access.
    """

    @property
    def name(self) -> str:
        """Return the canonical processing-stage name."""
        return ProcessingStage.CLEANING.value

    async def process(
        self,
        data: ProcessingContext,
        session: AsyncSession | None = None,
    ) -> ProcessingContext:
        """
        Clean and normalize extracted document text.

        Args:
            data:
                Current document processing context.

            session:
                Optional job-scoped database session supplied by the
                processing pipeline. It is intentionally unused because
                text cleaning is a pure in-memory operation.

        Returns:
            The same ProcessingContext instance with cleaned text and
            stage metadata populated.
        """
        # Keep the common pipeline interface while explicitly documenting
        # that this stage does not require database access.
        del session

        source = data.raw_text or ""
        cleaned = self.clean(source)

        data.cleaned_text = cleaned
        data.stage_results[self.name] = {
            "characters_before": len(source),
            "characters_after": len(cleaned),
        }

        return data

    @staticmethod
    def clean(text: str) -> str:
        """
        Normalize extracted text.

        Cleaning operations:
        1. Normalize platform-specific line endings.
        2. Collapse consecutive spaces and tabs.
        3. Collapse excessive blank lines.
        4. Remove whitespace around line breaks.
        5. Remove leading and trailing whitespace.

        Args:
            text:
                Raw extracted document text.

        Returns:
            Normalized document text.
        """
        if not text:
            return ""

        # Normalize CRLF and CR line endings to LF.
        text = text.replace("\r\n", "\n")
        text = text.replace("\r", "\n")

        # Collapse horizontal whitespace while preserving line structure.
        text = re.sub(r"[ \t]+", " ", text)

        # Prevent excessive vertical whitespace.
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Remove horizontal whitespace immediately before/after newlines.
        text = re.sub(r"[ \t]*\n[ \t]*", "\n", text)

        return text.strip()


__all__ = ["CleaningStage"]
