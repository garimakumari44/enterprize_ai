"""
Base Worker

Provides common functionality for all background workers.
"""


import asyncio
import logging
from abc import ABC, abstractmethod


from app.workers.heartbeat import WorkerHeartbeat


logger = logging.getLogger(__name__)


class Worker(ABC):

    def __init__(
        self,
        name: str,
        interval: int = 5
    ):
        self.name = name
        self.interval = interval

        self.running = False

        self.heartbeat = WorkerHeartbeat(
            worker_name=name
        )


    async def start(self):

        logger.info(
            f"Starting worker: {self.name}"
        )

        self.running = True

        await self.heartbeat.start()

        while self.running:

            try:

                await self.process()

            except Exception as e:

                logger.exception(
                    f"Worker {self.name} failed: {e}"
                )

            await asyncio.sleep(
                self.interval
            )


    async def stop(self):

        logger.info(
            f"Stopping worker: {self.name}"
        )

        self.running = False

        await self.heartbeat.stop()


    @abstractmethod
    async def process(self):
        """
        Worker logic.
        """
        pass