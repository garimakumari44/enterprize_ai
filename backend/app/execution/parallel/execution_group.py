from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


class BranchStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class BranchExecution:
    """
    Represents one parallel branch.
    """

    branch_id: UUID
    start_node_id: UUID

    status: BranchStatus = BranchStatus.PENDING

    result: Optional[Any] = None

    error: Optional[str] = None


@dataclass
class ExecutionGroup:
    """
    Represents an entire parallel execution.

    Example

            Parallel Node
          /      |      \
        A1      B1      C1
         |       |       |
        A2      B2      C2
          \      |      /
            Merge Node

    This object tracks every branch.
    """

    workflow_execution_id: UUID

    group_id: UUID = field(default_factory=uuid4)

    branches: List[BranchExecution] = field(default_factory=list)

    metadata: Dict[str, Any] = field(default_factory=dict)

    _lock: Lock = field(default_factory=Lock, repr=False)

    # ---------------------------------------------------------

    def add_branch(self, branch: BranchExecution) -> None:
        with self._lock:
            self.branches.append(branch)

    # ---------------------------------------------------------

    def get_branch(self, branch_id: UUID) -> Optional[BranchExecution]:
        for branch in self.branches:
            if branch.branch_id == branch_id:
                return branch
        return None

    # ---------------------------------------------------------

    def mark_running(self, branch_id: UUID) -> None:
        branch = self.get_branch(branch_id)
        if branch:
            branch.status = BranchStatus.RUNNING

    # ---------------------------------------------------------

    def mark_completed(
        self,
        branch_id: UUID,
        result: Any = None,
    ) -> None:
        branch = self.get_branch(branch_id)

        if branch:
            branch.status = BranchStatus.COMPLETED
            branch.result = result

    # ---------------------------------------------------------

    def mark_failed(
        self,
        branch_id: UUID,
        error: str,
    ) -> None:
        branch = self.get_branch(branch_id)

        if branch:
            branch.status = BranchStatus.FAILED
            branch.error = error

    # ---------------------------------------------------------

    @property
    def completed_count(self) -> int:
        return sum(
            b.status == BranchStatus.COMPLETED
            for b in self.branches
        )

    # ---------------------------------------------------------

    @property
    def failed_count(self) -> int:
        return sum(
            b.status == BranchStatus.FAILED
            for b in self.branches
        )

    # ---------------------------------------------------------

    @property
    def running_count(self) -> int:
        return sum(
            b.status == BranchStatus.RUNNING
            for b in self.branches
        )

    # ---------------------------------------------------------

    @property
    def total_branches(self) -> int:
        return len(self.branches)

    # ---------------------------------------------------------

    @property
    def is_finished(self) -> bool:
        return (
            self.completed_count +
            self.failed_count
        ) == self.total_branches

    # ---------------------------------------------------------

    @property
    def has_failures(self) -> bool:
        return self.failed_count > 0

    # ---------------------------------------------------------

    def results(self) -> Dict[str, Any]:
        """
        Collect branch outputs.
        """

        return {
            str(branch.branch_id): branch.result
            for branch in self.branches
            if branch.status == BranchStatus.COMPLETED
        }

    # ---------------------------------------------------------

    def errors(self) -> Dict[str, str]:
        return {
            str(branch.branch_id): branch.error
            for branch in self.branches
            if branch.status == BranchStatus.FAILED
        }

    # ---------------------------------------------------------

    def reset(self) -> None:
        """
        Used for retries.
        """

        for branch in self.branches:
            branch.status = BranchStatus.PENDING
            branch.result = None
            branch.error = None