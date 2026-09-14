"""
Knowledge Ingestion Worker

Responsible for:
- Receiving ingestion jobs
- Processing uploaded documents
- Triggering embedding generation
"""

from __future__ import annotations

import logging
from uuid import UUID

from app.knowledge.services.ingestion_service import IngestionService

logger = logging.getLogger(__name__)


class IngestionWorker:
    """
    Background worker for document ingestion.
    """

    def __init__(self) -> None:
        self.service = IngestionService()

    async def run(
        self,
        document_id: UUID,
    ) -> None:
        """
        Execute ingestion pipeline.
        """

        logger.info("Starting ingestion: %s", document_id)

        try:
            await self.service.ingest_document(document_id)

            logger.info(
                "Finished ingestion: %s",
                document_id,
            )

        except Exception:
            logger.exception(
                "Ingestion failed: %s",
                document_id,
            )
            raise


ingestion_worker = IngestionWorker()