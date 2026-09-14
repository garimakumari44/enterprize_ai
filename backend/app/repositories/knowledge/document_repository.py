from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge.indexed_document import IndexedDocument


class DocumentRepository:
    """Repository for indexed documents."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        document: IndexedDocument,
    ) -> IndexedDocument:
        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)
        return document

    async def get_by_id(
        self,
        document_id: str,
    ) -> Optional[IndexedDocument]:
        result = await self.db.execute(
            select(IndexedDocument).where(
                IndexedDocument.id == document_id
            )
        )
        return result.scalar_one_or_none()

    async def get_by_collection(
        self,
        collection_id: str,
    ) -> List[IndexedDocument]:
        result = await self.db.execute(
            select(IndexedDocument).where(
                IndexedDocument.collection_id == collection_id
            )
        )
        return list(result.scalars().all())

    async def list_all(self) -> List[IndexedDocument]:
        result = await self.db.execute(
            select(IndexedDocument)
        )
        return list(result.scalars().all())

    async def update(
        self,
        document: IndexedDocument,
    ) -> IndexedDocument:
        await self.db.commit()
        await self.db.refresh(document)
        return document

    async def delete(
        self,
        document_id: str,
    ) -> None:
        await self.db.execute(
            delete(IndexedDocument).where(
                IndexedDocument.id == document_id
            )
        )
        await self.db.commit()