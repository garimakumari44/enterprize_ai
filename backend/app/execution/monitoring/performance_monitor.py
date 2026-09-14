"""
Performance Monitor.

Tracks workflow execution performance.

Responsibilities:
- Execution latency
- Node performance
- Worker throughput
- Queue delays
- Bottleneck detection
"""

from time import time
from typing import Dict, List


from app.execution.monitoring.metrics import (
    metrics
)

from app.execution.monitoring.logger import (
    execution_logger
)



class PerformanceMonitor:
    """
    Workflow runtime performance analyzer.
    """


    def __init__(self):

        # execution_id -> start timestamp

        self.execution_times: Dict[str, float] = {}


        # node_id -> start timestamp

        self.node_times: Dict[str, float] = {}


        # Worker throughput

        self.worker_stats: Dict[str, dict] = {}



    # ==================================================
    # Execution Performance
    # ==================================================

    def start_execution_timer(
        self,
        execution_id: str
    ):
        """
        Start execution timer.
        """


        self.execution_times[
            execution_id
        ] = time()



    def finish_execution_timer(
        self,
        execution_id: str
    ):
        """
        Finish execution timer.
        Returns duration.
        """


        started = self.execution_times.pop(
            execution_id,
            None
        )


        if not started:
            return 0



        duration = round(
            time() - started,
            4
        )


        metrics.record_time(
            "performance.execution.duration",
            duration
        )


        return duration



    # ==================================================
    # Node Performance
    # ==================================================

    def start_node_timer(
        self,
        node_id: str
    ):
        """
        Start node execution timer.
        """


        self.node_times[node_id] = time()



    def finish_node_timer(
        self,
        node_id: str
    ):
        """
        Calculate node execution duration.
        """


        started = self.node_times.pop(
            node_id,
            None
        )


        if not started:
            return 0



        duration = round(
            time() - started,
            4
        )


        metrics.record_time(
            "performance.node.duration",
            duration
        )


        return duration



    # ==================================================
    # Worker Throughput
    # ==================================================

    def register_worker(
        self,
        worker_id: str
    ):
        """
        Add worker tracking.
        """


        self.worker_stats[
            worker_id
        ] = {

            "jobs_completed": 0,

            "started_at": time()
        }



    def job_completed(
        self,
        worker_id: str
    ):
        """
        Track worker throughput.
        """


        worker = self.worker_stats.get(
            worker_id
        )


        if worker:

            worker[
                "jobs_completed"
            ] += 1



    def get_worker_throughput(
        self,
        worker_id: str
    ):

        worker = self.worker_stats.get(
            worker_id
        )


        if not worker:
            return 0



        runtime = (
            time()
            -
            worker["started_at"]
        )


        if runtime == 0:
            return 0



        return round(
            worker["jobs_completed"]
            /
            runtime,
            4
        )



    # ==================================================
    # Queue Wait Time
    # ==================================================

    def record_queue_wait(
        self,
        wait_time: float
    ):
        """
        Record time job waited in queue.
        """


        metrics.record_time(
            "performance.queue.wait",
            wait_time
        )



    # ==================================================
    # Slow Operation Detection
    # ==================================================

    def detect_slow_execution(
        self,
        threshold_seconds: int = 60
    ) -> List[dict]:
        """
        Detect running executions
        exceeding threshold.
        """


        slow = []


        current = time()


        for execution_id, started in (
            self.execution_times.items()
        ):

            duration = (
                current - started
            )


            if duration > threshold_seconds:

                slow.append(
                    {
                        "execution_id":
                            execution_id,

                        "duration":
                            round(
                                duration,
                                2
                            )
                    }
                )


        if slow:

            execution_logger.warning(
                "Slow executions detected",
                {
                    "count": len(slow)
                }
            )


        return slow



    # ==================================================
    # Performance Summary
    # ==================================================

    def get_summary(self):

        snapshot = metrics.snapshot()


        return {

            "execution_duration":
                snapshot["timings"].get(
                    "performance.execution.duration",
                    {}
                ),


            "node_duration":
                snapshot["timings"].get(
                    "performance.node.duration",
                    {}
                ),


            "queue_wait":
                snapshot["timings"].get(
                    "performance.queue.wait",
                    {}
                ),

            "slow_executions":
                self.detect_slow_execution()

        }



# --------------------------------------------------
# Global Instance
# --------------------------------------------------

performance_monitor = PerformanceMonitor()