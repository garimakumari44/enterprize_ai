
from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ProcessingStage
from app.processing.pipeline.context import ProcessingContext
from app.processing.pipeline.pipeline import DocumentProcessingStage


class ChunkingStage(DocumentProcessingStage):
    """
    Split normalized document text into retrieval-friendly chunks.

    The processing pipeline may provide a database session to every stage.
    Chunking does not currently require database access, but the session
    parameter is accepted to keep the stage contract consistent.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        overlap: int = 150,
    ) -> None:
        if chunk_size <= 0:
            raise ValueError(
                "chunk_size must be greater than zero"
            )

        if overlap < 0:
            raise ValueError(
                "overlap cannot be negative"
            )

        if overlap >= chunk_size:
            raise ValueError(
                "overlap must be smaller than chunk_size"
            )

        self.chunk_size = chunk_size
        self.overlap = overlap

    @property
    def name(self) -> str:
        return ProcessingStage.CHUNKING.value

    async def process(
        self,
        data: ProcessingContext,
        session: AsyncSession | None = None,
    ) -> ProcessingContext:
        """
        Generate retrieval-friendly chunks from cleaned document text.

        `session` is accepted for compatibility with the pipeline-wide
        stage contract. Chunking currently does not require database access.
        """

        # The pipeline provides the session to every stage.
        # Chunking does not currently use it.
        _ = session

        text = (
            data.cleaned_text
            if data.cleaned_text is not None
            else data.raw_text or ""
        )

        chunks = self.chunk(text)

        data.set_chunks(chunks)

        data.stage_results[self.name] = {
            "chunk_count": len(chunks),
            "chunk_size": self.chunk_size,
            "overlap": self.overlap,
        }

        return data

    def chunk(
        self,
        text: str,
    ) -> list[dict[str, Any]]:
        """
        Split text into overlapping chunks.

        Returns chunk dictionaries compatible with ProcessingContext.
        """

        if not text.strip():
            return []

        chunks: list[dict[str, Any]] = []

        start = 0
        index = 0

        while start < len(text):
            end = min(
                start + self.chunk_size,
                len(text),
            )

            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append(
                    {
                        "index": index,
                        "document_id": None,
                        "text": chunk_text,
                        "start": start,
                        "end": end,
                    }
                )

                index += 1

            if end >= len(text):
                break

            start = end - self.overlap

        return chunks


__all__ = [
    "ChunkingStage",
]
