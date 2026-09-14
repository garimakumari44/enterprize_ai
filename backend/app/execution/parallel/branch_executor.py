from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from app.execution.engine.execution_engine import ExecutionEngine
from app.execution.parallel.execution_group import (
    ExecutionGroup,
)

logger = logging.getLogger(__name__)


class BranchExecutor:
    """
    Executes a single branch inside a parallel execution.

    This class is intentionally lightweight. It delegates actual
    workflow/node execution to the ExecutionEngine while updating
    the ExecutionGroup with branch state.
    """

    def __init__(
        self,
        execution_engine: ExecutionEngine,
    ) -> None:
        self.execution_engine = execution_engine

    # ------------------------------------------------------------------ #

    async def execute(
        self,
        group: ExecutionGroup,
        branch_id: UUID,
        start_node_id: UUID,
        context: Dict[str, Any],
    ) -> Optional[Any]:
        """
        Execute one parallel branch.

        Parameters
        ----------
        group:
            Parallel execution group.

        branch_id:
            Branch identifier.

        start_node_id:
            First node of the branch.

        context:
            Runtime context shared/copied from the parent execution.

        Returns
        -------
        Any
            Branch result.
        """

        logger.info(
            "Starting parallel branch %s",
            branch_id,
        )

        group.mark_running(branch_id)

        try:
            result = await self.execution_engine.execute_from_node(
                start_node_id=start_node_id,
                context=context,
            )

            group.mark_completed(
                branch_id=branch_id,
                result=result,
            )

            logger.info(
                "Parallel branch %s completed",
                branch_id,
            )

            return result

        except Exception as exc:

            logger.exception(
                "Parallel branch %s failed",
                branch_id,
            )

            group.mark_failed(
                branch_id=branch_id,
                error=str(exc),
            )

            raise

    # ------------------------------------------------------------------ #

    async def safe_execute(
        self,
        group: ExecutionGroup,
        branch_id: UUID,
        start_node_id: UUID,
        context: Dict[str, Any],
    ) -> Optional[Any]:
        """
        Execute a branch without propagating exceptions.

        Useful when the ParallelExecutor wants all branches to
        finish before deciding how to handle failures.
        """

        try:
            return await self.execute(
                group=group,
                branch_id=branch_id,
                start_node_id=start_node_id,
                context=context,
            )

        except Exception:
            return None