from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analytics.models.workflow_metric import WorkflowMetric
from app.analytics.models.user_metric import UserMetric
from app.analytics.models.usage_metric import UsageMetric


class AnalyticsRepository:

    def __init__(self, db: Session):
        self.db = db

    # =====================================================
    # Workflow Metrics
    # =====================================================

    def create_workflow_metric(self, metric: WorkflowMetric):
        self.db.add(metric)
        self.db.commit()
        self.db.refresh(metric)
        return metric

    def get_workflow_metric(self, metric_id: int):
        return self.db.get(WorkflowMetric, metric_id)

    def get_workflow_metric_by_workflow(self, workflow_id: int):
        stmt = select(WorkflowMetric).where(
            WorkflowMetric.workflow_id == workflow_id
        )
        return self.db.scalar(stmt)

    def list_workflow_metrics(self):
        stmt = select(WorkflowMetric)
        return self.db.scalars(stmt).all()

    def update_workflow_metric(self, metric: WorkflowMetric):
        self.db.commit()
        self.db.refresh(metric)
        return metric

    def delete_workflow_metric(self, metric: WorkflowMetric):
        self.db.delete(metric)
        self.db.commit()

    # =====================================================
    # User Metrics
    # =====================================================

    def create_user_metric(self, metric: UserMetric):
        self.db.add(metric)
        self.db.commit()
        self.db.refresh(metric)
        return metric

    def get_user_metric(self, metric_id: int):
        return self.db.get(UserMetric, metric_id)

    def get_user_metric_by_user(self, user_id: int):
        stmt = select(UserMetric).where(
            UserMetric.user_id == user_id
        )
        return self.db.scalar(stmt)

    def list_user_metrics(self):
        stmt = select(UserMetric)
        return self.db.scalars(stmt).all()

    def update_user_metric(self, metric: UserMetric):
        self.db.commit()
        self.db.refresh(metric)
        return metric

    def delete_user_metric(self, metric: UserMetric):
        self.db.delete(metric)
        self.db.commit()

    # =====================================================
    # Usage Metrics
    # =====================================================

    def create_usage_metric(self, metric: UsageMetric):
        self.db.add(metric)
        self.db.commit()
        self.db.refresh(metric)
        return metric

    def get_usage_metric(self, metric_id: int):
        return self.db.get(UsageMetric, metric_id)

    def get_usage_metric_by_organization(self, organization_id: int):
        stmt = select(UsageMetric).where(
            UsageMetric.organization_id == organization_id
        )
        return self.db.scalar(stmt)

    def list_usage_metrics(self):
        stmt = select(UsageMetric)
        return self.db.scalars(stmt).all()

    def update_usage_metric(self, metric: UsageMetric):
        self.db.commit()
        self.db.refresh(metric)
        return metric

    def delete_usage_metric(self, metric: UsageMetric):
        self.db.delete(metric)
        self.db.commit()

    # =====================================================
    # Dashboard Aggregates
    # =====================================================

    def total_workflow_executions(self):
        stmt = select(WorkflowMetric)
        metrics = self.db.scalars(stmt).all()
        return sum(m.executions for m in metrics)

    def total_successful_executions(self):
        stmt = select(WorkflowMetric)
        metrics = self.db.scalars(stmt).all()
        return sum(m.successful_executions for m in metrics)

    def total_failed_executions(self):
        stmt = select(WorkflowMetric)
        metrics = self.db.scalars(stmt).all()
        return sum(m.failed_executions for m in metrics)

    def total_api_calls(self):
        stmt = select(UsageMetric)
        metrics = self.db.scalars(stmt).all()
        return sum(m.api_calls for m in metrics)

    def total_llm_tokens(self):
        stmt = select(UsageMetric)
        metrics = self.db.scalars(stmt).all()
        return sum(m.llm_tokens for m in metrics)

    def total_storage_used(self):
        stmt = select(UsageMetric)
        metrics = self.db.scalars(stmt).all()
        return sum(m.storage_used_mb for m in metrics)

    def total_active_users(self):
        stmt = select(UsageMetric)
        metrics = self.db.scalars(stmt).all()
        return sum(m.active_users for m in metrics)