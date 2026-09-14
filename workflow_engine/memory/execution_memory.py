# execution_memory.py

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from threading import RLock
from typing import Any, Dict, List, Optional


@dataclass
class MemoryEntry:
    key: str
    value: Any
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ExecutionMemory:
    """
    Runtime memory for workflow execution.

    Stores:
    - node outputs
    - intermediate artifacts
    - agent decisions
    - execution metadata
    - checkpoints
    """

    def __init__(self):
        self._lock = RLock()

        self._data: Dict[str, Any] = {}

        self._history: List[MemoryEntry] = []

        self._checkpoints: Dict[str, Dict[str, Any]] = {}

    # --------------------------------------------------
    # Basic Operations
    # --------------------------------------------------

    def put(self, key: str, value: Any) -> None:
        with self._lock:
            self._data[key] = value

            self._history.append(
                MemoryEntry(
                    key=key,
                    value=value,
                )
            )

    def get(
        self,
        key: str,
        default: Optional[Any] = None,
    ) -> Any:
        with self._lock:
            return self._data.get(key, default)

    def exists(self, key: str) -> bool:
        with self._lock:
            return key in self._data

    def delete(self, key: str) -> None:
        with self._lock:
            self._data.pop(key, None)

    # --------------------------------------------------
    # Bulk Operations
    # --------------------------------------------------

    def update(self, values: Dict[str, Any]) -> None:
        with self._lock:
            for key, value in values.items():
                self.put(key, value)

    def all(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._data)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()

    # --------------------------------------------------
    # Node Memory
    # --------------------------------------------------

    def store_node_output(
        self,
        node_id: str,
        output: Any,
    ) -> None:
        self.put(f"node:{node_id}:output", output)

    def get_node_output(
        self,
        node_id: str,
    ) -> Any:
        return self.get(f"node:{node_id}:output")

    # --------------------------------------------------
    # Agent Memory
    # --------------------------------------------------

    def store_agent_decision(
        self,
        agent_id: str,
        decision: Any,
    ) -> None:
        self.put(
            f"agent:{agent_id}:decision",
            decision,
        )

    def get_agent_decision(
        self,
        agent_id: str,
    ) -> Any:
        return self.get(
            f"agent:{agent_id}:decision"
        )

    # --------------------------------------------------
    # Checkpointing
    # --------------------------------------------------

    def create_checkpoint(
        self,
        checkpoint_id: str,
    ) -> None:
        with self._lock:
            self._checkpoints[checkpoint_id] = (
                dict(self._data)
            )

    def restore_checkpoint(
        self,
        checkpoint_id: str,
    ) -> None:
        with self._lock:
            snapshot = self._checkpoints.get(
                checkpoint_id
            )

            if snapshot is None:
                raise ValueError(
                    f"Checkpoint '{checkpoint_id}' not found"
                )

            self._data = dict(snapshot)

    def list_checkpoints(self) -> List[str]:
        with self._lock:
            return list(self._checkpoints.keys())

    # --------------------------------------------------
    # History
    # --------------------------------------------------

    def history(self) -> List[MemoryEntry]:
        return self._history.copy()

    # --------------------------------------------------
    # Debugging
    # --------------------------------------------------

    def summary(self) -> Dict[str, Any]:
        return {
            "keys": len(self._data),
            "history_entries": len(self._history),
            "checkpoints": len(self._checkpoints),
        }