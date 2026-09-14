from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class WorkflowEvent:
    """
    Base event emitted during workflow execution.
    This is the backbone of observability + event-bus integration.
    """

    # Identity
    event_id: str
    workflow_id: str
    execution_id: str

    # Event classification
    event_type: str  # e.g. WORKFLOW_STARTED, NODE_STARTED, NODE_COMPLETED

    # Source of event
    source: str  # orchestrator | executor | node | tool | system

    # Associated node (if any)
    node_id: Optional[str] = None

    # Event payload (flexible data)
    payload: Dict[str, Any] = field(default_factory=dict)

    # Status context (optional but useful)
    status: Optional[str] = None

    # Timing
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Error info (if event represents failure)
    error: Optional[str] = None

    # Traceability
    trace_id: Optional[str] = None


# -----------------------------
# Common Event Types Registry
# -----------------------------

class EventTypes:
    """
    Standard event names used across the system.
    Prevents string-hell in event-driven architecture.
    """

    # Workflow lifecycle
    WORKFLOW_STARTED = "WORKFLOW_STARTED"
    WORKFLOW_COMPLETED = "WORKFLOW_COMPLETED"
    WORKFLOW_FAILED = "WORKFLOW_FAILED"

    # Node lifecycle
    NODE_STARTED = "NODE_STARTED"
    NODE_COMPLETED = "NODE_COMPLETED"
    NODE_FAILED = "NODE_FAILED"
    NODE_SKIPPED = "NODE_SKIPPED"

    # Execution control
    DAG_BUILT = "DAG_BUILT"
    DAG_EXECUTION_STARTED = "DAG_EXECUTION_STARTED"
    DAG_EXECUTION_COMPLETED = "DAG_EXECUTION_COMPLETED"

    # Tool execution (future Phase 2+)
    TOOL_INVOKED = "TOOL_INVOKED"
    TOOL_COMPLETED = "TOOL_COMPLETED"
    TOOL_FAILED = "TOOL_FAILED"

    # System-level
    STATE_UPDATED = "STATE_UPDATED"
    RESULT_EMITTED = "RESULT_EMITTED"