# state_manager.py

from __future__ import annotations

from datetime import datetime
from threading import Lock
from typing import Any, Dict, Optional


class StateManager:
    """
    Central workflow state storage.

    Responsibilities:
    - Store workflow-level state
    - Store node outputs
    - Track execution progress
    - Provide safe state updates
    """

    def __init__(self) -> None:
        self._lock = Lock()

        self._state: Dict[str, Any] = {
            "workflow_id": None,
            "status": "PENDING",
            "started_at": None,
            "finished_at": None,
            "context": {},
            "node_outputs": {},
            "node_status": {},
            "metadata": {},
        }

    # --------------------------------------------------
    # Workflow Lifecycle
    # --------------------------------------------------

    def start_workflow(self, workflow_id: str) -> None:
        with self._lock:
            self._state["workflow_id"] = workflow_id
            self._state["status"] = "RUNNING"
            self._state["started_at"] = datetime.utcnow()

    def complete_workflow(self) -> None:
        with self._lock:
            self._state["status"] = "COMPLETED"
            self._state["finished_at"] = datetime.utcnow()

    def fail_workflow(self) -> None:
        with self._lock:
            self._state["status"] = "FAILED"
            self._state["finished_at"] = datetime.utcnow()

    # --------------------------------------------------
    # Node Status
    # --------------------------------------------------

    def set_node_status(
        self,
        node_id: str,
        status: str,
    ) -> None:
        with self._lock:
            self._state["node_status"][node_id] = status

    def get_node_status(
        self,
        node_id: str,
    ) -> Optional[str]:
        return self._state["node_status"].get(node_id)

    # --------------------------------------------------
    # Node Outputs
    # --------------------------------------------------

    def set_node_output(
        self,
        node_id: str,
        output: Any,
    ) -> None:
        with self._lock:
            self._state["node_outputs"][node_id] = output

    def get_node_output(
        self,
        node_id: str,
    ) -> Any:
        return self._state["node_outputs"].get(node_id)

    # --------------------------------------------------
    # Shared Context
    # --------------------------------------------------

    def update_context(
        self,
        key: str,
        value: Any,
    ) -> None:
        with self._lock:
            self._state["context"][key] = value

    def get_context(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        return self._state["context"].get(key, default)

    # --------------------------------------------------
    # Metadata
    # --------------------------------------------------

    def set_metadata(
        self,
        key: str,
        value: Any,
    ) -> None:
        with self._lock:
            self._state["metadata"][key] = value

    def get_metadata(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        return self._state["metadata"].get(key, default)

    # --------------------------------------------------
    # Snapshot
    # --------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._state)

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------

    @property
    def status(self) -> str:
        return self._state["status"]

    @property
    def workflow_id(self) -> Optional[str]:
        return self._state["workflow_id"]