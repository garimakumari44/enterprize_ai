"""
Knowledge Graph Worker

Builds and updates the knowledge graph.
"""

from __future__ import annotations

import logging
from uuid import UUID

from app.knowledge.services.graph_service import GraphService

logger = logging.getLogger(__name__)


class GraphWorker:
    """
    Background worker for knowledge graph generation.
    """

    def __init__(self) -> None:
        self.service = GraphService()

    async def run(
        self,
        document_id: UUID,
    ) -> None:
        """
        Build graph from indexed document.
        """

        logger.info(
            "Generating knowledge graph for %s",
            document_id,
        )

        try:
            await self.service.build_graph(
                document_id
            )

            logger.info(
                "Knowledge graph generated."
            )

        except Exception:
            logger.exception(
                "Graph generation failed."
            )
            raise


graph_worker = GraphWorker()