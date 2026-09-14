"""
Cleanup Worker

Maintains database hygiene.
"""


import logging


from app.workers.worker import Worker


logger = logging.getLogger(__name__)



class CleanupWorker(Worker):


    def __init__(
        self,
        cleanup_service
    ):

        super().__init__(
            name="cleanup-worker",
            interval=3600
        )

        self.cleanup = cleanup_service



    async def process(self):


        logger.info(
            "Running cleanup"
        )


        await self.cleanup.remove_old_logs()


        await self.cleanup.remove_old_executions()