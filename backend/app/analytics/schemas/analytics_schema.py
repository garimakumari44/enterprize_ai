from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ==========================================================
# Workflow Metrics
# ==========================================================

class WorkflowMetricBase(BaseModel):
    workflow_id: int
    executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    average_duration: float = 0.0


class WorkflowMetricCreate(WorkflowMetricBase):
    pass


class WorkflowMetricUpdate(BaseModel):
    executions: Optional[int] = None
    successful_executions: Optional[int] = None
    failed_executions: Optional[int] = None
    average_duration: Optional[float] = None


class WorkflowMetricRead(WorkflowMetricBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


# ==========================================================
# User Metrics
# ==========================================================

class UserMetricBase(BaseModel):
    user_id: int
    workflows_created: int = 0
    executions_started: int = 0
    ai_requests: int = 0


class UserMetricCreate(UserMetricBase):
    pass


class UserMetricUpdate(BaseModel):
    workflows_created: Optional[int] = None
    executions_started: Optional[int] = None
    ai_requests: Optional[int] = None


class UserMetricRead(UserMetricBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


# ==========================================================
# Usage Metrics
# ==========================================================

class UsageMetricBase(BaseModel):
    organization_id: int
    api_calls: int = 0
    llm_tokens: int = 0
    storage_used_mb: float = 0
    active_users: int = 0


class UsageMetricCreate(UsageMetricBase):
    pass


class UsageMetricUpdate(BaseModel):
    api_calls: Optional[int] = None
    llm_tokens: Optional[int] = None
    storage_used_mb: Optional[float] = None
    active_users: Optional[int] = None


class UsageMetricRead(UsageMetricBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime