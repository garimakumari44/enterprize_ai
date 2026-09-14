from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.processing.processing_template import ProcessingTemplate


class TemplateRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        template: ProcessingTemplate,
    ) -> ProcessingTemplate:
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def get(
        self,
        template_id: uuid.UUID,
    ) -> ProcessingTemplate | None:
        result = await self.db.execute(
            select(ProcessingTemplate).where(
                ProcessingTemplate.id == template_id
            )
        )
        return result.scalar_one_or_none()

    async def list(self) -> list[ProcessingTemplate]:
        result = await self.db.execute(
            select(ProcessingTemplate)
            .order_by(ProcessingTemplate.name)
        )
        return list(result.scalars().all())

    async def update(
        self,
        template: ProcessingTemplate,
    ) -> ProcessingTemplate:
        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def delete(
        self,
        template: ProcessingTemplate,
    ) -> None:
        await self.db.delete(template)
        await self.db.commit()