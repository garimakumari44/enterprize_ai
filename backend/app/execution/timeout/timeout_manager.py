import logging
from datetime import datetime
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.execution.timeout.workflow_timeout import WorkflowTimeout
from app.execution.timeout.node_timeout import NodeTimeout

from app.execution.repositories.execution_repository import (
    ExecutionRepository,
)

from app.execution.services.execution_service import (
    ExecutionService,
)

logger = logging.getLogger(__name__)


class TimeoutManager:
    """
    Central timeout coordinator.

    Responsible for detecting workflow and node
    timeouts and delegating cancellation to the
    ExecutionService.
    """

    def __init__(
        self,
        db: AsyncSession,
        execution_repository: ExecutionRepository,
        execution_service: ExecutionService,
    ):
        self.db = db
        self.execution_repository = execution_repository
        self.execution_service = execution_service

    async def check_workflow_timeouts(self) -> int:
        """
        Scan running workflows and cancel those
        exceeding their timeout.

        Returns:
            Number of cancelled executions.
        """

        cancelled = 0

        executions = (
            await self.execution_repository.get_running_executions()
        )

        now = datetime.utcnow()

        for execution in executions:

            timeout_seconds = getattr(
                execution,
                "timeout_seconds",
                3600,
            )

            timeout = WorkflowTimeout(timeout_seconds)

            if timeout.has_timed_out(
                execution.started_at,
                now,
            ):
                logger.warning(
                    "Workflow %s timed out.",
                    execution.id,
                )

                await self.execution_service.cancel_execution(
                    execution.id,
                    reason="Workflow timeout",
                )

                cancelled += 1

        return cancelled

    async def check_node_timeouts(self) -> int:
        """
        Scan running nodes and cancel those
        exceeding their timeout.

        Returns:
            Number of cancelled node executions.
        """

        cancelled = 0

        running_nodes = (
            await self.execution_repository.get_running_nodes()
        )

        now = datetime.utcnow()

        for node in running_nodes:

            timeout_seconds = getattr(
                node,
                "timeout_seconds",
                300,
            )

            timeout = NodeTimeout(timeout_seconds)

            if timeout.has_timed_out(
                node.started_at,
                now,
            ):
                logger.warning(
                    "Node %s timed out.",
                    node.id,
                )

                await self.execution_service.cancel_execution(
                    node.execution_id,
                    reason=f"Node '{node.node_name}' timeout",
                )

                cancelled += 1

        return cancelled

    async def check_all(self) -> None:
        """
        Run every timeout check.
        """

        await self.check_workflow_timeouts()
        await self.check_node_timeouts()