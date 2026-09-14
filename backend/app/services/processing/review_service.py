
"""
app/services/processing/review_service.py

Business logic for human review of processing results.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.document_intelligence_result import (
    DocumentIntelligenceResult,
)
from app.db.models.review_record import (
    ReviewDecision,
    ReviewRecord,
    ReviewStatus,
)
from app.repositories.processing.review_repository import (
    ReviewRepository,
)


class ReviewService:
    """
    Service layer for processing-result reviews.

    Reviews belong to DocumentIntelligenceResult, which belongs
    to a processing job.
    """

    def __init__(
        self,
        db: AsyncSession,
    ):
        self.db = db
        self.repository = ReviewRepository(db)

    # ==================================================================
    # INTERNAL HELPERS
    # ==================================================================

    async def _get_intelligence_result(
        self,
        processing_id: uuid.UUID,
    ) -> DocumentIntelligenceResult | None:
        result = await self.db.execute(
            select(DocumentIntelligenceResult).where(
                DocumentIntelligenceResult.processing_id
                == processing_id
            )
        )

        return result.scalar_one_or_none()

    # ==================================================================
    # CREATE
    # ==================================================================

    async def create_review(
        self,
        *,
        processing_id: uuid.UUID,
        reviewer_id: uuid.UUID | None = None,
        reviewer_name: str | None = None,
        reviewer_email: str | None = None,
        comments: str | None = None,
        corrections: list[dict] | None = None,
    ) -> ReviewRecord:
        intelligence_result = await self._get_intelligence_result(
            processing_id
        )

        if intelligence_result is None:
            raise ValueError(
                "Cannot create review: "
                "document intelligence result does not exist."
            )

        review = ReviewRecord(
            intelligence_result_id=intelligence_result.id,
            reviewer_id=reviewer_id,
            reviewer_name=reviewer_name,
            reviewer_email=reviewer_email,
            status=ReviewStatus.PENDING.value,
            decision=None,
            comments=comments,
            corrections=(
                {"items": corrections}
                if corrections
                else None
            ),
        )

        return await self.repository.create(review)

    # ==================================================================
    # GET BY REVIEW ID
    # ==================================================================

    async def get_review(
        self,
        review_id: uuid.UUID,
    ) -> ReviewRecord | None:
        return await self.repository.get(review_id)

    # ==================================================================
    # GET BY PROCESSING ID
    # ==================================================================

    async def get_review_by_processing_id(
        self,
        processing_id: uuid.UUID,
    ) -> ReviewRecord | None:
        return await self.repository.get_by_processing_id(
            processing_id
        )

    # ==================================================================
    # LIST
    # ==================================================================

    async def list_reviews(
        self,
    ) -> list[ReviewRecord]:
        return await self.repository.list()

    async def list_reviews_by_processing_id(
        self,
        processing_id: uuid.UUID,
    ) -> list[ReviewRecord]:
        return await self.repository.list_by_processing_id(
            processing_id
        )

    # ==================================================================
    # SUBMIT REVIEW
    # ==================================================================

    async def submit_review(
        self,
        *,
        processing_id: uuid.UUID,
        decision: str,
        comments: str | None = None,
        corrections: list[dict] | None = None,
        reviewer_id: uuid.UUID | None = None,
        reviewer_name: str | None = None,
        reviewer_email: str | None = None,
    ) -> ReviewRecord:
        review = await self.get_review_by_processing_id(
            processing_id
        )

        if review is None:
            review = await self.create_review(
                processing_id=processing_id,
                reviewer_id=reviewer_id,
                reviewer_name=reviewer_name,
                reviewer_email=reviewer_email,
                comments=comments,
                corrections=corrections,
            )

        normalized_decision = decision.lower().strip()

        if normalized_decision in {
            ReviewDecision.APPROVE.value,
            ReviewStatus.APPROVED.value,
        }:
            review.approve(
                comments=comments,
            )

        elif normalized_decision in {
            ReviewDecision.REJECT.value,
            ReviewStatus.REJECTED.value,
        }:
            review.reject(
                comments=comments,
                corrections=(
                    {"items": corrections}
                    if corrections
                    else None
                ),
            )

        elif normalized_decision in {
            ReviewDecision.REQUEST_CHANGES.value,
            ReviewStatus.CHANGES_REQUESTED.value,
        }:
            review.request_changes(
                comments=comments,
                corrections=(
                    {"items": corrections}
                    if corrections
                    else None
                ),
            )

        else:
            raise ValueError(
                f"Unsupported review decision: {decision}"
            )

        return await self.repository.update(review)

    # ==================================================================
    # APPROVE BY PROCESSING ID
    # ==================================================================

    async def approve_by_processing_id(
        self,
        *,
        processing_id: uuid.UUID,
        comments: str | None = None,
    ) -> ReviewRecord:
        review = await self.get_review_by_processing_id(
            processing_id
        )

        if review is None:
            review = await self.create_review(
                processing_id=processing_id,
                comments=comments,
            )

        review.approve(
            comments=comments,
        )

        return await self.repository.update(review)

    # ==================================================================
    # REJECT BY PROCESSING ID
    # ==================================================================

    async def reject_by_processing_id(
        self,
        *,
        processing_id: uuid.UUID,
        comments: str | None = None,
        corrections: list[dict] | None = None,
    ) -> ReviewRecord:
        review = await self.get_review_by_processing_id(
            processing_id
        )

        if review is None:
            review = await self.create_review(
                processing_id=processing_id,
                comments=comments,
                corrections=corrections,
            )

        review.reject(
            comments=comments,
            corrections=(
                {"items": corrections}
                if corrections
                else None
            ),
        )

        return await self.repository.update(review)

    # ==================================================================
    # APPROVE BY REVIEW ID
    # ==================================================================

    async def approve(
        self,
        review_id: uuid.UUID,
        comments: str | None = None,
    ) -> ReviewRecord | None:
        review = await self.repository.get(review_id)

        if review is None:
            return None

        review.approve(
            comments=comments,
        )

        return await self.repository.update(review)

    # ==================================================================
    # REJECT BY REVIEW ID
    # ==================================================================

    async def reject(
        self,
        review_id: uuid.UUID,
        comments: str | None = None,
        corrections: list[dict] | None = None,
    ) -> ReviewRecord | None:
        review = await self.repository.get(review_id)

        if review is None:
            return None

        review.reject(
            comments=comments,
            corrections=(
                {"items": corrections}
                if corrections
                else None
            ),
        )

        return await self.repository.update(review)

    # ==================================================================
    # DELETE
    # ==================================================================

    async def delete_review(
        self,
        review_id: uuid.UUID,
    ) -> bool:
        review = await self.repository.get(review_id)

        if review is None:
            return False

        await self.repository.delete(review)

        return True
