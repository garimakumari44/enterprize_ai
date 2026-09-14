"""
Execution Worker

Consumes execution jobs
and runs workflows.
"""


import logging


from app.workers.worker import Worker
from app.queue.queue_manager import QueueManager
from app.execution.services.execution_service import ExecutionService


logger = logging.getLogger(__name__)


class ExecutionWorker(Worker):


    def __init__(
        self,
        queue_manager: QueueManager,
        execution_service: ExecutionService
    ):

        super().__init__(
            name="execution-worker"
        )

        self.queue = queue_manager
        self.execution_service = execution_service



    async def process(self):

        job = await self.queue.get_job(
            queue_name="execution"
        )


        if not job:
            return


        execution_id = job["execution_id"]


        logger.info(
            f"Executing workflow {execution_id}"
        )


        try:

            await self.execution_service.execute(
                execution_id
            )


            await self.queue.complete_job(
                job
            )


        except Exception as error:


            logger.error(
                f"Execution failed {execution_id}"
            )


            await self.queue.fail_job(
                job,
                error=str(error)
            )