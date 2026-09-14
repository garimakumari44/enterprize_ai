from datetime import datetime, timezone, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.execution.scheduler.scheduler_repository import (
    SchedulerRepository
)

from app.execution.exceptions.execution_exception import (
    ExecutionException
)
from croniter import croniter

from app.execution.models.scheduler import Scheduler



class SchedulerService:
    """
    Business logic layer for workflow scheduling.

    Responsible for:
    - Creating schedules
    - Validating triggers
    - Calculating next execution
    - Managing lifecycle
    """



    VALID_TRIGGER_TYPES = {
        "cron",
        "interval",
        "one_time"
    }



    def __init__(
        self,
        session: AsyncSession
    ):

        self.repository = SchedulerRepository(
            session
        )



    async def create_schedule(
        self,
        workflow_id: UUID,
        trigger_type: str,
        cron_expression: Optional[str] = None,
        interval_seconds: Optional[int] = None,
        run_at: Optional[datetime] = None
    ) -> Scheduler:


        self._validate_trigger(
            trigger_type,
            cron_expression,
            interval_seconds,
            run_at
        )


        next_run = self.calculate_next_run(
            trigger_type=trigger_type,
            cron_expression=cron_expression,
            interval_seconds=interval_seconds,
            run_at=run_at
        )


        scheduler = Scheduler(

            workflow_id=workflow_id,

            trigger_type=trigger_type,

            cron_expression=cron_expression,

            interval_seconds=interval_seconds,

            run_at=run_at,

            next_run_at=next_run,

            is_active=True
        )


        return await self.repository.create(
            scheduler
        )



    async def get_schedule(
        self,
        scheduler_id: UUID
    ) -> Scheduler:


        scheduler = await self.repository.get_by_id(
            scheduler_id
        )


        if not scheduler:
            raise ExecutionException(
                "Scheduler not found"
            )


        return scheduler



    async def enable_schedule(
        self,
        scheduler_id: UUID
    ):


        scheduler = await self.get_schedule(
            scheduler_id
        )


        scheduler.is_active = True


        await self.repository.commit()


        return scheduler



    async def disable_schedule(
        self,
        scheduler_id: UUID
    ):


        scheduler = await self.get_schedule(
            scheduler_id
        )


        await self.repository.disable(
            scheduler_id
        )


        return {
            "scheduler_id": str(scheduler_id),
            "status": "disabled"
        }



    async def delete_schedule(
        self,
        scheduler_id: UUID
    ):


        await self.get_schedule(
            scheduler_id
        )


        await self.repository.delete(
            scheduler_id
        )


        return {
            "scheduler_id": str(scheduler_id),
            "status": "deleted"
        }



    async def update_next_execution(
        self,
        scheduler_id: UUID
    ):


        scheduler = await self.get_schedule(
            scheduler_id
        )


        next_run = self.calculate_next_run(

            trigger_type=scheduler.trigger_type,

            cron_expression=scheduler.cron_expression,

            interval_seconds=scheduler.interval_seconds,

            run_at=scheduler.run_at

        )


        await self.repository.update_next_run(

            scheduler_id,

            next_run

        )


        return next_run



    def calculate_next_run(
        self,
        trigger_type: str,
        cron_expression: Optional[str],
        interval_seconds: Optional[int],
        run_at: Optional[datetime]
    ) -> datetime:



        now = datetime.now(
            timezone.utc
        )



        if trigger_type == "one_time":


            if not run_at:

                raise ExecutionException(
                    "run_at is required"
                )


            return run_at



        elif trigger_type == "interval":


            return now + timedelta(
                seconds=interval_seconds
            )



        elif trigger_type == "cron":


            return self.calculate_cron(
                cron_expression
            )



        raise ExecutionException(
            "Unsupported trigger type"
        )



    def calculate_cron(
        self,
        expression: str
    ) -> datetime:


        if not expression:

            raise ExecutionException(
                "Cron expression required"
            )


        


        now = datetime.now(
            timezone.utc
        )


        iterator = croniter(
            expression,
            now
        )


        return iterator.get_next(
            datetime
        )



    def _validate_trigger(
        self,
        trigger_type: str,
        cron_expression: Optional[str],
        interval_seconds: Optional[int],
        run_at: Optional[datetime]
    ):


        if trigger_type not in self.VALID_TRIGGER_TYPES:

            raise ExecutionException(
                f"Invalid trigger type {trigger_type}"
            )



        if trigger_type == "cron":

            if not cron_expression:

                raise ExecutionException(
                    "Cron expression required"
                )



        if trigger_type == "interval":

            if not interval_seconds:

                raise ExecutionException(
                    "Interval seconds required"
                )


            if interval_seconds <= 0:

                raise ExecutionException(
                    "Interval must be greater than zero"
                )



        if trigger_type == "one_time":

            if not run_at:

                raise ExecutionException(
                    "run_at required"
                )