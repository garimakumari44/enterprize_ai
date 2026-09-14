
"""
app/repositories/ai/provider_repository.py

Repository for AI provider persistence.
"""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.ai_provider import AIProvider


class ProviderRepository:
    """
    Repository for AI Provider management.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self,
        provider: AIProvider,
    ) -> AIProvider:
        self.db.add(provider)

        await self.db.commit()
        await self.db.refresh(provider)

        return provider

    async def get_by_id(
        self,
        provider_id: int,
    ) -> Optional[AIProvider]:
        result = await self.db.execute(
            select(AIProvider).where(
                AIProvider.id == provider_id
            )
        )

        return result.scalar_one_or_none()

    async def get_by_name(
        self,
        name: str,
    ) -> Optional[AIProvider]:
        result = await self.db.execute(
            select(AIProvider).where(
                AIProvider.name == name
            )
        )

        return result.scalar_one_or_none()

    async def get_all(
        self,
    ) -> List[AIProvider]:
        result = await self.db.execute(
            select(AIProvider).order_by(
                AIProvider.created_at.desc()
            )
        )

        return list(result.scalars().all())

    async def get_active_providers(
        self,
    ) -> List[AIProvider]:
        result = await self.db.execute(
            select(AIProvider)
            .where(AIProvider.is_active.is_(True))
            .order_by(AIProvider.name)
        )

        return list(result.scalars().all())

    async def update(
        self,
        provider_id: int,
        data: dict,
    ) -> Optional[AIProvider]:
        if not data:
            return await self.get_by_id(provider_id)

        await self.db.execute(
            update(AIProvider)
            .where(AIProvider.id == provider_id)
            .values(**data)
        )

        await self.db.commit()

        return await self.get_by_id(provider_id)

    async def delete(
        self,
        provider_id: int,
    ) -> bool:
        result = await self.db.execute(
            delete(AIProvider).where(
                AIProvider.id == provider_id
            )
        )

        await self.db.commit()

        return result.rowcount > 0

