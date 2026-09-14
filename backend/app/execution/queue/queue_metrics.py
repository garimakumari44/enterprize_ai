"""
Queue Metrics.

Provides monitoring information
about Redis workflow queues.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict

from app.execution.queue.broker import Broker


class QueueMetrics:
    """
    Collects queue statistics.

    Used by:
        - Monitoring Service
        - Dashboard APIs
        - Worker Monitoring
    """


    DEFAULT_QUEUES = [
        "workflow_execution",
        "priority_execution",
        "scheduled_execution",
    ]


    def __init__(
        self,
        broker: Broker | None = None,
    ) -> None:

        self.broker = broker or Broker()



    def get_queue_size(
        self,
        queue_name: str,
    ) -> int:
        """
        Return number of waiting jobs.
        """

        return self.broker.size(queue_name)



    def get_queue_status(
        self,
        queue_name: str,
    ) -> Dict:
        """
        Return queue health information.
        """

        exists = self.broker.exists(
            queue_name
        )

        size = self.broker.size(
            queue_name
        )


        return {
            "queue": queue_name,
            "exists": exists,
            "pending_jobs": size,
            "checked_at": self._timestamp(),
        }



    def get_all_metrics(self) -> Dict:
        """
        Return metrics for all queues.
        """

        metrics = {}

        for queue in self.DEFAULT_QUEUES:

            metrics[queue] = (
                self.get_queue_status(queue)
            )


        return {
            "queues": metrics,
            "timestamp": self._timestamp(),
        }



    def is_healthy(
        self,
    ) -> bool:
        """
        Check queue system health.
        """

        try:

            return self.broker.ping()

        except Exception:

            return False



    def _timestamp(self) -> str:
        """
        UTC timestamp.
        """

        return datetime.now(
            timezone.utc
        ).isoformat()