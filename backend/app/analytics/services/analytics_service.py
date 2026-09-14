from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.repositories.analytics_repository import AnalyticsRepository


class AnalyticsService:
    """
    High-level analytics aggregation service.

    This service combines metrics from multiple repositories
    and prepares dashboard-ready responses.
    """

    def __init__(self, db: AsyncSession):
        self.repository = AnalyticsRepository(db)

    async def dashboard_summary(self) -> dict[str, Any]:
        """
        Returns overall analytics dashboard.
        """

        workflow_metrics = await self.repository.get_latest_workflow_metrics()
        usage_metrics = await self.repository.get_latest_usage_metrics()
        user_metrics = await self.repository.get_latest_user_metrics()

        return {
            "workflow": workflow_metrics,
            "usage": usage_metrics,
            "users": user_metrics,
            "generated_at": datetime.utcnow(),
        }

    async def workflow_statistics(self) -> dict[str, Any]:
        metrics = await self.repository.get_latest_workflow_metrics()

        return {
            "executions": metrics.total_executions,
            "success_rate": metrics.success_rate,
            "average_duration": metrics.average_duration_ms,
            "failed": metrics.failed_executions,
            "running": metrics.running_executions,
        }

    async def usage_statistics(self) -> dict[str, Any]:
        metrics = await self.repository.get_latest_usage_metrics()

        return {
            "api_calls": metrics.api_calls,
            "tokens_used": metrics.tokens_used,
            "storage_used_gb": metrics.storage_used_gb,
            "bandwidth_gb": metrics.bandwidth_gb,
        }

    async def user_statistics(self) -> dict[str, Any]:
        metrics = await self.repository.get_latest_user_metrics()

        return {
            "active_users": metrics.active_users,
            "new_users": metrics.new_users,
            "organizations": metrics.organizations,
            "projects": metrics.projects,
        }

    async def analytics_overview(self) -> dict[str, Any]:
        """
        Returns everything required by the Analytics Dashboard.
        """

        return {
            "workflow": await self.workflow_statistics(),
            "usage": await self.usage_statistics(),
            "users": await self.user_statistics(),
            "generated_at": datetime.utcnow(),
        }

    async def metrics_between(
        self,
        start: datetime,
        end: datetime,
    ):
        """
        Historical metrics.
        """

        return await self.repository.get_metrics_between(start, end)

    async def last_30_days(self):
        end = datetime.utcnow()
        start = end - timedelta(days=30)

        return await self.metrics_between(start, end)