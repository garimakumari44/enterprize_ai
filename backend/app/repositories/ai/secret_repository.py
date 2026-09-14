
"""
app/repositories/ai/secret_repository.py

Repository for AI secret persistence.
"""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.ai_secret import AISecret


class SecretRepository:
    """
    Repository for AI Secret storage.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self,
        secret: AISecret,
    ) -> AISecret:
        self.db.add(secret)

        await self.db.commit()
        await self.db.refresh(secret)

        return secret

    async def get_by_id(
        self,
        secret_id: int,
    ) -> Optional[AISecret]:
        result = await self.db.execute(
            select(AISecret).where(
                AISecret.id == secret_id
            )
        )

        return result.scalar_one_or_none()

    async def get_by_provider(
        self,
        provider_id: int,
    ) -> Optional[AISecret]:
        result = await self.db.execute(
            select(AISecret)
            .where(AISecret.provider_id == provider_id)
            .order_by(AISecret.created_at.desc())
        )

        return result.scalars().first()

    async def get_all(
        self,
    ) -> List[AISecret]:
        result = await self.db.execute(
            select(AISecret)
            .order_by(AISecret.created_at.desc())
        )

        return list(result.scalars().all())

    async def delete(
        self,
        secret_id: int,
    ) -> bool:
        result = await self.db.execute(
            delete(AISecret).where(
                AISecret.id == secret_id
            )
        )

        await self.db.commit()

        return result.rowcount > 0
