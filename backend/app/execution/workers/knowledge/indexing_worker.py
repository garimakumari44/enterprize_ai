"""
Indexing Worker

Indexes embeddings into the vector database.
"""

from __future__ import annotations

import logging
from uuid import UUID

from app.knowledge.services.indexing_service import IndexingService

logger = logging.getLogger(__name__)


class IndexingWorker:

    def __init__(self) -> None:
        self.service = IndexingService()

    async def run(
        self,
        document_id: UUID,
    ) -> None:

        logger.info(
            "Indexing document %s",
            document_id,
        )

        try:
            await self.service.index_document(
                document_id
            )

            logger.info(
                "Indexing completed."
            )

        except Exception:
            logger.exception(
                "Indexing failed."
            )
            raise


indexing_worker = IndexingWorker()