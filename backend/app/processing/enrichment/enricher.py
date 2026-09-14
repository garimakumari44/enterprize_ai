from __future__ import annotations

import re
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ProcessingStage
from app.processing.pipeline.context import ProcessingContext
from app.processing.pipeline.pipeline import DocumentProcessingStage


class MetadataEnrichmentStage(DocumentProcessingStage):
    """
    Enrich document chunks with metadata.

    This is intentionally provider-independent. A real NER/entity
    extraction service can be added later.

    The pipeline provides a database session to every stage. This stage
    does not currently require database access, but accepts the session
    to maintain the common stage interface.
    """

    @property
    def name(self) -> str:
        return ProcessingStage.METADATA_ENRICHMENT.value

    async def process(
        self,
        data: ProcessingContext,
        session: AsyncSession | None = None,
    ) -> ProcessingContext:
        chunks = data.chunks
        document_type = data.document_type

        enriched_chunks: list[dict[str, Any]] = []

        for chunk in chunks:
            text = str(
                chunk.get(
                    "text",
                    "",
                )
            )

            metadata = {
                "document_id": data.document_id,
                "document_type": document_type,
                "chunk_index": chunk.get(
                    "index"
                ),
                "entities": self._extract_entities(
                    text
                ),
            }

            enriched_chunks.append(
                {
                    **chunk,
                    "metadata": metadata,
                }
            )

        data.set_enriched_chunks(
            enriched_chunks
        )

        data.stage_results[
            self.name
        ] = {
            "chunk_count": len(enriched_chunks),
        }

        return data

    @staticmethod
    def _extract_entities(
        text: str,
    ) -> list[str]:
        candidates = re.findall(
            r"\b[A-Z][A-Za-z0-9&.-]{2,}"
            r"(?:\s+[A-Z][A-Za-z0-9&.-]{2,})*\b",
            text,
        )

        unique: list[str] = []

        for candidate in candidates:
            if candidate not in unique:
                unique.append(candidate)

        return unique[:100]


__all__ = [
    "MetadataEnrichmentStage",
]