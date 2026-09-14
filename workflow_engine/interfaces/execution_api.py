# workflow_engine/interfaces/execution_api.py

from typing import Any, Dict, Optional

from contracts.dag import DAG
from contracts.result import WorkflowResult
from executor.workflow_executor import WorkflowExecutor


class ExecutionAPI:
    """
    Public execution interface for the workflow engine.
    Other platform services call this instead of directly
    accessing the executor layer.
    """

    def __init__(self, executor: WorkflowExecutor):
        self._executor = executor

    async def execute_workflow(
        self,
        workflow: DAG,
        inputs: Optional[Dict[str, Any]] = None,
    ) -> WorkflowResult:
        """
        Execute a workflow from start to finish.
        """
        return await self._executor.execute(
            workflow=workflow,
            inputs=inputs or {},
        )

    async def execute_node(
        self,
        workflow: DAG,
        node_id: str,
        inputs: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Execute a single node within a workflow.
        Useful for debugging/testing.
        """
        return await self._executor.execute_node(
            workflow=workflow,
            node_id=node_id,
            inputs=inputs or {},
        )

    async def resume_workflow(
        self,
        execution_id: str,
    ) -> WorkflowResult:
        """
        Resume a paused workflow.
        """
        return await self._executor.resume(
            execution_id=execution_id
        )

    async def cancel_workflow(
        self,
        execution_id: str,
    ) -> bool:
        """
        Cancel a running workflow.
        """
        return await self._executor.cancel(
            execution_id=execution_id
        )

    async def retry_workflow(
        self,
        execution_id: str,
    ) -> WorkflowResult:
        """
        Retry a failed workflow execution.
        """
        return await self._executor.retry(
            execution_id=execution_id
        )

    async def get_execution_status(
        self,
        execution_id: str,
    ) -> Dict[str, Any]:
        """
        Retrieve workflow execution status.
        """
        return await self._executor.status(
            execution_id=execution_id
        )