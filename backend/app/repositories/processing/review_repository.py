
"""
app/repositories/processing/review_repository.py

Repository for human review records.

Relationship
------------

ProcessingJob
    |
    v
DocumentIntelligenceResult
    |
    v
ReviewRecord

ReviewRecord does NOT directly reference ProcessingJob.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.document_intelligence_result import (
    DocumentIntelligenceResult,
)
from app.db.models.review_record import ReviewRecord


class ReviewRepository:
    """
    Async repository for ReviewRecord persistence and lookup.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------

    async def create(
        self,
        review: ReviewRecord,
    ) -> ReviewRecord:
        self.db.add(review)

        await self.db.commit()
        await self.db.refresh(review)

        return review

    # ------------------------------------------------------------------
    # GET BY REVIEW ID
    # ------------------------------------------------------------------

    async def get(
        self,
        review_id: uuid.UUID,
    ) -> ReviewRecord | None:
        result = await self.db.execute(
            select(ReviewRecord).where(
                ReviewRecord.id == review_id
            )
        )

        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # GET LATEST REVIEW BY PROCESSING ID
    # ------------------------------------------------------------------

    async def get_by_processing_id(
        self,
        processing_id: uuid.UUID,
    ) -> ReviewRecord | None:
        """
        Resolve a review through DocumentIntelligenceResult.

        ProcessingJob
            -> DocumentIntelligenceResult
            -> ReviewRecord
        """

        result = await self.db.execute(
            select(ReviewRecord)
            .join(
                DocumentIntelligenceResult,
                ReviewRecord.intelligence_result_id
                == DocumentIntelligenceResult.id,
            )
            .where(
                DocumentIntelligenceResult.processing_id
                == processing_id
            )
            .order_by(
                ReviewRecord.created_at.desc()
            )
            .limit(1)
        )

        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # LIST REVIEWS BY PROCESSING ID
    # ------------------------------------------------------------------

    async def list_by_processing_id(
        self,
        processing_id: uuid.UUID,
    ) -> list[ReviewRecord]:
        result = await self.db.execute(
            select(ReviewRecord)
            .join(
                DocumentIntelligenceResult,
                ReviewRecord.intelligence_result_id
                == DocumentIntelligenceResult.id,
            )
            .where(
                DocumentIntelligenceResult.processing_id
                == processing_id
            )
            .order_by(
                ReviewRecord.created_at.desc()
            )
        )

        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # LIST ALL
    # ------------------------------------------------------------------

    async def list(
        self,
    ) -> list[ReviewRecord]:
        result = await self.db.execute(
            select(ReviewRecord).order_by(
                ReviewRecord.created_at.desc()
            )
        )

        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------

    async def update(
        self,
        review: ReviewRecord,
    ) -> ReviewRecord:
        await self.db.commit()
        await self.db.refresh(review)

        return review

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------

    async def delete(
        self,
        review: ReviewRecord,
    ) -> None:
        await self.db.delete(review)
        await self.db.commit()

