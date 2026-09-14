"""
Metrics Service.

Business-level metrics for workflow execution.

Used by:
- Execution Engine
- Workers
- Queue
- Monitoring
"""

from time import time
from typing import Dict

from app.execution.monitoring.metrics import metrics
from app.execution.monitoring.logger import execution_logger


class MetricsService:
    """
    High-level metrics service.

    Converts execution events into metrics.
    """


    def __init__(self):

        # Active execution start timestamps

        self.execution_start_times: Dict[str, float] = {}


    # ==================================================
    # Workflow Execution Metrics
    # ==================================================

    def execution_started(
        self,
        execution_id: str,
        workflow_id: str
    ):
        """
        Record workflow start.
        """

        self.execution_start_times[
            execution_id
        ] = time()


        metrics.increment(
            "executions.started"
        )


        metrics.increment(
            "executions.running"
        )


        execution_logger.info(
            "Execution started",
            {
                "execution_id": execution_id,
                "workflow_id": workflow_id
            }
        )



    def execution_completed(
        self,
        execution_id: str,
        workflow_id: str
    ):
        """
        Record successful execution.
        """

        duration = self._get_duration(
            execution_id
        )


        metrics.increment(
            "executions.completed"
        )


        metrics.decrement(
            "executions.running"
        )


        metrics.record_time(
            "execution.duration",
            duration
        )


        execution_logger.info(
            "Execution completed",
            {
                "execution_id": execution_id,
                "workflow_id": workflow_id,
                "duration": duration
            }
        )



    def execution_failed(
        self,
        execution_id: str,
        workflow_id: str,
        error: str
    ):
        """
        Record failed execution.
        """

        duration = self._get_duration(
            execution_id
        )


        metrics.increment(
            "executions.failed"
        )


        metrics.decrement(
            "executions.running"
        )


        metrics.record_time(
            "execution.failed.duration",
            duration
        )


        execution_logger.error(
            "Execution failed",
            {
                "execution_id": execution_id,
                "workflow_id": workflow_id,
                "duration": duration,
                "error": error
            }
        )



    # ==================================================
    # Node Metrics
    # ==================================================

    def node_started(
        self,
        node_id: str,
        node_type: str
    ):

        metrics.increment(
            "nodes.started"
        )


        execution_logger.info(
            "Node started",
            {
                "node_id": node_id,
                "node_type": node_type
            }
        )



    def node_completed(
        self,
        node_id: str,
        node_type: str
    ):

        metrics.increment(
            "nodes.completed"
        )


        execution_logger.info(
            "Node completed",
            {
                "node_id": node_id,
                "node_type": node_type
            }
        )



    def node_failed(
        self,
        node_id: str,
        node_type: str,
        error: str
    ):

        metrics.increment(
            "nodes.failed"
        )


        execution_logger.error(
            "Node failed",
            {
                "node_id": node_id,
                "node_type": node_type,
                "error": error
            }
        )



    # ==================================================
    # Retry Metrics
    # ==================================================

    def retry_attempted(
        self,
        execution_id: str
    ):

        metrics.increment(
            "executions.retry"
        )


        execution_logger.warning(
            "Execution retry",
            {
                "execution_id": execution_id
            }
        )



    # ==================================================
    # Statistics
    # ==================================================

    def get_execution_statistics(self):

        snapshot = metrics.snapshot()


        return {

            "started":
                snapshot["counters"].get(
                    "executions.started",
                    0
                ),

            "completed":
                snapshot["counters"].get(
                    "executions.completed",
                    0
                ),

            "failed":
                snapshot["counters"].get(
                    "executions.failed",
                    0
                ),

            "running":
                snapshot["gauges"].get(
                    "executions.running",
                    0
                )
        }



    # ==================================================
    # Internal
    # ==================================================

    def _get_duration(
        self,
        execution_id: str
    ) -> float:
        """
        Calculate execution duration.
        """

        started = self.execution_start_times.pop(
            execution_id,
            None
        )


        if not started:
            return 0


        return round(
            time() - started,
            4
        )



# ------------------------------------------------------
# Global Instance
# ------------------------------------------------------

metrics_service = MetricsService()