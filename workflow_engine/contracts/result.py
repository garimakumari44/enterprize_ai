from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class NodeResult:
    """
    Result of a single node execution.
    """

    node_id: str
    status: str  # SUCCESS | FAILED | SKIPPED
    output: Any = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowResult:
    """
    Final aggregated result of an entire workflow execution.
    """

    workflow_id: str
    execution_id: str

    # Final output (what user actually cares about)
    output: Any

    # Per-node execution results
    node_results: List[NodeResult] = field(default_factory=list)

    # Overall status
    status: str = "SUCCESS"  # SUCCESS | FAILED | PARTIAL_SUCCESS

    # Execution timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # High-level errors (if any)
    errors: List[str] = field(default_factory=list)

    # Debug / observability metadata
    metrics: Dict[str, Any] = field(default_factory=dict)

    # Traceability
    trace_id: Optional[str] = None

    def add_node_result(self, node_result: NodeResult) -> None:
        self.node_results.append(node_result)

    def add_error(self, error: str) -> None:
        self.errors.append(error)

    def set_metric(self, key: str, value: Any) -> None:
        self.metrics[key] = value

    def get_node(self, node_id: str) -> Optional[NodeResult]:
        return next((n for n in self.node_results if n.node_id == node_id), None)