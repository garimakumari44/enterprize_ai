from __future__ import annotations

from enum import Enum


class ExecutionStatus(str, Enum):
    """
    Lifecycle status of a workflow execution.
    """

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"