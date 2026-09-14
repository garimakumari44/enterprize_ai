from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class FailurePolicy(str, Enum):
    """
    Behavior when a node fails.
    """

    FAIL_FAST = "fail_fast"
    CONTINUE = "continue"
    RETRY = "retry"


class RecoveryPolicy(str, Enum):
    """
    Recovery strategy.
    """

    NONE = "none"
    RETRY = "retry"
    CHECKPOINT_RESTORE = "checkpoint_restore"


class ApprovalPolicy(str, Enum):
    """
    Human approval requirements.
    """

    NONE = "none"
    REQUIRED = "required"


@dataclass
class ExecutionPolicy:
    """
    Runtime execution rules.

    These policies are consumed by:
        - WorkflowOrchestrator
        - WorkflowExecutor
        - RetryExecutor
        - RecoveryManager
    """

    # --------------------------------------------------
    # Failure Handling
    # --------------------------------------------------

    failure_policy: FailurePolicy = FailurePolicy.FAIL_FAST

    # --------------------------------------------------
    # Retry
    # --------------------------------------------------

    max_retries: int = 3

    retry_delay_seconds: float = 1.0

    # --------------------------------------------------
    # Timeout
    # --------------------------------------------------

    workflow_timeout_seconds: Optional[int] = None

    node_timeout_seconds: Optional[int] = None

    # --------------------------------------------------
    # Parallelism
    # --------------------------------------------------

    max_parallel_nodes: int = 10

    # --------------------------------------------------
    # Recovery
    # --------------------------------------------------

    recovery_policy: RecoveryPolicy = RecoveryPolicy.RETRY

    checkpoint_enabled: bool = False

    # --------------------------------------------------
    # Human Approval
    # --------------------------------------------------

    approval_policy: ApprovalPolicy = ApprovalPolicy.NONE

    approval_nodes: List[str] = field(default_factory=list)

    # --------------------------------------------------
    # State Persistence
    # --------------------------------------------------

    persist_state: bool = True

    persist_results: bool = True

    # --------------------------------------------------
    # Monitoring
    # --------------------------------------------------

    emit_events: bool = True

    collect_metrics: bool = True

    # --------------------------------------------------
    # Validation
    # --------------------------------------------------

    def validate(self) -> None:
        """
        Validate execution policy.
        """

        if self.max_retries < 0:
            raise ValueError(
                "max_retries cannot be negative"
            )

        if self.max_parallel_nodes < 1:
            raise ValueError(
                "max_parallel_nodes must be >= 1"
            )

        if (
            self.workflow_timeout_seconds is not None
            and self.workflow_timeout_seconds <= 0
        ):
            raise ValueError(
                "workflow_timeout_seconds must be positive"
            )

        if (
            self.node_timeout_seconds is not None
            and self.node_timeout_seconds <= 0
        ):
            raise ValueError(
                "node_timeout_seconds must be positive"
            )