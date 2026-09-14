from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class StateEvent:
    """
    Audit event generated during execution.
    """

    timestamp: datetime
    event_type: str
    message: str


@dataclass
class WorkflowState:
    """
    Shared execution state passed between nodes.
    """

    # Workflow identity
    workflow_id: str
    execution_id: str

    # Original request
    input_data: Dict[str, Any]

    # Current execution data
    context: Dict[str, Any] = field(default_factory=dict)

    # Node outputs
    outputs: Dict[str, Any] = field(default_factory=dict)

    # Variables shared across workflow
    variables: Dict[str, Any] = field(default_factory=dict)

    # Execution metadata
    status: str = "PENDING"

    current_node: Optional[str] = None

    started_at: datetime = field(default_factory=datetime.utcnow)

    completed_at: Optional[datetime] = None

    # Error tracking
    errors: List[str] = field(default_factory=list)

    # Audit trail
    events: List[StateEvent] = field(default_factory=list)

    def set_output(self, node_id: str, output: Any) -> None:
        self.outputs[node_id] = output

    def get_output(self, node_id: str) -> Any:
        return self.outputs.get(node_id)

    def set_variable(self, key: str, value: Any) -> None:
        self.variables[key] = value

    def get_variable(self, key: str, default=None) -> Any:
        return self.variables.get(key, default)

    def add_error(self, error: str) -> None:
        self.errors.append(error)

    def add_event(
        self,
        event_type: str,
        message: str
    ) -> None:
        self.events.append(
            StateEvent(
                timestamp=datetime.utcnow(),
                event_type=event_type,
                message=message,
            )
        )