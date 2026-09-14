from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from statistics import mean

from .field_confidence import FieldConfidence


@dataclass(slots=True, frozen=True)
class PageConfidence:
    """
    Confidence score for a single document page.

    Attributes
    ----------
    page_number:
        One-based page number.

    score:
        Aggregated confidence score for the page in the range
        [0.0, 1.0].
    """

    page_number: int
    score: float

    def normalized(self) -> float:
        """
        Return a safe page confidence score in the range [0.0, 1.0].

        Non-finite values such as NaN or infinity are converted to 0.0.
        """

        try:
            value = float(self.score)
        except (TypeError, ValueError):
            return 0.0

        if not isfinite(value):
            return 0.0

        return max(0.0, min(value, 1.0))


class PageConfidenceCalculator:
    """
    Aggregates field confidence into page confidence.

    A page confidence score is calculated as the arithmetic mean
    of the normalized confidence scores of all extracted fields
    on that page.
    """

    MIN_SCORE = 0.0
    MAX_SCORE = 1.0

    def calculate(
        self,
        page_number: int,
        fields: list[FieldConfidence],
    ) -> PageConfidence:
        """
        Calculate confidence for a single page.

        Parameters
        ----------
        page_number:
            One-based page number.

        fields:
            Extracted fields belonging to the page.

        Returns
        -------
        PageConfidence
            Aggregated page confidence.

        Notes
        -----
        An empty field list results in a confidence score of 0.0.
        """

        if not fields:
            return PageConfidence(
                page_number=page_number,
                score=0.0,
            )

        values = [
            field.normalized()
            for field in fields
        ]

        if not values:
            return PageConfidence(
                page_number=page_number,
                score=0.0,
            )

        score = mean(values)

        return PageConfidence(
            page_number=page_number,
            score=self._clamp(score),
        )

    @classmethod
    def _clamp(
        cls,
        score: float,
    ) -> float:
        """
        Clamp a confidence score to [0.0, 1.0].
        """

        try:
            value = float(score)
        except (TypeError, ValueError):
            return cls.MIN_SCORE

        if not isfinite(value):
            return cls.MIN_SCORE

        return max(
            cls.MIN_SCORE,
            min(cls.MAX_SCORE, value),
        )