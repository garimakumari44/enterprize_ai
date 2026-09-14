"""
Worker Manager

Responsible for managing the lifecycle
of all background workers.

Starts:
- Execution Worker
- Retry Worker
- Scheduler Worker
- Cleanup Worker

Handles:
- Startup
- Shutdown
- Worker registration
"""


import asyncio
import logging
from typing import List


from app.workers.worker import Worker
from app.workers.health import WorkerHealth


logger = logging.getLogger(__name__)


class WorkerManager:


    def __init__(self):

        self.workers: List[Worker] = []

        self.tasks = []

        self.running = False



    def register(
        self,
        worker: Worker
    ):
        """
        Register a worker.
        """

        self.workers.append(
            worker
        )

        logger.info(
            f"Registered worker: {worker.name}"
        )



    async def start(self):
        """
        Start all workers.
        """

        if self.running:
            return


        self.running = True


        logger.info(
            "Starting Worker Manager"
        )


        for worker in self.workers:


            WorkerHealth.register(
                worker.name
            )


            task = asyncio.create_task(
                worker.start()
            )


            self.tasks.append(
                task
            )


            logger.info(
                f"Started worker: {worker.name}"
            )



        await asyncio.gather(
            *self.tasks
        )



    async def stop(self):
        """
        Gracefully stop workers.
        """

        logger.info(
            "Stopping Worker Manager"
        )


        self.running = False



        for worker in self.workers:

            await worker.stop()



        for task in self.tasks:

            task.cancel()



        self.tasks.clear()


        logger.info(
            "All workers stopped"
        )



    def get_workers(self):
        """
        Return worker list.
        """

        return [
            {
                "name": worker.name,
                "status": "running"
                if self.running
                else "stopped"
            }

            for worker in self.workers
        ]