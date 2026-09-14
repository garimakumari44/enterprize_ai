from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.execution.models.execution import WorkflowExecution
from app.execution.enums.execution_status import ExecutionStatus


class WorkflowCollector:
    """
    Collects workflow execution metrics from the execution engine.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def collect(self) -> dict:
        """
        Collect current workflow execution metrics.
        """

        total_executions = await self.db.scalar(
            select(func.count(WorkflowExecution.id))
        ) or 0

        successful_executions = await self.db.scalar(
            select(func.count(WorkflowExecution.id)).where(
                WorkflowExecution.status == ExecutionStatus.SUCCESS
            )
        ) or 0

        failed_executions = await self.db.scalar(
            select(func.count(WorkflowExecution.id)).where(
                WorkflowExecution.status == ExecutionStatus.FAILED
            )
        ) or 0

        running_executions = await self.db.scalar(
            select(func.count(WorkflowExecution.id)).where(
                WorkflowExecution.status == ExecutionStatus.RUNNING
            )
        ) or 0

        average_duration = await self.db.scalar(
            select(func.avg(WorkflowExecution.duration_ms))
        ) or 0.0

        success_rate = (
            (successful_executions / total_executions) * 100
            if total_executions > 0
            else 0.0
        )

        return {
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "failed_executions": failed_executions,
            "running_executions": running_executions,
            "average_duration_ms": round(float(average_duration), 2),
            "success_rate": round(success_rate, 2),
        }