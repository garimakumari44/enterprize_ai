from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.review.models.reviewer_assignment import ReviewerAssignment


class AssignmentRepository:
    """
    Repository for reviewer assignments.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        assignment: ReviewerAssignment,
    ) -> ReviewerAssignment:
        self.db.add(assignment)
        await self.db.flush()
        await self.db.refresh(assignment)
        return assignment

    async def get_by_id(
        self,
        assignment_id: UUID,
    ) -> ReviewerAssignment | None:
        result = await self.db.execute(
            select(ReviewerAssignment).where(
                ReviewerAssignment.id == assignment_id
            )
        )
        return result.scalar_one_or_none()

    async def get_by_review(
        self,
        review_id: UUID,
    ) -> list[ReviewerAssignment]:
        result = await self.db.execute(
            select(ReviewerAssignment).where(
                ReviewerAssignment.review_task_id == review_id
            )
        )
        return list(result.scalars().all())

    async def get_active_assignment(
        self,
        review_id: UUID,
    ) -> ReviewerAssignment | None:
        result = await self.db.execute(
            select(ReviewerAssignment).where(
                ReviewerAssignment.review_task_id == review_id,
                ReviewerAssignment.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def get_reviewer_tasks(
        self,
        reviewer_id: UUID,
    ) -> list[ReviewerAssignment]:
        result = await self.db.execute(
            select(ReviewerAssignment).where(
                ReviewerAssignment.reviewer_id == reviewer_id,
                ReviewerAssignment.is_active.is_(True),
            )
        )
        return list(result.scalars().all())

    async def reassign(
        self,
        assignment: ReviewerAssignment,
        new_reviewer: UUID,
    ) -> ReviewerAssignment:
        assignment.reviewer_id = new_reviewer
        await self.db.flush()
        await self.db.refresh(assignment)
        return assignment

    async def deactivate(
        self,
        assignment: ReviewerAssignment,
    ) -> ReviewerAssignment:
        assignment.is_active = False
        await self.db.flush()
        await self.db.refresh(assignment)
        return assignment

    async def delete(
        self,
        assignment: ReviewerAssignment,
    ) -> None:
        await self.db.delete(assignment)