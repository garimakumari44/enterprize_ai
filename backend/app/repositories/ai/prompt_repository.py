from typing import Optional, List

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai.prompt import Prompt


class PromptRepository:
    """
    Repository for AI Prompt database operations.
    """

    def __init__(self, db: AsyncSession):
        self.db = db


    async def create(
        self,
        prompt: Prompt
    ) -> Prompt:
        """
        Create new prompt
        """

        self.db.add(prompt)

        await self.db.commit()
        await self.db.refresh(prompt)

        return prompt


    async def get_by_id(
        self,
        prompt_id: int
    ) -> Optional[Prompt]:

        result = await self.db.execute(
            select(Prompt)
            .where(
                Prompt.id == prompt_id
            )
        )

        return result.scalar_one_or_none()


    async def get_all(
        self
    ) -> List[Prompt]:

        result = await self.db.execute(
            select(Prompt)
            .order_by(
                Prompt.created_at.desc()
            )
        )

        return list(
            result.scalars().all()
        )


    async def get_by_name(
        self,
        name: str
    ) -> Optional[Prompt]:

        result = await self.db.execute(
            select(Prompt)
            .where(
                Prompt.name == name
            )
        )

        return result.scalar_one_or_none()


    async def update(
        self,
        prompt_id: int,
        data: dict
    ) -> Optional[Prompt]:

        await self.db.execute(
            update(Prompt)
            .where(
                Prompt.id == prompt_id
            )
            .values(
                **data
            )
        )

        await self.db.commit()

        return await self.get_by_id(prompt_id)



    async def delete(
        self,
        prompt_id: int
    ) -> bool:

        result = await self.db.execute(
            delete(Prompt)
            .where(
                Prompt.id == prompt_id
            )
        )

        await self.db.commit()

        return result.rowcount > 0