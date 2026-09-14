from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.processing.extraction_result import ExtractionResult


class ExtractionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        extraction: ExtractionResult,
    ) -> ExtractionResult:
        self.db.add(extraction)
        await self.db.commit()
        await self.db.refresh(extraction)
        return extraction

    async def get(
        self,
        extraction_id: uuid.UUID,
    ) -> ExtractionResult | None:
        result = await self.db.execute(
            select(ExtractionResult).where(
                ExtractionResult.id == extraction_id
            )
        )
        return result.scalar_one_or_none()

    async def get_by_job(
        self,
        job_id: uuid.UUID,
    ) -> list[ExtractionResult]:
        result = await self.db.execute(
            select(ExtractionResult)
            .where(ExtractionResult.processing_job_id == job_id)
        )
        return list(result.scalars().all())

    async def update(
        self,
        extraction: ExtractionResult,
    ) -> ExtractionResult:
        await self.db.commit()
        await self.db.refresh(extraction)
        return extraction

    async def delete(
        self,
        extraction: ExtractionResult,
    ) -> None:
        await self.db.delete(extraction)
        await self.db.commit()