"""
Scheduler Worker

Creates workflow execution
jobs based on schedules.
"""


import logging
from datetime import datetime


from app.workers.worker import Worker



logger = logging.getLogger(__name__)


class SchedulerWorker(Worker):


    def __init__(
        self,
        scheduler_service
    ):

        super().__init__(
            name="scheduler-worker",
            interval=30
        )

        self.scheduler = scheduler_service



    async def process(self):


        schedules = await self.scheduler.get_due_jobs()


        for schedule in schedules:


            await self.scheduler.trigger(
                schedule
            )


            logger.info(
                f"Triggered schedule {schedule.id}"
            )