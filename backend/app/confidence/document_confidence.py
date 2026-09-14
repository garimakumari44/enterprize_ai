from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from statistics import mean

from .page_confidence import PageConfidence


@dataclass(slots=True, frozen=True)
class DocumentConfidence:
    """
    Confidence score for an entire document.

    Attributes
    ----------
    score:
        Overall document confidence in the range [0.0, 1.0].
    pages:
        Number of pages included in the calculation.
    """

    score: float
    pages: int


class DocumentConfidenceCalculator:
    """
    Calculates confidence for the whole document.

    The document confidence is calculated as the arithmetic mean of
    the confidence scores of all valid pages.

    Expected PageConfidence:
        page.score -> numeric confidence value, normally in [0.0, 1.0]

    Invalid/non-finite scores are ignored. If no valid page scores
    remain, the document confidence is 0.0.
    """

    MIN_SCORE = 0.0
    MAX_SCORE = 1.0

    def calculate(
        self,
        pages: list[PageConfidence],
    ) -> DocumentConfidence:
        """
        Calculate overall document confidence.

        Parameters
        ----------
        pages:
            List of PageConfidence objects.

        Returns
        -------
        DocumentConfidence
            Overall confidence and number of pages.

        Notes
        -----
        - Empty input returns score=0.0 and pages=0.
        - Non-finite scores such as NaN or infinity are ignored.
        - Scores outside [0.0, 1.0] are clamped.
        - The returned page count represents the total number of
          pages supplied, not only the valid pages.
        """

        if not pages:
            return DocumentConfidence(
                score=0.0,
                pages=0,
            )

        valid_scores: list[float] = []

        for page in pages:
            score = self._normalize_score(page.score)

            if score is not None:
                valid_scores.append(score)

        if not valid_scores:
            return DocumentConfidence(
                score=0.0,
                pages=len(pages),
            )

        document_score = mean(valid_scores)

        return DocumentConfidence(
            score=self._normalize_score(document_score) or 0.0,
            pages=len(pages),
        )

    @classmethod
    def _normalize_score(
        cls,
        score: float,
    ) -> float | None:
        """
        Validate and normalize a confidence score.

        Returns None for non-finite values.
        Otherwise clamps the value to [0.0, 1.0].
        """

        try:
            value = float(score)
        except (TypeError, ValueError):
            return None

        if not isfinite(value):
            return None

        return max(
            cls.MIN_SCORE,
            min(cls.MAX_SCORE, value),
        )