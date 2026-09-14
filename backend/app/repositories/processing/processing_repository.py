from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.processing_job import ProcessingJob


class ProcessingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, job: ProcessingJob) -> ProcessingJob:
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def get(self, job_id: uuid.UUID) -> ProcessingJob | None:
        result = await self.db.execute(
            select(ProcessingJob).where(ProcessingJob.id == job_id)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        skip: int = 0,
        limit: int = 50,
    ) -> list[ProcessingJob]:
        result = await self.db.execute(
            select(ProcessingJob)
            .offset(skip)
            .limit(limit)
            .order_by(ProcessingJob.created_at.desc())
        )
        return list(result.scalars().all())

    async def update(self, job: ProcessingJob) -> ProcessingJob:
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def delete(self, job: ProcessingJob) -> None:
        await self.db.delete(job)
        await self.db.commit()