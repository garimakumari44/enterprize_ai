from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.review.models.review_task import ReviewTask


class ReviewRepository:
    """
    Repository for ReviewTask persistence.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, review: ReviewTask) -> ReviewTask:
        self.db.add(review)
        await self.db.flush()
        await self.db.refresh(review)
        return review

    async def get_by_id(self, review_id: UUID) -> ReviewTask | None:
        result = await self.db.execute(
            select(ReviewTask).where(ReviewTask.id == review_id)
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> list[ReviewTask]:
        result = await self.db.execute(
            select(ReviewTask).order_by(ReviewTask.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_pending(self) -> list[ReviewTask]:
        result = await self.db.execute(
            select(ReviewTask).where(
                ReviewTask.status == "PENDING"
            )
        )
        return list(result.scalars().all())

    async def get_by_workflow_execution(
        self,
        execution_id: UUID,
    ) -> list[ReviewTask]:
        result = await self.db.execute(
            select(ReviewTask).where(
                ReviewTask.workflow_execution_id == execution_id
            )
        )
        return list(result.scalars().all())

    async def update(self, review: ReviewTask) -> ReviewTask:
        await self.db.flush()
        await self.db.refresh(review)
        return review

    async def delete(self, review: ReviewTask) -> None:
        await self.db.delete(review)

    async def count_pending(self) -> int:
        result = await self.db.execute(
            select(ReviewTask).where(
                ReviewTask.status == "PENDING"
            )
        )
        return len(result.scalars().all())