from __future__ import annotations

from .base import BaseValidator


class ConfidenceValidator(BaseValidator):
    """
    Validate OCR / AI confidence scores.
    """

    def __init__(
        self,
        minimum_confidence: float = 0.70,
    ) -> None:
        self.minimum_confidence = minimum_confidence
        self._message = ""

    def validate(self, value: float) -> bool:
        if value is None:
            self._message = "Confidence score missing."
            return False

        if not (0.0 <= value <= 1.0):
            self._message = (
                "Confidence must be between 0 and 1."
            )
            return False

        if value < self.minimum_confidence:
            self._message = (
                f"Confidence below threshold ({self.minimum_confidence:.2f})."
            )
            return False

        return True

    def error_message(self) -> str:
        return self._message