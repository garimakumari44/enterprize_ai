"""
Embedding Worker

Creates embeddings for document chunks.
"""

from __future__ import annotations

import logging
from uuid import UUID

from app.knowledge.services.indexing_service import IndexingService

logger = logging.getLogger(__name__)


class EmbeddingWorker:

    def __init__(self) -> None:
        self.service = IndexingService()

    async def run(
        self,
        document_id: UUID,
    ) -> None:

        logger.info(
            "Generating embeddings for %s",
            document_id,
        )

        try:
            await self.service.generate_embeddings(
                document_id
            )

            logger.info(
                "Embedding generation complete."
            )

        except Exception:
            logger.exception(
                "Embedding worker failed."
            )
            raise


embedding_worker = EmbeddingWorker()