"""
Execution Service.

Handles workflow execution lifecycle.
"""

from typing import Any, Dict, Optional

from app.execution.engine.execution_engine import ExecutionEngine
from app.execution.repositories.execution_repository  import ExecutionRepository
from app.repositories.workflow.workflow_repository import WorkflowRepository


class ExecutionService:
    """
    Service for workflow executions.
    """

    def __init__(
        self,
        execution_repository: ExecutionRepository,
        workflow_repository: WorkflowRepository,
    ) -> None:
        self.execution_repository = execution_repository
        self.workflow_repository = workflow_repository
        self.engine = ExecutionEngine()

    def run_workflow(
        self,
        workflow_id: str,
        inputs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a workflow.

        Args:
            workflow_id: Workflow ID.
            inputs: Initial execution inputs.

        Returns:
            Execution result.
        """

        workflow = self.workflow_repository.get_by_id(workflow_id)

        if workflow is None:
            raise ValueError("Workflow not found.")

        execution = self.execution_repository.create(
            workflow_id=workflow_id,
            status="RUNNING",
            inputs=inputs or {},
        )

        try:

            result = self.engine.execute(
                workflow=workflow.definition,
                inputs=inputs,
            )

            self.execution_repository.update(
                execution.id,
                status="COMPLETED",
                outputs=result.get("outputs", {}),
            )

            return {
                "execution_id": execution.id,
                **result,
            }

        except Exception as exc:

            self.execution_repository.update(
                execution.id,
                status="FAILED",
                error=str(exc),
            )

            raise

    def get_execution(
        self,
        execution_id: str,
    ):
        """
        Retrieve execution details.
        """

        return self.execution_repository.get_by_id(execution_id)

    def list_executions(
        self,
        workflow_id: Optional[str] = None,
    ):
        """
        List executions.

        If workflow_id is supplied, return only
        executions for that workflow.
        """

        if workflow_id:
            return self.execution_repository.list_by_workflow(workflow_id)

        return self.execution_repository.list()

    def cancel_execution(
        self,
        execution_id: str,
    ):
        """
        Mark an execution as cancelled.
        """

        return self.execution_repository.update(
            execution_id,
            status="CANCELLED",
        )