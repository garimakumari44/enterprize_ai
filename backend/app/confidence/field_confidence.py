from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from statistics import mean
from typing import Iterable


@dataclass(slots=True, frozen=True)
class FieldConfidence:
    """
    Confidence score for a single extracted field.

    Attributes
    ----------
    field_name:
        Name of the extracted field.

    score:
        Raw confidence score. Expected to be in the range [0.0, 1.0].
    """

    field_name: str
    score: float

    def normalized(self) -> float:
        """
        Return a safe confidence score in the range [0.0, 1.0].

        Non-finite values such as NaN or infinity are converted to 0.0.
        """

        try:
            value = float(self.score)
        except (TypeError, ValueError):
            return 0.0

        if not isfinite(value):
            return 0.0

        return max(
            0.0,
            min(value, 1.0),
        )


class FieldConfidenceCalculator:
    """
    Calculates confidence scores for extracted fields.

    Field confidence is composed from three signals:

    - OCR confidence:        40%
    - Extraction confidence: 40%
    - Validation confidence: 20%

    All scores are normalized to [0.0, 1.0].
    """

    OCR_WEIGHT = 0.4
    EXTRACTION_WEIGHT = 0.4
    VALIDATION_WEIGHT = 0.2

    MIN_SCORE = 0.0
    MAX_SCORE = 1.0

    def calculate(
        self,
        ocr_score: float,
        extraction_score: float,
        validation_score: float,
    ) -> float:
        """
        Calculate the confidence of a single extracted field.

        Parameters
        ----------
        ocr_score:
            Confidence produced by OCR.

        extraction_score:
            Confidence that the field was correctly extracted.

        validation_score:
            Confidence produced by downstream validation.

        Returns
        -------
        float
            Combined confidence in the range [0.0, 1.0].

        Invalid or non-finite scores are treated as 0.0.
        """

        ocr = self._normalize_score(ocr_score)
        extraction = self._normalize_score(extraction_score)
        validation = self._normalize_score(validation_score)

        score = (
            ocr * self.OCR_WEIGHT
            + extraction * self.EXTRACTION_WEIGHT
            + validation * self.VALIDATION_WEIGHT
        )

        return self._clamp(score)

    def average(
        self,
        scores: Iterable[FieldConfidence],
    ) -> float:
        """
        Calculate the average confidence across extracted fields.

        Parameters
        ----------
        scores:
            Iterable of FieldConfidence objects.

        Returns
        -------
        float
            Average normalized confidence in the range [0.0, 1.0].

        Empty input returns 0.0.
        """

        values = [
            score.normalized()
            for score in scores
        ]

        if not values:
            return 0.0

        return self._clamp(mean(values))

    @classmethod
    def _normalize_score(
        cls,
        score: float,
    ) -> float:
        """
        Convert a raw confidence value into a safe [0.0, 1.0] score.
        """

        try:
            value = float(score)
        except (TypeError, ValueError):
            return cls.MIN_SCORE

        if not isfinite(value):
            return cls.MIN_SCORE

        return cls._clamp(value)

    @classmethod
    def _clamp(
        cls,
        score: float,
    ) -> float:
        """
        Clamp a score to the valid confidence range.
        """

        return max(
            cls.MIN_SCORE,
            min(cls.MAX_SCORE, score),
        )