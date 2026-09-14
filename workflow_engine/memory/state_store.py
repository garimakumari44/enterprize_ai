from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from threading import RLock
from typing import Dict, Any, Optional, List


@dataclass
class StateTransition:
    entity_id: str
    old_state: str
    new_state: str
    timestamp: datetime = field(
        default_factory=datetime.utcnow
    )


class StateStore:
    """
    Central workflow state manager.

    Tracks:

    - workflow states
    - node states
    - agent states
    - retries
    - failures
    - transitions
    """

    def __init__(self):
        self._lock = RLock()

        self._workflow_states: Dict[str, str] = {}

        self._node_states: Dict[str, str] = {}

        self._agent_states: Dict[str, str] = {}

        self._retry_counts: Dict[str, int] = {}

        self._failures: Dict[str, Any] = {}

        self._metadata: Dict[str, Dict[str, Any]] = {}

        self._transitions: List[
            StateTransition
        ] = []

    # --------------------------------------------------
    # Workflow State
    # --------------------------------------------------

    def set_workflow_state(
        self,
        workflow_id: str,
        state: str,
    ) -> None:

        with self._lock:

            previous = self._workflow_states.get(
                workflow_id,
                "UNKNOWN"
            )

            self._workflow_states[
                workflow_id
            ] = state

            self._record_transition(
                workflow_id,
                previous,
                state,
            )

    def get_workflow_state(
        self,
        workflow_id: str,
    ) -> Optional[str]:

        return self._workflow_states.get(
            workflow_id
        )

    # --------------------------------------------------
    # Node State
    # --------------------------------------------------

    def set_node_state(
        self,
        node_id: str,
        state: str,
    ) -> None:

        with self._lock:

            previous = self._node_states.get(
                node_id,
                "UNKNOWN"
            )

            self._node_states[node_id] = state

            self._record_transition(
                node_id,
                previous,
                state,
            )

    def get_node_state(
        self,
        node_id: str,
    ) -> Optional[str]:

        return self._node_states.get(node_id)

    # --------------------------------------------------
    # Agent State
    # --------------------------------------------------

    def set_agent_state(
        self,
        agent_id: str,
        state: str,
    ) -> None:

        with self._lock:

            previous = self._agent_states.get(
                agent_id,
                "UNKNOWN"
            )

            self._agent_states[
                agent_id
            ] = state

            self._record_transition(
                agent_id,
                previous,
                state,
            )

    def get_agent_state(
        self,
        agent_id: str,
    ) -> Optional[str]:

        return self._agent_states.get(
            agent_id
        )

    # --------------------------------------------------
    # Retry Tracking
    # --------------------------------------------------

    def increment_retry(
        self,
        entity_id: str,
    ) -> int:

        current = self._retry_counts.get(
            entity_id,
            0
        )

        current += 1

        self._retry_counts[
            entity_id
        ] = current

        return current

    def get_retry_count(
        self,
        entity_id: str,
    ) -> int:

        return self._retry_counts.get(
            entity_id,
            0
        )

    # --------------------------------------------------
    # Failure Tracking
    # --------------------------------------------------

    def record_failure(
        self,
        entity_id: str,
        error: Any,
    ) -> None:

        self._failures[entity_id] = {
            "error": str(error),
            "timestamp": datetime.utcnow(),
        }

    def get_failure(
        self,
        entity_id: str,
    ) -> Optional[Dict]:

        return self._failures.get(entity_id)

    # --------------------------------------------------
    # Metadata
    # --------------------------------------------------

    def set_metadata(
        self,
        entity_id: str,
        metadata: Dict[str, Any],
    ) -> None:

        self._metadata[
            entity_id
        ] = metadata

    def get_metadata(
        self,
        entity_id: str,
    ) -> Dict[str, Any]:

        return self._metadata.get(
            entity_id,
            {}
        )

    # --------------------------------------------------
    # Transitions
    # --------------------------------------------------

    def _record_transition(
        self,
        entity_id: str,
        old_state: str,
        new_state: str,
    ) -> None:

        self._transitions.append(
            StateTransition(
                entity_id=entity_id,
                old_state=old_state,
                new_state=new_state,
            )
        )

    def transitions(self) -> List[
        StateTransition
    ]:
        return self._transitions.copy()

    # --------------------------------------------------
    # Queries
    # --------------------------------------------------

    def workflows_in_state(
        self,
        state: str,
    ) -> List[str]:

        return [
            workflow_id
            for workflow_id, current
            in self._workflow_states.items()
            if current == state
        ]

    def nodes_in_state(
        self,
        state: str,
    ) -> List[str]:

        return [
            node_id
            for node_id, current
            in self._node_states.items()
            if current == state
        ]

    # --------------------------------------------------
    # Snapshot
    # --------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:

        return {
            "workflow_states":
                dict(self._workflow_states),

            "node_states":
                dict(self._node_states),

            "agent_states":
                dict(self._agent_states),

            "retry_counts":
                dict(self._retry_counts),

            "failures":
                dict(self._failures),
        }

    # --------------------------------------------------
    # Metrics
    # --------------------------------------------------

    def summary(self) -> Dict[str, int]:

        return {
            "workflows":
                len(self._workflow_states),

            "nodes":
                len(self._node_states),

            "agents":
                len(self._agent_states),

            "failures":
                len(self._failures),

            "transitions":
                len(self._transitions),
        }