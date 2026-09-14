"""
Knowledge Reindex Worker

Rebuilds vector indexes for existing documents.
"""

from __future__ import annotations

import logging
from uuid import UUID

from app.knowledge.services.indexing_service import IndexingService

logger = logging.getLogger(__name__)


class ReindexWorker:
    """
    Background worker responsible for rebuilding indexes.
    """

    def __init__(self) -> None:
        self.service = IndexingService()

    async def run(
        self,
        document_id: UUID,
    ) -> None:
        """
        Reindex a document.
        """

        logger.info(
            "Starting reindex for document %s",
            document_id,
        )

        try:
            await self.service.reindex_document(
                document_id
            )

            logger.info(
                "Reindex completed for %s",
                document_id,
            )

        except Exception:
            logger.exception(
                "Reindex failed for %s",
                document_id,
            )
            raise


reindex_worker = ReindexWorker()