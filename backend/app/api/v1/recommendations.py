"""
Recommendation Service

High-level service responsible for generating actionable
recommendations from structured document intelligence.

This service orchestrates the RecommendationEngine and provides
a stable interface for API endpoints, workflows, and AI agents.
"""

from __future__ import annotations

from typing import Any

from app.recommendations.recommendation_engine import RecommendationEngine


class RecommendationService:
    """
    Application service for recommendation generation.
    """

    def __init__(
        self,
        engine: RecommendationEngine | None = None,
    ) -> None:
        self.engine = engine or RecommendationEngine()

    async def generate(
        self,
        document: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Generate recommendations for a document.
        """

        return await self.engine.generate_recommendations(document)

    async def prioritize(
        self,
        recommendations: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Rank recommendations by priority.
        """

        return await self.engine.prioritize_actions(recommendations)

    async def explain(
        self,
        recommendation: dict[str, Any],
    ) -> str:
        """
        Explain why a recommendation was generated.
        """

        return await self.engine.explain_recommendation(recommendation)