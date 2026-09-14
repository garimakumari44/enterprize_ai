"""
Background worker responsible for AI recommendations.
"""

from __future__ import annotations

import logging
from uuid import UUID

from app.ai.recommendations.recommendation_engine import (
    RecommendationEngine,
)
from app.events.recommendation_events import RecommendationEvents
from app.repositories.intelligence.recommendation_repository import (
    RecommendationRepository,
)

logger = logging.getLogger(__name__)


class RecommendationWorker:
    """
    Generates AI recommendations asynchronously.
    """

    def __init__(
        self,
        repository: RecommendationRepository,
        engine: RecommendationEngine,
    ):
        self.repository = repository
        self.engine = engine

    async def execute(
        self,
        recommendation_id: UUID,
    ) -> dict:

        RecommendationEvents.execution_started(
            recommendation_id
        )

        logger.info(
            "Recommendation execution started (%s)",
            recommendation_id,
        )

        try:

            recommendation = await self.repository.get(
                recommendation_id
            )

            result = await self.engine.generate(
                recommendation
            )

            await self.repository.save_result(
                recommendation_id=recommendation_id,
                recommendations=result.recommendations,
                confidence=result.confidence,
            )

            RecommendationEvents.execution_completed(
                recommendation_id
            )

            logger.info(
                "Recommendation execution completed"
            )

            return {
                "success": True,
                "recommendation_id": str(
                    recommendation_id
                ),
            }

        except Exception as exc:

            logger.exception(exc)

            RecommendationEvents.execution_failed(
                recommendation_id=recommendation_id,
                error=str(exc),
            )

            return {
                "success": False,
                "error": str(exc),
            }