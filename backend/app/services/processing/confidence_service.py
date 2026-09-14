from __future__ import annotations

from statistics import mean

from app.models.processing.confidence_score import ConfidenceScore


class ConfidenceService:
    """
    Calculates confidence scores.
    """

    @staticmethod
    def calculate_average(
        scores: list[float],
    ) -> ConfidenceScore:

        if not scores:
            value = 0.0
        else:
            value = round(mean(scores), 4)

        level = ConfidenceService.classify(value)

        return ConfidenceScore(
            score=value,
            level=level,
        )

    @staticmethod
    def classify(score: float) -> str:

        if score >= 0.95:
            return "excellent"

        if score >= 0.85:
            return "high"

        if score >= 0.70:
            return "medium"

        return "low"

    @staticmethod
    def requires_review(score: float) -> bool:
        return score < 0.85