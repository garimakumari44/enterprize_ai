from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List
from uuid import UUID, uuid4

from app.execution.parallel.branch_executor import BranchExecutor
from app.execution.parallel.execution_group import (
    BranchExecution,
    ExecutionGroup,
)

logger = logging.getLogger(__name__)


class ParallelExecutor:
    """
    Coordinates execution of multiple workflow branches concurrently.

    Flow:

        Parallel Node
            │
      ┌─────┼─────┐
      ▼     ▼     ▼
    Branch Branch Branch
      │      │      │
      ▼      ▼      ▼
      Task   Task   Task
       └─────┼─────┘
             ▼
        ExecutionGroup
    """

    def __init__(
        self,
        branch_executor: BranchExecutor,
    ) -> None:
        self.branch_executor = branch_executor

    # ------------------------------------------------------------------ #

    async def execute(
        self,
        workflow_execution_id: UUID,
        branches: List[UUID],
        context: Dict[str, Any],
    ) -> ExecutionGroup:
        """
        Execute all branches in parallel.

        Parameters
        ----------
        workflow_execution_id:
            Current workflow execution.

        branches:
            List of start node IDs.

        context:
            Parent execution context.

        Returns
        -------
        ExecutionGroup
        """

        logger.info(
            "Starting parallel execution (%d branches)",
            len(branches),
        )

        group = ExecutionGroup(
            workflow_execution_id=workflow_execution_id
        )

        tasks = []

        for node_id in branches:

            branch = BranchExecution(
                branch_id=uuid4(),
                start_node_id=node_id,
            )

            group.add_branch(branch)

            # Each branch gets its own copy of the runtime context.
            branch_context = dict(context)

            task = asyncio.create_task(
                self.branch_executor.safe_execute(
                    group=group,
                    branch_id=branch.branch_id,
                    start_node_id=node_id,
                    context=branch_context,
                )
            )

            tasks.append(task)

        await asyncio.gather(*tasks)

        logger.info(
            "Parallel execution finished "
            "(completed=%d failed=%d)",
            group.completed_count,
            group.failed_count,
        )

        return group

    # ------------------------------------------------------------------ #

    async def execute_or_raise(
        self,
        workflow_execution_id: UUID,
        branches: List[UUID],
        context: Dict[str, Any],
    ) -> ExecutionGroup:
        """
        Execute all branches and raise if any failed.
        """

        group = await self.execute(
            workflow_execution_id=workflow_execution_id,
            branches=branches,
            context=context,
        )

        if group.has_failures:

            raise RuntimeError(
                f"{group.failed_count} parallel branch(es) failed."
            )

        return group

    # ------------------------------------------------------------------ #

    async def execute_with_limit(
        self,
        workflow_execution_id: UUID,
        branches: List[UUID],
        context: Dict[str, Any],
        max_concurrency: int,
    ) -> ExecutionGroup:
        """
        Execute branches while limiting concurrent execution.
        """

        semaphore = asyncio.Semaphore(max_concurrency)

        group = ExecutionGroup(
            workflow_execution_id=workflow_execution_id
        )

        async def runner(
            branch: BranchExecution,
            branch_context: Dict[str, Any],
        ) -> None:

            async with semaphore:

                await self.branch_executor.safe_execute(
                    group=group,
                    branch_id=branch.branch_id,
                    start_node_id=branch.start_node_id,
                    context=branch_context,
                )

        tasks = []

        for node_id in branches:

            branch = BranchExecution(
                branch_id=uuid4(),
                start_node_id=node_id,
            )

            group.add_branch(branch)

            tasks.append(
                asyncio.create_task(
                    runner(
                        branch,
                        dict(context),
                    )
                )
            )

        await asyncio.gather(*tasks)

        return group