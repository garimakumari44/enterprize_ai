import asyncio
import logging
from datetime import datetime, timedelta


from sqlalchemy.ext.asyncio import AsyncSession


from app.execution.scheduler.scheduler_repository import (
    SchedulerRepository
)


from app.execution.scheduler.scheduler_service import (
    SchedulerService
)


from app.execution.scheduler.trigger_manager import (
    TriggerManager
)



logger = logging.getLogger(__name__)



class IntervalScheduler:
    """
    Executes interval based workflow schedules.

    Example:

    Every 5 minutes
    Every 1 hour

    Runs as a background service.
    """


    def __init__(
        self,
        session: AsyncSession,
        check_interval: int = 10
    ):

        self.repository = SchedulerRepository(
            session
        )


        self.scheduler_service = SchedulerService(
            session
        )


        self.trigger_manager = TriggerManager()


        self.check_interval = check_interval


        self.running = False



    async def start(self):

        """
        Start interval scheduler loop.
        """


        logger.info(
            "Interval scheduler started"
        )


        self.running = True


        while self.running:


            try:

                await self.process_intervals()


            except Exception as e:

                logger.exception(
                    f"Interval scheduler error: {e}"
                )


            await asyncio.sleep(
                self.check_interval
            )



    async def stop(self):

        logger.info(
            "Stopping interval scheduler"
        )


        self.running = False




    async def process_intervals(self):

        """
        Check interval schedules
        that are ready for execution.
        """


        schedules = await self.repository.get_active_schedulers()


        now = datetime.utcnow()



        for scheduler in schedules:


            if scheduler.trigger_type != "interval":

                continue



            if scheduler.next_run_at <= now:


                logger.info(
                    f"Executing interval workflow {scheduler.workflow_id}"
                )


                await self.execute_schedule(
                    scheduler
                )





    async def execute_schedule(
        self,
        scheduler
    ):

        """
        Trigger workflow execution
        and calculate next interval run.
        """


        await self.trigger_manager.trigger_workflow(

            workflow_id=scheduler.workflow_id,

            scheduler_id=scheduler.id

        )



        next_run = datetime.utcnow() + timedelta(

            seconds=scheduler.interval_seconds

        )



        await self.repository.update_next_run(

            scheduler.id,

            next_run

        )



        logger.info(

            f"Next interval execution scheduled at {next_run}"

        )