from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge.knowledge_collection import KnowledgeCollection


class KnowledgeRepository:
    """Repository for Knowledge Collections."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        collection: KnowledgeCollection,
    ) -> KnowledgeCollection:
        self.db.add(collection)
        await self.db.commit()
        await self.db.refresh(collection)
        return collection

    async def get_by_id(
        self,
        collection_id: str,
    ) -> Optional[KnowledgeCollection]:
        result = await self.db.execute(
            select(KnowledgeCollection).where(
                KnowledgeCollection.id == collection_id
            )
        )
        return result.scalar_one_or_none()

    async def get_by_name(
        self,
        name: str,
    ) -> Optional[KnowledgeCollection]:
        result = await self.db.execute(
            select(KnowledgeCollection).where(
                KnowledgeCollection.name == name
            )
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> List[KnowledgeCollection]:
        result = await self.db.execute(
            select(KnowledgeCollection)
        )
        return list(result.scalars().all())

    async def update(
        self,
        collection: KnowledgeCollection,
    ) -> KnowledgeCollection:
        await self.db.commit()
        await self.db.refresh(collection)
        return collection

    async def delete(
        self,
        collection_id: str,
    ) -> None:
        await self.db.execute(
            delete(KnowledgeCollection).where(
                KnowledgeCollection.id == collection_id
            )
        )
        await self.db.commit()