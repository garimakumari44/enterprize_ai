"""
Worker Monitor.

Monitors execution worker health.

Responsibilities:
- Worker registration
- Heartbeat tracking
- Worker status
- Dead worker detection
- Worker statistics
"""

from time import time
from typing import Dict


from app.execution.monitoring.logger import (
    execution_logger
)

from app.execution.monitoring.metrics import (
    metrics
)



class WorkerMonitor:
    """
    Worker health monitoring service.
    """


    def __init__(self):

        # Worker registry

        self.workers: Dict[str, dict] = {}



    # ==================================================
    # Worker Registration
    # ==================================================

    def register_worker(
        self,
        worker_id: str,
        worker_type: str = "execution"
    ):
        """
        Register new worker.
        """


        self.workers[worker_id] = {

            "worker_id": worker_id,

            "worker_type": worker_type,

            "status": "ONLINE",

            "started_at": time(),

            "last_heartbeat": time(),

            "jobs_processed": 0,

            "failures": 0
        }


        metrics.increment(
            "workers.registered"
        )


        execution_logger.info(
            "Worker registered",
            {
                "worker_id": worker_id,
                "worker_type": worker_type
            }
        )



    # ==================================================
    # Heartbeat
    # ==================================================

    def heartbeat(
        self,
        worker_id: str
    ):
        """
        Update worker heartbeat.
        """


        worker = self.workers.get(
            worker_id
        )


        if not worker:
            return False



        worker["last_heartbeat"] = time()

        worker["status"] = "ONLINE"



        execution_logger.info(
            "Worker heartbeat",
            {
                "worker_id": worker_id
            }
        )


        return True



    # ==================================================
    # Job Started
    # ==================================================

    def job_started(
        self,
        worker_id: str
    ):

        worker = self.workers.get(
            worker_id
        )


        if worker:

            worker["active_jobs"] = (
                worker.get(
                    "active_jobs",
                    0
                )
                +
                1
            )



    # ==================================================
    # Job Completed
    # ==================================================

    def job_completed(
        self,
        worker_id: str
    ):

        worker = self.workers.get(
            worker_id
        )


        if worker:

            worker["active_jobs"] = max(
                0,
                worker.get(
                    "active_jobs",
                    1
                )
                -
                1
            )


            worker["jobs_processed"] += 1



            metrics.increment(
                "workers.jobs.completed"
            )



    # ==================================================
    # Job Failed
    # ==================================================

    def job_failed(
        self,
        worker_id: str
    ):

        worker = self.workers.get(
            worker_id
        )


        if worker:

            worker["failures"] += 1



        metrics.increment(
            "workers.jobs.failed"
        )



    # ==================================================
    # Dead Worker Detection
    # ==================================================

    def detect_dead_workers(
        self,
        timeout_seconds: int = 60
    ):
        """
        Find workers without heartbeat.
        """


        dead_workers = []


        current_time = time()



        for worker_id, worker in (
            self.workers.items()
        ):

            heartbeat_age = (
                current_time
                -
                worker["last_heartbeat"]
            )



            if heartbeat_age > timeout_seconds:

                worker["status"] = "OFFLINE"


                dead_workers.append(
                    worker_id
                )


                execution_logger.warning(
                    "Worker heartbeat timeout",
                    {
                        "worker_id": worker_id,
                        "last_seen_seconds":
                            heartbeat_age
                    }
                )


        return dead_workers



    # ==================================================
    # Worker Status
    # ==================================================

    def get_worker(
        self,
        worker_id: str
    ):

        return self.workers.get(
            worker_id
        )



    # ==================================================
    # Health Summary
    # ==================================================

    def get_status(self):

        return {

            "total_workers":
                len(
                    self.workers
                ),


            "online_workers":
                len(
                    [
                        w
                        for w in self.workers.values()
                        if w["status"]
                        == "ONLINE"
                    ]
                ),


            "offline_workers":
                self.detect_dead_workers()

        }



# --------------------------------------------------
# Global Instance
# --------------------------------------------------

worker_monitor = WorkerMonitor()