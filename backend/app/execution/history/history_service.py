"""
Business logic for execution history.
"""

from __future__ import annotations

from typing import Dict, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.execution.exceptions.execution_exception import ExecutionException
from app.execution.history.filters import HistoryFilter, SearchFilter
from app.execution.history.history_repository import HistoryRepository
from app.execution.models.execution import Execution
from app.execution.models.execution_log import ExecutionLog


class HistoryService:
    """
    Business service for execution history.
    """

    def __init__(self, db: AsyncSession):
        self.repository = HistoryRepository(db)

    # ------------------------------------------------------------------
    # Execution Details
    # ------------------------------------------------------------------

    async def get_execution(
        self,
        execution_id: UUID,
    ) -> Execution:
        """
        Return a single execution.
        """

        execution = await self.repository.get_execution(
            execution_id
        )

        if execution is None:
            raise ExecutionException(
                f"Execution '{execution_id}' not found."
            )

        return execution

    async def get_execution_logs(
        self,
        execution_id: UUID,
    ) -> List[ExecutionLog]:
        """
        Return execution logs.
        """

        await self.get_execution(execution_id)

        return await self.repository.get_logs(
            execution_id
        )

    async def get_execution_details(
        self,
        execution_id: UUID,
    ) -> Dict:
        """
        Returns execution and logs.
        """

        execution = await self.get_execution(
            execution_id
        )

        logs = await self.repository.get_logs(
            execution_id
        )

        return {
            "execution": execution,
            "logs": logs,
            "log_count": len(logs),
        }

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------

    async def list_history(
        self,
        filters: HistoryFilter,
    ) -> Dict:
        """
        Paginated execution history.
        """

        items = await self.repository.list_history(
            filters
        )

        total = await self.repository.count_history(
            filters
        )

        pages = (
            total + filters.page_size - 1
        ) // filters.page_size

        return {
            "items": items,
            "total": total,
            "page": filters.page,
            "page_size": filters.page_size,
            "pages": pages,
        }

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    async def search(
        self,
        filters: SearchFilter,
    ) -> List[Execution]:
        """
        Search execution history.
        """

        if not filters.query.strip():
            return []

        return await self.repository.search(
            filters
        )

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    async def history_summary(
        self,
        filters: HistoryFilter,
    ) -> Dict:
        """
        Summary statistics.
        """

        executions = await self.repository.list_history(
            filters
        )

        succeeded = sum(
            1
            for e in executions
            if e.status == "SUCCEEDED"
        )

        failed = sum(
            1
            for e in executions
            if e.status == "FAILED"
        )

        running = sum(
            1
            for e in executions
            if e.status == "RUNNING"
        )

        cancelled = sum(
            1
            for e in executions
            if e.status == "CANCELLED"
        )

        return {
            "total": len(executions),
            "succeeded": succeeded,
            "failed": failed,
            "running": running,
            "cancelled": cancelled,
        }

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    async def delete_execution(
        self,
        execution_id: UUID,
    ) -> None:
        """
        Delete an execution.
        """

        deleted = await self.repository.delete_execution(
            execution_id
        )

        if not deleted:
            raise ExecutionException(
                f"Execution '{execution_id}' not found."
            )