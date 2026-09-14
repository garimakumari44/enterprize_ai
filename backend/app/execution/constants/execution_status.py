"""
Execution status constants.

Defines the lifecycle states of a workflow execution.
"""

from enum import StrEnum


class ExecutionStatus(StrEnum):
    """
    Workflow execution lifecycle.
    """

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMEOUT = "TIMEOUT"


class ExecutionResult(StrEnum):
    """
    Final execution outcome.
    """

    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    CANCELLED = "CANCELLED"
    TIMEOUT = "TIMEOUT"


class LogLevel(StrEnum):
    """
    Execution log severity levels.
    """

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"