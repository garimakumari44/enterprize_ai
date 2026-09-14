import asyncio
import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession


from app.execution.scheduler.scheduler_repository import (
    SchedulerRepository
)


from app.execution.scheduler.trigger_manager import (
    TriggerManager
)



logger = logging.getLogger(__name__)




class OneTimeScheduler:
    """
    Executes one-time workflow schedules.

    Example:

    Execute workflow at:
    2026-07-20 10:30

    After execution:
    schedule is disabled.
    """



    def __init__(
        self,
        session: AsyncSession,
        check_interval: int = 10
    ):


        self.repository = SchedulerRepository(
            session
        )


        self.trigger_manager = TriggerManager()


        self.check_interval = check_interval


        self.running = False



    async def start(self):

        """
        Start background one-time scheduler.
        """


        logger.info(
            "One time scheduler started"
        )


        self.running = True



        while self.running:


            try:

                await self.process_schedules()


            except Exception as e:

                logger.exception(
                    f"One time scheduler error: {e}"
                )



            await asyncio.sleep(
                self.check_interval
            )




    async def stop(self):

        logger.info(
            "Stopping one time scheduler"
        )


        self.running = False




    async def process_schedules(self):

        """
        Find one-time schedules ready
        for execution.
        """


        schedules = await self.repository.get_active_schedulers()


        now = datetime.utcnow()



        for scheduler in schedules:


            if scheduler.trigger_type != "one_time":

                continue



            if scheduler.run_at <= now:


                logger.info(
                    f"Executing one time workflow {scheduler.workflow_id}"
                )


                await self.execute_schedule(
                    scheduler
                )





    async def execute_schedule(
        self,
        scheduler
    ):

        """
        Trigger workflow once
        and disable schedule.
        """


        await self.trigger_manager.trigger_workflow(

            workflow_id=scheduler.workflow_id,

            scheduler_id=scheduler.id

        )


        await self.repository.disable(
            scheduler.id
        )


        logger.info(

            f"One time workflow completed: {scheduler.workflow_id}"

        )