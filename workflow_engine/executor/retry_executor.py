from __future__ import annotations

import asyncio
import logging
from typing import Any, Awaitable, Callable

from contracts.task import Task
from contracts.result import TaskResult
from contracts.state import WorkflowState

from .task_executor import TaskExecutor


logger = logging.getLogger(__name__)


class RetryExecutor:
    """
    Adds retry behavior on top of TaskExecutor.

    Features:
    - Configurable retry count
    - Exponential backoff
    - Failure logging
    - Final failure propagation
    """

    def __init__(
        self,
        task_executor: TaskExecutor,
        max_retries: int = 3,
        base_delay: float = 1.0,
    ) -> None:
        self.task_executor = task_executor
        self.max_retries = max_retries
        self.base_delay = base_delay

    async def execute(
        self,
        task: Task,
        state: WorkflowState,
        handler: Callable[..., Awaitable[Any]],
    ) -> TaskResult:
        """
        Execute task with retries.

        Args:
            task: Task contract
            state: Workflow state
            handler: Task implementation

        Returns:
            TaskResult
        """

        last_result: TaskResult | None = None

        for attempt in range(self.max_retries + 1):

            result = await self.task_executor.execute(
                task=task,
                state=state,
                handler=handler,
            )

            if result.success:
                if attempt > 0:
                    logger.info(
                        "Task %s succeeded on retry %s",
                        task.id,
                        attempt,
                    )

                return result

            last_result = result

            if attempt >= self.max_retries:
                break

            delay = self.base_delay * (2 ** attempt)

            logger.warning(
                "Task %s failed. Retry %s/%s in %.2fs",
                task.id,
                attempt + 1,
                self.max_retries,
                delay,
            )

            await asyncio.sleep(delay)

        logger.error(
            "Task %s exhausted retries",
            task.id,
        )

        return last_result