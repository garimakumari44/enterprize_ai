# interfaces/workflow_api.py

from typing import Dict, Any, Optional
from uuid import uuid4

from contracts.workflow import Workflow
from contracts.result import WorkflowResult
from orchestration.workflow_orchestrator import WorkflowOrchestrator


class WorkflowAPI:
    """
    Public interface for interacting with the Workflow Engine.

    Used by:
    - API Gateway
    - Agent Runtime
    - Scheduler
    - External services
    """

    def __init__(self, orchestrator: WorkflowOrchestrator):
        self.orchestrator = orchestrator

    async def execute_workflow(
        self,
        workflow: Workflow,
        inputs: Dict[str, Any],
    ) -> WorkflowResult:
        """
        Execute a workflow immediately.
        """

        execution_id = str(uuid4())

        return await self.orchestrator.execute(
            workflow=workflow,
            execution_id=execution_id,
            inputs=inputs,
        )

    async def schedule_workflow(
        self,
        workflow: Workflow,
        inputs: Dict[str, Any],
        schedule_time: str,
    ) -> Dict[str, Any]:
        """
        Schedule workflow execution.
        """

        execution_id = str(uuid4())

        return {
            "execution_id": execution_id,
            "workflow_id": workflow.id,
            "schedule_time": schedule_time,
            "status": "scheduled",
        }

    async def get_execution_status(
        self,
        execution_id: str,
    ) -> Dict[str, Any]:
        """
        Fetch workflow execution status.
        """

        return await self.orchestrator.get_execution_status(
            execution_id
        )

    async def cancel_execution(
        self,
        execution_id: str,
    ) -> bool:
        """
        Cancel a running workflow.
        """

        return await self.orchestrator.cancel_execution(
            execution_id
        )

    async def retry_execution(
        self,
        execution_id: str,
    ) -> WorkflowResult:
        """
        Retry a failed workflow.
        """

        return await self.orchestrator.retry_execution(
            execution_id
        )

    async def list_active_executions(
        self,
    ) -> Dict[str, Any]:
        """
        Return currently running workflows.
        """

        return await self.orchestrator.list_active_executions()