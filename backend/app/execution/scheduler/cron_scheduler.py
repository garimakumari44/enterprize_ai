import asyncio
from datetime import datetime
import logging


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



class CronScheduler:
    """
    Executes cron based workflow schedules.

    Runs as a background service.
    """


    def __init__(
        self,
        session: AsyncSession,
        check_interval: int = 30
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
        Start scheduler loop.
        """

        logger.info(
            "Cron scheduler started"
        )


        self.running = True


        while self.running:

            try:

                await self.process_schedules()


            except Exception as e:

                logger.exception(
                    f"Cron scheduler error: {e}"
                )


            await asyncio.sleep(
                self.check_interval
            )



    async def stop(self):

        logger.info(
            "Stopping cron scheduler"
        )

        self.running = False



    async def process_schedules(self):

        """
        Find due cron schedules
        and execute them.
        """


        schedules = await self.repository.get_active_schedulers()


        now = datetime.utcnow()



        for scheduler in schedules:


            if scheduler.trigger_type != "cron":

                continue



            if scheduler.next_run_at <= now:


                logger.info(
                    f"Triggering workflow {scheduler.workflow_id}"
                )


                await self.execute_schedule(
                    scheduler
                )



    async def execute_schedule(
        self,
        scheduler
    ):

        """
        Fire workflow execution
        and update next run.
        """


        await self.trigger_manager.trigger_workflow(
            workflow_id=scheduler.workflow_id,
            scheduler_id=scheduler.id
        )



        next_run = self.scheduler_service.calculate_next_run(

            trigger_type="cron",

            cron_expression=scheduler.cron_expression,

            interval_seconds=None,

            run_at=None
        )



        await self.repository.update_next_run(
            scheduler.id,
            next_run
        )


        logger.info(
            f"Next cron run scheduled at {next_run}"
        )