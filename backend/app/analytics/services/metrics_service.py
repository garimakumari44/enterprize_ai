from __future__ import annotations

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.repositories.analytics_repository import AnalyticsRepository
from app.analytics.models.workflow_metric import WorkflowMetric
from app.analytics.models.user_metric import UserMetric
from app.analytics.models.usage_metric import UsageMetric


class MetricsService:
    """
    Responsible for collecting and persisting platform metrics.

    This service is typically called by:

    - Background workers
    - Scheduler
    - Event handlers
    - Execution engine
    """

    def __init__(self, db: AsyncSession):
        self.repository = AnalyticsRepository(db)

    async def record_workflow_metrics(
        self,
        *,
        total_executions: int,
        successful_executions: int,
        failed_executions: int,
        running_executions: int,
        average_duration_ms: float,
    ) -> WorkflowMetric:

        total = max(total_executions, 1)

        metric = WorkflowMetric(
            total_executions=total_executions,
            successful_executions=successful_executions,
            failed_executions=failed_executions,
            running_executions=running_executions,
            average_duration_ms=average_duration_ms,
            success_rate=(successful_executions / total) * 100,
            collected_at=datetime.utcnow(),
        )

        return await self.repository.create_workflow_metric(metric)

    async def record_usage_metrics(
        self,
        *,
        api_calls: int,
        tokens_used: int,
        storage_used_gb: float,
        bandwidth_gb: float,
    ) -> UsageMetric:

        metric = UsageMetric(
            api_calls=api_calls,
            tokens_used=tokens_used,
            storage_used_gb=storage_used_gb,
            bandwidth_gb=bandwidth_gb,
            collected_at=datetime.utcnow(),
        )

        return await self.repository.create_usage_metric(metric)

    async def record_user_metrics(
        self,
        *,
        active_users: int,
        new_users: int,
        organizations: int,
        projects: int,
    ) -> UserMetric:

        metric = UserMetric(
            active_users=active_users,
            new_users=new_users,
            organizations=organizations,
            projects=projects,
            collected_at=datetime.utcnow(),
        )

        return await self.repository.create_user_metric(metric)

    async def collect_snapshot(
        self,
        *,
        workflow: dict,
        usage: dict,
        users: dict,
    ):
        """
        Store all metrics together as a single collection cycle.
        """

        workflow_metric = await self.record_workflow_metrics(**workflow)
        usage_metric = await self.record_usage_metrics(**usage)
        user_metric = await self.record_user_metrics(**users)

        return {
            "workflow": workflow_metric,
            "usage": usage_metric,
            "users": user_metric,
            "collected_at": datetime.utcnow(),
        }