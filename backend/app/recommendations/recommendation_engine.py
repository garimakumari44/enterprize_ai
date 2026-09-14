"""
Enterprise Recommendation Engine.

Generates intelligent recommendations based on
workflow execution, AI usage, runtime metrics,
knowledge retrieval, and system health.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ==========================================================
# Enums
# ==========================================================


class RecommendationCategory(str, Enum):
    WORKFLOW = "workflow"
    PERFORMANCE = "performance"
    COST = "cost"
    PROMPT = "prompt"
    KNOWLEDGE = "knowledge"
    SECURITY = "security"
    RELIABILITY = "reliability"
    MODEL = "model"


class RecommendationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ==========================================================
# Recommendation Model
# ==========================================================


@dataclass(slots=True)
class Recommendation:
    title: str
    description: str

    category: RecommendationCategory
    priority: RecommendationPriority

    action: str

    metadata: dict[str, Any] = field(default_factory=dict)


# ==========================================================
# Recommendation Engine
# ==========================================================


class RecommendationEngine:
    """
    Produces optimization recommendations.

    This engine is intentionally rule-based.
    In the future it can be replaced by
    ML/LLM powered recommendation logic.
    """

    def recommend(
        self,
        metrics: dict[str, Any],
    ) -> list[Recommendation]:

        recommendations: list[Recommendation] = []

        recommendations.extend(self._workflow(metrics))
        recommendations.extend(self._performance(metrics))
        recommendations.extend(self._cost(metrics))
        recommendations.extend(self._knowledge(metrics))
        recommendations.extend(self._security(metrics))
        recommendations.extend(self._model(metrics))

        return recommendations

    # ------------------------------------------------------

    def _workflow(
        self,
        metrics: dict[str, Any],
    ) -> list[Recommendation]:

        recs = []

        if metrics.get("workflow_nodes", 0) > 50:
            recs.append(
                Recommendation(
                    title="Large Workflow",
                    description=(
                        "Workflow contains many nodes. "
                        "Consider splitting it into reusable sub-workflows."
                    ),
                    category=RecommendationCategory.WORKFLOW,
                    priority=RecommendationPriority.MEDIUM,
                    action="Create modular workflows.",
                )
            )

        return recs

    # ------------------------------------------------------

    def _performance(
        self,
        metrics: dict[str, Any],
    ) -> list[Recommendation]:

        recs = []

        latency = metrics.get("avg_latency_ms", 0)

        if latency > 3000:
            recs.append(
                Recommendation(
                    title="High Latency",
                    description="Average execution latency exceeds 3 seconds.",
                    category=RecommendationCategory.PERFORMANCE,
                    priority=RecommendationPriority.HIGH,
                    action="Optimize slow nodes or enable parallel execution.",
                    metadata={
                        "latency_ms": latency,
                    },
                )
            )

        return recs

    # ------------------------------------------------------

    def _cost(
        self,
        metrics: dict[str, Any],
    ) -> list[Recommendation]:

        recs = []

        tokens = metrics.get("monthly_tokens", 0)

        if tokens > 5_000_000:
            recs.append(
                Recommendation(
                    title="High Token Usage",
                    description="Monthly token usage is unusually high.",
                    category=RecommendationCategory.COST,
                    priority=RecommendationPriority.HIGH,
                    action="Use smaller models or cache repeated prompts.",
                )
            )

        return recs

    # ------------------------------------------------------

    def _knowledge(
        self,
        metrics: dict[str, Any],
    ) -> list[Recommendation]:

        recs = []

        score = metrics.get("retrieval_score", 1.0)

        if score < 0.60:
            recs.append(
                Recommendation(
                    title="Weak Retrieval Quality",
                    description=(
                        "Knowledge retrieval quality appears low."
                    ),
                    category=RecommendationCategory.KNOWLEDGE,
                    priority=RecommendationPriority.HIGH,
                    action=(
                        "Re-index documents or improve chunking strategy."
                    ),
                )
            )

        return recs

    # ------------------------------------------------------

    def _security(
        self,
        metrics: dict[str, Any],
    ) -> list[Recommendation]:

        recs = []

        if metrics.get("public_api_key", False):
            recs.append(
                Recommendation(
                    title="Public API Key Detected",
                    description="API keys should never be publicly accessible.",
                    category=RecommendationCategory.SECURITY,
                    priority=RecommendationPriority.CRITICAL,
                    action="Move secrets into secure storage.",
                )
            )

        return recs

    # ------------------------------------------------------

    def _model(
        self,
        metrics: dict[str, Any],
    ) -> list[Recommendation]:

        recs = []

        accuracy = metrics.get("model_accuracy", 1.0)

        if accuracy < 0.80:
            recs.append(
                Recommendation(
                    title="Low Model Accuracy",
                    description="Current AI model accuracy is below target.",
                    category=RecommendationCategory.MODEL,
                    priority=RecommendationPriority.HIGH,
                    action="Evaluate alternative models or improve prompts.",
                    metadata={
                        "accuracy": accuracy,
                    },
                )
            )

        return recs

    # ------------------------------------------------------

    def summarize(
        self,
        recommendations: list[Recommendation],
    ) -> dict[str, int]:
        """
        Return counts grouped by priority.
        """

        summary = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
        }

        for recommendation in recommendations:
            summary[recommendation.priority.value] += 1

        return summary

    # ------------------------------------------------------

    def top(
        self,
        recommendations: list[Recommendation],
        limit: int = 5,
    ) -> list[Recommendation]:
        """
        Return highest-priority recommendations.
        """

        priority_order = {
            RecommendationPriority.CRITICAL: 0,
            RecommendationPriority.HIGH: 1,
            RecommendationPriority.MEDIUM: 2,
            RecommendationPriority.LOW: 3,
        }

        return sorted(
            recommendations,
            key=lambda r: priority_order[r.priority],
        )[:limit]