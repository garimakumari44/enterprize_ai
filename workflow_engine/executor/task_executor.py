from __future__ import annotations

import logging
import time
from typing import Any, Callable, Dict

from contracts.task import Task
from contracts.result import TaskResult
from contracts.state import WorkflowState


logger = logging.getLogger(__name__)


class TaskExecutor:
    """
    Executes an individual task.

    Responsibilities:
    - Run task implementation
    - Capture execution metadata
    - Handle exceptions
    - Update workflow state
    - Return TaskResult
    """

    def __init__(self) -> None:
        pass

    async def execute(
        self,
        task: Task,
        state: WorkflowState,
        handler: Callable[..., Any],
    ) -> TaskResult:
        """
        Execute a task handler.

        Args:
            task: Task contract
            state: Current workflow state
            handler: Function implementing task logic

        Returns:
            TaskResult
        """

        start_time = time.time()

        try:
            logger.info(
                f"Starting task {task.id} ({task.name})"
            )

            output = await handler(
                task=task,
                state=state,
            )

            duration = time.time() - start_time

            result = TaskResult(
                task_id=task.id,
                success=True,
                output=output,
                error=None,
                duration=duration,
            )

            state.set(task.id, output)

            logger.info(
                f"Task {task.id} completed in "
                f"{duration:.2f}s"
            )

            return result

        except Exception as e:
            duration = time.time() - start_time

            logger.exception(
                f"Task {task.id} failed"
            )

            return TaskResult(
                task_id=task.id,
                success=False,
                output=None,
                error=str(e),
                duration=duration,
            )