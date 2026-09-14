from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.execution.models.scheduler import Scheduler


class SchedulerRepository:
    """
    Database operations for workflow schedules.
    """


    def __init__(self, session: AsyncSession):
        self.session = session


    async def create(
        self,
        scheduler: Scheduler
    ) -> Scheduler:

        self.session.add(scheduler)

        await self.session.commit()

        await self.session.refresh(scheduler)

        return scheduler



    async def get_by_id(
        self,
        scheduler_id: UUID
    ) -> Optional[Scheduler]:

        result = await self.session.execute(
            select(Scheduler)
            .where(
                Scheduler.id == scheduler_id
            )
        )

        return result.scalar_one_or_none()



    async def get_active_schedulers(
        self
    ) -> List[Scheduler]:

        result = await self.session.execute(
            select(Scheduler)
            .where(
                Scheduler.is_active == True
            )
        )

        return list(result.scalars().all())



    async def update_next_run(
        self,
        scheduler_id: UUID,
        next_run: datetime
    ):


        await self.session.execute(
            update(Scheduler)
            .where(
                Scheduler.id == scheduler_id
            )
            .values(
                next_run_at=next_run
            )
        )


        await self.session.commit()



    async def disable(
        self,
        scheduler_id: UUID
    ):

        await self.session.execute(
            update(Scheduler)
            .where(
                Scheduler.id == scheduler_id
            )
            .values(
                is_active=False
            )
        )

        await self.session.commit()



    async def delete(
        self,
        scheduler_id: UUID
    ):

        await self.session.execute(
            delete(Scheduler)
            .where(
                Scheduler.id == scheduler_id
            )
        )

        await self.session.commit()