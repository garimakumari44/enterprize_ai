# contracts/task.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(slots=True)
class Task:
    """
    Fundamental unit of work within a workflow.

    Example:
        research
            ↓
        analysis
            ↓
        report

    Each step is represented as a Task.
    """

    # Unique identifier
    id: str

    # Human-readable name
    name: str

    # Optional description
    description: Optional[str] = None

    # IDs of tasks that must complete first
    dependencies: List[str] = field(default_factory=list)

    # Arbitrary task configuration
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Retry configuration
    max_retries: int = 3

    # Execution timeout (seconds)
    timeout_seconds: Optional[int] = None

    def add_dependency(self, task_id: str) -> None:
        """
        Add a dependency if it does not already exist.
        """
        if task_id not in self.dependencies:
            self.dependencies.append(task_id)

    def remove_dependency(self, task_id: str) -> None:
        """
        Remove a dependency if present.
        """
        if task_id in self.dependencies:
            self.dependencies.remove(task_id)

    def has_dependencies(self) -> bool:
        """
        Returns True if the task depends on other tasks.
        """
        return len(self.dependencies) > 0

    def is_root_task(self) -> bool:
        """
        A root task has no dependencies.
        """
        return len(self.dependencies) == 0