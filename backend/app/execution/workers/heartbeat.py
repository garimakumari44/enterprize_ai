"""
Worker heartbeat manager.
"""


import asyncio
import logging
from datetime import datetime


logger = logging.getLogger(__name__)



class WorkerHeartbeat:


    def __init__(
        self,
        worker_name:str
    ):

        self.worker_name = worker_name
        self.running=False



    async def start(self):

        self.running=True

        asyncio.create_task(
            self._heartbeat_loop()
        )



    async def stop(self):

        self.running=False



    async def _heartbeat_loop(self):

        while self.running:


            await self.send_heartbeat()


            await asyncio.sleep(
                15
            )



    async def send_heartbeat(self):

        logger.debug(
            f"""
            Worker heartbeat

            Worker:
            {self.worker_name}

            Time:
            {datetime.utcnow()}
            """
        )