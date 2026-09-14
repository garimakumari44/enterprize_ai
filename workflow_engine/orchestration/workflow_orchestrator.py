

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from contracts.workflow import Workflow
from contracts.result import ExecutionResult
from contracts.state import WorkflowState

from runtime.execution_context import ExecutionContext

from executor.workflow_executor import WorkflowExecutor

logger = logging.getLogger(__name__)


class WorkflowOrchestrator:
    """
    Top-level workflow coordinator.

    Responsibilities:
    -----------------
    - Validate workflow
    - Create execution context
    - Coordinate execution
    - Handle failures
    - Return final result

    Does NOT execute nodes directly.
    Delegates execution to WorkflowExecutor.
    """

    def __init__(
        self,
        workflow_executor: WorkflowExecutor,
    ) -> None:
        self.workflow_executor = workflow_executor

    async def execute(
        self,
        workflow: Workflow,
        initial_input: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """
        Execute a workflow.

        Parameters
        ----------
        workflow:
            Workflow definition.

        initial_input:
            Runtime input payload.

        Returns
        -------
        ExecutionResult
        """

        logger.info(
            "Starting workflow execution: %s",
            workflow.id,
        )

        context = self._create_context(
            workflow,
            initial_input or {},
        )

        try:
            result = await self.workflow_executor.execute(
                workflow=workflow,
                context=context,
            )

            logger.info(
                "Workflow completed successfully: %s",
                workflow.id,
            )

            return result

        except Exception as exc:
            logger.exception(
                "Workflow failed: %s",
                workflow.id,
            )

            context.state = WorkflowState.FAILED

            return ExecutionResult.failure(
                workflow_id=workflow.id,
                error=str(exc),
            )

    def _create_context(
        self,
        workflow: Workflow,
        payload: Dict[str, Any],
    ) -> ExecutionContext:
        """
        Create execution context.
        """

        return ExecutionContext(
            workflow_id=workflow.id,
            input_data=payload,
        )