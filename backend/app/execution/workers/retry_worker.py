"""
Retry Worker

Moves failed jobs back
to execution queue.
"""


import logging


from app.workers.worker import Worker


logger = logging.getLogger(__name__)


class RetryWorker(Worker):


    def __init__(
        self,
        queue_manager
    ):

        super().__init__(
            name="retry-worker",
            interval=10
        )

        self.queue = queue_manager



    async def process(self):


        jobs = await self.queue.get_retry_jobs()


        for job in jobs:


            if job["retry_count"] >= job["max_retry"]:

                logger.warning(
                    f"Job permanently failed {job}"
                )

                await self.queue.dead_letter(
                    job
                )

                continue



            await self.queue.retry_job(
                job
            )


            logger.info(
                f"Retry scheduled {job}"
            )