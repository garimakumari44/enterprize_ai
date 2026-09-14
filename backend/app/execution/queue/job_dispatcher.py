"""
Job Dispatcher.

Responsible for routing workflow execution jobs
to appropriate queues.
"""

from __future__ import annotations

from typing import Any

from app.execution.queue.queue_manager import QueueManager


class JobDispatcher:
    """
    Dispatch execution jobs to queues.

    Used by:
        - Execution Service
        - Scheduler
        - Retry Manager
    """

    DEFAULT_QUEUE = "workflow_execution"

    PRIORITY_QUEUE = "priority_execution"

    SCHEDULE_QUEUE = "scheduled_execution"


    def __init__(
        self,
        queue_manager: QueueManager | None = None,
    ) -> None:

        self.queue_manager = (
            queue_manager
            or QueueManager()
        )


    def dispatch(
        self,
        payload: str,
        priority: str = "normal",
        scheduled: bool = False,
    ) -> int:
        """
        Send job to correct queue.

        Args:

            payload:
                Serialized execution job.

            priority:
                normal | high

            scheduled:
                Scheduler generated job.

        Returns:
            Queue size.
        """

        queue_name = self._resolve_queue(
            priority=priority,
            scheduled=scheduled,
        )


        return self.queue_manager.enqueue(
            payload=payload,
            queue_name=queue_name,
        )


    def _resolve_queue(
        self,
        priority: str,
        scheduled: bool,
    ) -> str:
        """
        Decide queue destination.
        """

        if scheduled:
            return self.SCHEDULE_QUEUE


        if priority == "high":
            return self.PRIORITY_QUEUE


        return self.DEFAULT_QUEUE


    def dispatch_retry(
        self,
        payload: str,
    ) -> int:
        """
        Dispatch failed execution back
        into execution queue.
        """

        return self.queue_manager.retry_job(
            payload=payload,
            queue_name=self.DEFAULT_QUEUE,
        )


    def get_queue_for_job(
        self,
        priority: str,
        scheduled: bool,
    ) -> str:
        """
        Public queue resolution method.
        Useful for testing.
        """

        return self._resolve_queue(
            priority=priority,
            scheduled=scheduled,
        )