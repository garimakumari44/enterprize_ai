"""
Queue Monitor.

Monitors workflow execution queues.

Responsibilities:
- Queue statistics
- Backlog detection
- Queue health
- Job throughput tracking
"""

from time import time
from typing import Dict


from app.execution.monitoring.logger import (
    execution_logger
)

from app.execution.monitoring.metrics import (
    metrics
)



class QueueMonitor:
    """
    Queue health monitoring service.
    """


    def __init__(self):

        # Queue registry

        self.queues: Dict[str, dict] = {}



    # ==================================================
    # Register Queue
    # ==================================================

    def register_queue(
        self,
        queue_name: str
    ):
        """
        Register execution queue.
        """


        self.queues[queue_name] = {

            "name": queue_name,

            "created_at": time(),

            "pending_jobs": 0,

            "processing_jobs": 0,

            "completed_jobs": 0,

            "failed_jobs": 0,

            "last_job_time": None
        }



        execution_logger.info(
            "Queue registered",
            {
                "queue": queue_name
            }
        )



    # ==================================================
    # Job Added
    # ==================================================

    def job_added(
        self,
        queue_name: str
    ):
        """
        Called when job enters queue.
        """


        queue = self.queues.get(
            queue_name
        )


        if not queue:
            return



        queue["pending_jobs"] += 1



        metrics.increment(
            "queue.jobs.added"
        )



    # ==================================================
    # Job Started
    # ==================================================

    def job_started(
        self,
        queue_name: str
    ):
        """
        Called when worker picks job.
        """


        queue = self.queues.get(
            queue_name
        )


        if not queue:
            return



        queue["pending_jobs"] = max(
            0,
            queue["pending_jobs"] - 1
        )


        queue["processing_jobs"] += 1



        metrics.increment(
            "queue.jobs.processing"
        )



    # ==================================================
    # Job Completed
    # ==================================================

    def job_completed(
        self,
        queue_name: str
    ):

        queue = self.queues.get(
            queue_name
        )


        if not queue:
            return



        queue["processing_jobs"] = max(
            0,
            queue["processing_jobs"] - 1
        )


        queue["completed_jobs"] += 1


        queue["last_job_time"] = time()



        metrics.increment(
            "queue.jobs.completed"
        )



    # ==================================================
    # Job Failed
    # ==================================================

    def job_failed(
        self,
        queue_name: str
    ):

        queue = self.queues.get(
            queue_name
        )


        if not queue:
            return



        queue["processing_jobs"] = max(
            0,
            queue["processing_jobs"] - 1
        )


        queue["failed_jobs"] += 1



        metrics.increment(
            "queue.jobs.failed"
        )



        execution_logger.warning(
            "Queue job failed",
            {
                "queue": queue_name
            }
        )



    # ==================================================
    # Backlog Detection
    # ==================================================

    def detect_backlog(
        self,
        threshold: int = 100
    ):
        """
        Detect overloaded queues.
        """


        overloaded = []


        for name, queue in (
            self.queues.items()
        ):

            if (
                queue["pending_jobs"]
                >
                threshold
            ):

                overloaded.append(
                    {
                        "queue": name,

                        "pending_jobs":
                            queue["pending_jobs"]
                    }
                )


                execution_logger.warning(
                    "Queue backlog detected",
                    {
                        "queue": name,
                        "pending_jobs":
                            queue["pending_jobs"]
                    }
                )


        return overloaded



    # ==================================================
    # Queue Health
    # ==================================================

    def get_queue_status(
        self,
        queue_name: str
    ):

        return self.queues.get(
            queue_name
        )



    # ==================================================
    # Overall Status
    # ==================================================

    def get_status(self):

        return {

            "queues":
                len(
                    self.queues
                ),

            "backlog":
                self.detect_backlog()

        }



# --------------------------------------------------
# Global Instance
# --------------------------------------------------

queue_monitor = QueueMonitor()