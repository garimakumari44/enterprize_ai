import logging
from datetime import datetime
from uuid import uuid4, UUID


from app.queue.job_dispatcher import (
    JobDispatcher
)


from app.queue.job_serializer import (
    JobSerializer
)



logger = logging.getLogger(__name__)




class TriggerManager:
    """
    Responsible for converting scheduler events
    into execution jobs.
    """



    def __init__(self):

        self.dispatcher = JobDispatcher()

        self.serializer = JobSerializer()



    async def trigger_workflow(
        self,
        workflow_id: UUID,
        scheduler_id: UUID
    ):
        """
        Create and dispatch workflow execution job.
        """


        execution_id = uuid4()



        job = {

            "job_id": str(uuid4()),

            "execution_id": str(execution_id),

            "workflow_id": str(workflow_id),

            "trigger_type": "scheduler",

            "scheduler_id": str(scheduler_id),

            "created_at": datetime.utcnow().isoformat()

        }



        serialized_job = self.serializer.serialize(
            job
        )



        await self.dispatcher.dispatch(

            queue_name="workflow_execution",

            payload=serialized_job

        )



        logger.info(

            f"Workflow triggered: {workflow_id}, execution={execution_id}"

        )



        return execution_id