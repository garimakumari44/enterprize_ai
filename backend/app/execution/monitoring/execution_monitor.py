"""
Execution Monitor.

Monitors workflow execution health.

Responsibilities:
- Detect execution failures
- Detect slow executions
- Track running executions
- Generate monitoring events
"""

from time import time
from typing import Dict, List


from app.execution.monitoring.metrics_service import (
    metrics_service
)

from app.execution.monitoring.logger import (
    execution_logger
)



class ExecutionMonitor:
    """
    Workflow execution monitoring service.
    """


    def __init__(self):

        # Active executions

        self.running_executions: Dict[str, dict] = {}



    # ==================================================
    # Register Execution
    # ==================================================

    def register_execution(
        self,
        execution_id: str,
        workflow_id: str
    ):
        """
        Register running execution.
        """


        self.running_executions[
            execution_id
        ] = {

            "workflow_id": workflow_id,

            "started_at": time(),

            "status": "RUNNING"
        }



        execution_logger.info(
            "Execution registered",
            {
                "execution_id": execution_id,
                "workflow_id": workflow_id
            }
        )



    # ==================================================
    # Mark Completion
    # ==================================================

    def mark_completed(
        self,
        execution_id: str
    ):
        """
        Remove completed execution.
        """


        execution = self.running_executions.get(
            execution_id
        )


        if execution:

            execution["status"] = "COMPLETED"

            del self.running_executions[
                execution_id
            ]



    # ==================================================
    # Mark Failed
    # ==================================================

    def mark_failed(
        self,
        execution_id: str,
        error: str
    ):

        execution = self.running_executions.get(
            execution_id
        )


        if execution:

            execution["status"] = "FAILED"


        execution_logger.error(
            "Execution failure detected",
            {
                "execution_id": execution_id,
                "error": error
            }
        )



    # ==================================================
    # Detect Long Running Executions
    # ==================================================

    def detect_long_running(
        self,
        threshold_seconds: int = 300
    ) -> List[dict]:
        """
        Find executions running longer
        than allowed threshold.
        """


        long_running = []


        current_time = time()


        for execution_id, execution in (
            self.running_executions.items()
        ):

            duration = (
                current_time
                -
                execution["started_at"]
            )


            if duration > threshold_seconds:

                long_running.append(
                    {
                        "execution_id": execution_id,

                        "workflow_id":
                            execution["workflow_id"],

                        "duration":
                            round(duration, 2)
                    }
                )


        return long_running



    # ==================================================
    # Failure Rate Monitoring
    # ==================================================

    def check_failure_rate(
        self,
        limit: float = 0.2
    ):
        """
        Check if failure percentage
        is too high.
        """


        stats = (
            metrics_service
            .get_execution_statistics()
        )


        total = (
            stats["completed"]
            +
            stats["failed"]
        )


        if total == 0:
            return False



        failure_rate = (
            stats["failed"]
            /
            total
        )


        if failure_rate >= limit:

            execution_logger.warning(
                "High execution failure rate",
                {
                    "failure_rate":
                        failure_rate
                }
            )

            return True


        return False



    # ==================================================
    # Health Summary
    # ==================================================

    def get_status(self):

        return {

            "running_executions":
                len(
                    self.running_executions
                ),


            "long_running":
                self.detect_long_running(),


            "failure_rate_warning":
                self.check_failure_rate()

        }



# --------------------------------------------------
# Global Instance
# --------------------------------------------------

execution_monitor = ExecutionMonitor()