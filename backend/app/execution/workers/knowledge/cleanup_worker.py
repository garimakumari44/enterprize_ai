"""
Knowledge Cleanup Worker

Removes orphaned chunks, embeddings,
graph nodes, and stale indexes.
"""

from __future__ import annotations

import logging

from app.knowledge.services.knowledge_service import KnowledgeService

logger = logging.getLogger(__name__)


class CleanupWorker:
    """
    Performs scheduled cleanup tasks.
    """

    def __init__(self) -> None:
        self.service = KnowledgeService()

    async def run(self) -> None:
        """
        Execute cleanup process.
        """

        logger.info(
            "Starting knowledge cleanup."
        )

        try:
            await self.service.cleanup()

            logger.info(
                "Cleanup completed."
            )

        except Exception:
            logger.exception(
                "Cleanup failed."
            )
            raise


cleanup_worker = CleanupWorker()