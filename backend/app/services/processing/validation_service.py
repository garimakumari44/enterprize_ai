"""
app/services/processing/validation_service.py

Application service for document validation.

Responsibilities
----------------
- Validate extracted values.
- Persist validation results.
- Retrieve validation results for a processing job.

Validation results are associated with ExtractionResult through:

    ProcessingJob
        |
        v
    ExtractionResult
        |
        v
    ValidationResult
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.extraction_result import ExtractionResult
from app.db.models.validation_result import (
    ValidationResult,
    ValidationStatus,
)


class ValidationService:
    """
    Application service responsible for validation.
    """

    def __init__(
        self,
        db: AsyncSession,
    ) -> None:
        self.db = db

    # ==================================================================
    # REQUIRED FIELD
    # ==================================================================

    def validate_required(
        self,
        *,
        field_name: str,
        value: str | None,
    ) -> ValidationResult:
        """
        Validate that a required field contains a value.
        """

        valid = value is not None and value != ""

        return ValidationResult(
            field_name=field_name,
            status=(
                ValidationStatus.PASSED
                if valid
                else ValidationStatus.FAILED
            ),
            passed=valid,
            message=(
                None
                if valid
                else "Required field missing."
            ),
        )

    # ==================================================================
    # NUMBER
    # ==================================================================

    def validate_number(
        self,
        *,
        field_name: str,
        value: str,
    ) -> ValidationResult:
        """
        Validate that a value is numeric.
        """

        try:
            float(value)

            return ValidationResult(
                field_name=field_name,
                status=ValidationStatus.PASSED,
                passed=True,
                message=None,
            )

        except (TypeError, ValueError):

            return ValidationResult(
                field_name=field_name,
                status=ValidationStatus.FAILED,
                passed=False,
                message="Invalid numeric value.",
            )

    # ==================================================================
    # EMAIL
    # ==================================================================

    def validate_email(
        self,
        *,
        field_name: str,
        value: str,
    ) -> ValidationResult:
        """
        Validate a basic email address.
        """

        valid = (
            isinstance(value, str)
            and "@" in value
            and "." in value
        )

        return ValidationResult(
            field_name=field_name,
            status=(
                ValidationStatus.PASSED
                if valid
                else ValidationStatus.FAILED
            ),
            passed=valid,
            message=(
                None
                if valid
                else "Invalid email address."
            ),
        )

    # ==================================================================
    # PERSIST
    # ==================================================================

    async def save_result(
        self,
        *,
        result: ValidationResult,
        extraction_result_id: UUID | None = None,
    ) -> ValidationResult:
        """
        Persist a validation result.
        """

        if extraction_result_id is not None:
            result.extraction_result_id = (
                extraction_result_id
            )

        self.db.add(result)

        await self.db.commit()
        await self.db.refresh(result)

        return result

    # ==================================================================
    # RETRIEVE BY PROCESSING ID
    # ==================================================================

    async def get_results(
        self,
        *,
        processing_id: UUID,
    ) -> list[ValidationResult]:
        """
        Retrieve all validation results associated with
        a processing job.
        """

        query = (
            select(ValidationResult)
            .join(
                ExtractionResult,
                ValidationResult.extraction_result_id
                == ExtractionResult.id,
            )
            .where(
                ExtractionResult.processing_id
                == processing_id,
            )
            .order_by(
                ValidationResult.created_at.asc(),
            )
        )

        result = await self.db.execute(query)

        return list(result.scalars().all())

    # ==================================================================
    # AGGREGATED RESULT
    # ==================================================================

    async def get_result(
        self,
        *,
        processing_id: UUID,
    ) -> dict[str, Any] | None:
        """
        Return an aggregated validation result for a processing job.

        Returns None when no validation results exist yet.
        """

        results = await self.get_results(
            processing_id=processing_id,
        )

        if not results:
            return None

        total = len(results)

        passed_count = sum(
            1
            for result in results
            if result.status == ValidationStatus.PASSED
            or result.passed is True
        )

        failed_count = sum(
            1
            for result in results
            if result.status == ValidationStatus.FAILED
            or result.passed is False
        )

        warning_count = sum(
            1
            for result in results
            if result.status == ValidationStatus.WARNING
        )

        if failed_count > 0:
            status_value = ValidationStatus.FAILED.value
        elif warning_count > 0:
            status_value = ValidationStatus.WARNING.value
        else:
            status_value = ValidationStatus.PASSED.value

        score = (
            passed_count / total
            if total > 0
            else None
        )

        issues: list[dict[str, Any]] = []

        for result in results:
            if result.passed:
                continue

            issues.append(
                {
                    "rule": result.rule_name,
                    "code": None,
                    "message": (
                        result.message
                        or "Validation failed."
                    ),
                    "severity": (
                        "warning"
                        if result.status
                        == ValidationStatus.WARNING
                        else "error"
                    ),
                    "field": result.field_name,
                    "value": None,
                }
            )

        return {
            "status": status_value,
            "passed": failed_count == 0,
            "score": score,
            "issues": issues,
            "metadata": {
                "total": total,
                "passed": passed_count,
                "failed": failed_count,
                "warnings": warning_count,
            },
            "created_at": min(
                result.created_at
                for result in results
                if result.created_at is not None
            ),
            "completed_at": max(
                result.updated_at
                for result in results
                if result.updated_at is not None
            ),
        }

    # ==================================================================
    # COMPATIBILITY ALIAS
    # ==================================================================

    async def get_validation_result(
        self,
        *,
        processing_id: UUID,
    ) -> dict[str, Any] | None:
        """
        Compatibility alias for API callers.
        """

        return await self.get_result(
            processing_id=processing_id,
        )


__all__ = [
    "ValidationService",
]