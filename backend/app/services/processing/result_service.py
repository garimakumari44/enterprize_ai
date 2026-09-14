from __future__ import annotations

from app.models.processing.confidence_score import ConfidenceScore
from app.models.processing.extracted_field import ExtractedField
from app.models.processing.validation_result import ValidationResult


class ResultService:
    """
    Builds the final processing result returned by the API.
    """

    @staticmethod
    def build_result(
        *,
        fields: list[ExtractedField],
        validations: list[ValidationResult],
        confidence: ConfidenceScore,
    ) -> dict:

        return {
            "fields": [
                {
                    "name": field.field_name,
                    "value": field.field_value,
                    "confidence": field.confidence,
                }
                for field in fields
            ],
            "validation": [
                {
                    "field": item.field_name,
                    "passed": item.passed,
                    "message": item.message,
                }
                for item in validations
            ],
            "confidence": {
                "score": confidence.score,
                "level": confidence.level,
            },
            "summary": {
                "total_fields": len(fields),
                "valid_fields": sum(v.passed for v in validations),
                "invalid_fields": sum(not v.passed for v in validations),
                "requires_review": confidence.level in {"low", "medium"},
            },
        }

    @staticmethod
    def build_error(
        message: str,
    ) -> dict:

        return {
            "success": False,
            "message": message,
        }

    @staticmethod
    def build_success(
        data: dict,
    ) -> dict:

        return {
            "success": True,
            "data": data,
        }