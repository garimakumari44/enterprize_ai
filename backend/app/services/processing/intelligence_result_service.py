"""
app/services/processing/intelligence_result_service.py

Service responsible for creating, updating, and retrieving the canonical
DocumentIntelligenceResult.

Transaction ownership
---------------------
This service does NOT commit transactions.

The caller owns the transaction boundary.

Use:
    await db.flush()

inside this service so that generated IDs and constraint errors are
available immediately, while allowing the ProcessingJobRunner to commit
the complete processing transaction atomically.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.document_intelligence_result import (
    DocumentIntelligenceResult,
)


class IntelligenceResultService:
    """
    Persistence service for DocumentIntelligenceResult.

    This service intentionally does not call commit().
    Transaction ownership belongs to the caller.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # CREATE / UPSERT
    # ------------------------------------------------------------------

    async def create_result(
        self,
        *,
        processing_id: UUID,
        document_id: UUID,
        document_version_id: UUID,
        document_type: str | None = None,
        classification_confidence: float | None = None,
        structured_data: dict[str, Any] | None = None,
        validation_results: dict[str, Any] | None = None,
        artifacts: list[Any] | None = None,
        knowledge: dict[str, Any] | None = None,
        raw_text: str | None = None,
    ) -> DocumentIntelligenceResult:
        """
        Create or update the canonical intelligence result.

        Important:
            No commit occurs here.

        The caller must commit the transaction.
        """

        existing = await self.get_by_processing_id(processing_id)

        normalized_confidence = self._normalize_confidence(
            classification_confidence
        )

        if existing is not None:
            existing.document_id = document_id
            existing.document_version_id = document_version_id
            existing.document_type = document_type
            existing.classification_confidence = normalized_confidence

            existing.structured_data = (
                structured_data if structured_data is not None else {}
            )

            existing.validation_results = (
                validation_results
                if validation_results is not None
                else {}
            )

            existing.artifacts = (
                artifacts if artifacts is not None else []
            )

            existing.knowledge = (
                knowledge if knowledge is not None else {}
            )

            existing.raw_text = raw_text

            await self.db.flush()
            await self.db.refresh(existing)

            return existing

        result = DocumentIntelligenceResult(
            processing_id=processing_id,
            document_id=document_id,
            document_version_id=document_version_id,
            document_type=document_type,
            classification_confidence=normalized_confidence,
            structured_data=(
                structured_data if structured_data is not None else {}
            ),
            validation_results=(
                validation_results
                if validation_results is not None
                else {}
            ),
            artifacts=(
                artifacts if artifacts is not None else []
            ),
            knowledge=(
                knowledge if knowledge is not None else {}
            ),
            raw_text=raw_text,
        )

        self.db.add(result)

        await self.db.flush()
        await self.db.refresh(result)

        return result

    # ------------------------------------------------------------------
    # GET
    # ------------------------------------------------------------------

    async def get_result(
        self,
        result_id: UUID,
    ) -> DocumentIntelligenceResult | None:
        """
        Retrieve a result by its primary key.
        """

        stmt = select(DocumentIntelligenceResult).where(
            DocumentIntelligenceResult.id == result_id
        )

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()

    async def get_by_processing_id(
        self,
        processing_id: UUID,
    ) -> DocumentIntelligenceResult | None:
        """
        Retrieve the canonical intelligence result associated with a
        processing job.
        """

        stmt = select(DocumentIntelligenceResult).where(
            DocumentIntelligenceResult.processing_id == processing_id
        )

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------

    async def update_result(
        self,
        result_id: UUID,
        *,
        document_type: str | None = None,
        classification_confidence: float | None = None,
        structured_data: dict[str, Any] | None = None,
        validation_results: dict[str, Any] | None = None,
        artifacts: list[Any] | None = None,
        knowledge: dict[str, Any] | None = None,
        raw_text: str | None = None,
    ) -> DocumentIntelligenceResult | None:
        """
        Update an existing intelligence result.

        Does not commit.
        """

        result = await self.get_result(result_id)

        if result is None:
            return None

        if document_type is not None:
            result.document_type = document_type

        if classification_confidence is not None:
            result.classification_confidence = (
                self._normalize_confidence(
                    classification_confidence
                )
            )

        if structured_data is not None:
            result.structured_data = structured_data

        if validation_results is not None:
            result.validation_results = validation_results

        if artifacts is not None:
            result.artifacts = artifacts

        if knowledge is not None:
            result.knowledge = knowledge

        if raw_text is not None:
            result.raw_text = raw_text

        await self.db.flush()
        await self.db.refresh(result)

        return result

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------

    async def delete_result(
        self,
        result_id: UUID,
    ) -> bool:
        """
        Delete an intelligence result.

        Does not commit.
        """

        result = await self.get_result(result_id)

        if result is None:
            return False

        await self.db.delete(result)
        await self.db.flush()

        return True

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_confidence(
        value: float | None,
    ) -> float | None:
        """
        Normalize classification confidence into [0, 1].
        """

        if value is None:
            return None

        try:
            confidence = float(value)
        except (TypeError, ValueError):
            return None

        if confidence != confidence:
            return None

        if confidence == float("inf"):
            return 1.0

        if confidence == float("-inf"):
            return 0.0

        return max(0.0, min(1.0, confidence))