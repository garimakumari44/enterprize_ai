"""
Retention policy service for execution history.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.execution.history.history_repository import HistoryRepository


class RetentionService:
    """
    Applies retention policies to execution history.
    """

    DEFAULT_RETENTION_DAYS = 90

    def __init__(self, db: AsyncSession):
        self.repository = HistoryRepository(db)

    # ---------------------------------------------------------
    # Cleanup
    # ---------------------------------------------------------

    async def cleanup(
        self,
        retention_days: int | None = None,
    ) -> Dict:
        """
        Delete executions older than the retention period.

        Returns cleanup statistics.
        """

        days = retention_days or self.DEFAULT_RETENTION_DAYS

        cutoff = datetime.utcnow() - timedelta(days=days)

        deleted = await self.repository.delete_older_than(
            cutoff
        )

        return {
            "retention_days": days,
            "cutoff_date": cutoff,
            "deleted_executions": deleted,
        }

    # ---------------------------------------------------------
    # Preview
    # ---------------------------------------------------------

    async def preview_cleanup(
        self,
        retention_days: int | None = None,
    ) -> Dict:
        """
        Preview cleanup without deleting anything.
        """

        days = retention_days or self.DEFAULT_RETENTION_DAYS

        cutoff = datetime.utcnow() - timedelta(days=days)

        executions = await self.repository.list_history(
            filters=self._history_filter(cutoff)
        )

        return {
            "retention_days": days,
            "cutoff_date": cutoff,
            "candidate_count": len(executions),
            "candidates": executions,
        }

    # ---------------------------------------------------------
    # Archive (future)
    # ---------------------------------------------------------

    async def archive(
        self,
        retention_days: int = 30,
    ) -> Dict:
        """
        Placeholder for archive support.

        Future implementation may move old executions
        to cold storage instead of deleting them.
        """

        raise NotImplementedError(
            "Execution archiving is not implemented."
        )

    # ---------------------------------------------------------
    # Policy
    # ---------------------------------------------------------

    async def apply_policy(
        self,
        retention_days: int | None = None,
    ) -> Dict:
        """
        Apply the configured retention policy.
        """

        return await self.cleanup(retention_days)

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    @staticmethod
    def _history_filter(cutoff: datetime):
        """
        Build a history filter for preview.
        """

        from app.execution.history.filters import HistoryFilter

        return HistoryFilter(
            finished_before=cutoff,
            page=1,
            page_size=1000,
        )