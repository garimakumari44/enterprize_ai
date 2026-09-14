"""
Repository for execution history.

Responsible only for database access.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.execution.history.filters import HistoryFilter, SearchFilter
from app.execution.models.execution import Execution
from app.execution.models.execution_log import ExecutionLog


class HistoryRepository:
    """
    Database access layer for execution history.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Basic Retrieval
    # ------------------------------------------------------------------

    async def get_execution(
        self,
        execution_id: UUID,
    ) -> Optional[Execution]:
        """
        Retrieve a single execution.
        """

        result = await self.db.execute(
            select(Execution).where(
                Execution.id == execution_id
            )
        )

        return result.scalar_one_or_none()

    async def get_logs(
        self,
        execution_id: UUID,
    ) -> List[ExecutionLog]:
        """
        Retrieve execution logs ordered by time.
        """

        result = await self.db.execute(
            select(ExecutionLog)
            .where(
                ExecutionLog.execution_id == execution_id
            )
            .order_by(
                ExecutionLog.created_at.asc()
            )
        )

        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # History Listing
    # ------------------------------------------------------------------

    async def list_history(
        self,
        filters: HistoryFilter,
    ) -> List[Execution]:

        stmt = select(Execution)

        conditions = []

        if filters.execution_id:
            conditions.append(
                Execution.id == filters.execution_id
            )

        if filters.workflow_id:
            conditions.append(
                Execution.workflow_id == filters.workflow_id
            )

        if filters.project_id:
            conditions.append(
                Execution.project_id == filters.project_id
            )

        if filters.status:
            conditions.append(
                Execution.status == filters.status
            )

        if filters.started_after:
            conditions.append(
                Execution.started_at >= filters.started_after
            )

        if filters.started_before:
            conditions.append(
                Execution.started_at <= filters.started_before
            )

        if filters.finished_after:
            conditions.append(
                Execution.finished_at >= filters.finished_after
            )

        if filters.finished_before:
            conditions.append(
                Execution.finished_at <= filters.finished_before
            )

        if conditions:
            stmt = stmt.where(and_(*conditions))

        sort_column = getattr(
            Execution,
            filters.sort_by,
            Execution.started_at,
        )

        if filters.descending:
            stmt = stmt.order_by(sort_column.desc())
        else:
            stmt = stmt.order_by(sort_column.asc())

        stmt = stmt.offset(
            (filters.page - 1) * filters.page_size
        ).limit(filters.page_size)

        result = await self.db.execute(stmt)

        return list(result.scalars().all())

    async def count_history(
        self,
        filters: HistoryFilter,
    ) -> int:

        stmt = select(func.count()).select_from(Execution)

        conditions = []

        if filters.workflow_id:
            conditions.append(
                Execution.workflow_id == filters.workflow_id
            )

        if filters.project_id:
            conditions.append(
                Execution.project_id == filters.project_id
            )

        if filters.status:
            conditions.append(
                Execution.status == filters.status
            )

        if conditions:
            stmt = stmt.where(and_(*conditions))

        result = await self.db.execute(stmt)

        return result.scalar_one()

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    async def search(
        self,
        filters: SearchFilter,
    ) -> List[Execution]:

        stmt = (
            select(Execution)
            .outerjoin(
                ExecutionLog,
                Execution.id == ExecutionLog.execution_id,
            )
        )

        search_conditions = []

        if filters.include_logs:
            search_conditions.append(
                ExecutionLog.message.ilike(
                    f"%{filters.query}%"
                )
            )

        if filters.include_workflow_name:
            search_conditions.append(
                Execution.workflow_name.ilike(
                    f"%{filters.query}%"
                )
            )

        stmt = (
            stmt.where(or_(*search_conditions))
            .distinct()
            .offset(
                (filters.page - 1) * filters.page_size
            )
            .limit(filters.page_size)
        )

        result = await self.db.execute(stmt)

        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Deletion
    # ------------------------------------------------------------------

    async def delete_execution(
        self,
        execution_id: UUID,
    ) -> bool:
        """
        Delete an execution record.
        """

        execution = await self.get_execution(execution_id)

        if execution is None:
            return False

        await self.db.delete(execution)
        await self.db.commit()

        return True

    async def delete_older_than(
        self,
        cutoff_date,
    ) -> int:
        """
        Delete executions older than the cutoff.
        """

        result = await self.db.execute(
            select(Execution).where(
                Execution.finished_at < cutoff_date
            )
        )

        executions = result.scalars().all()

        count = len(executions)

        for execution in executions:
            await self.db.delete(execution)

        await self.db.commit()

        return count