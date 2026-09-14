# context_memory.py

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from threading import RLock
from typing import Any, Dict, List, Optional


@dataclass
class ContextEntry:
    key: str
    value: Any
    source: str = "system"
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ContextMemory:
    """
    Shared contextual memory used by:

    - Workflow Planner
    - Agents
    - Adaptation Engine
    - Decision Engine
    - LLM Nodes

    Examples:
        user_profile
        workflow_goal
        business_rules
        execution_constraints
        current_environment
    """

    def __init__(self):
        self._lock = RLock()

        self._context: Dict[str, Any] = {}

        self._history: List[ContextEntry] = []

    # --------------------------------------------------
    # Basic Context Operations
    # --------------------------------------------------

    def set(
        self,
        key: str,
        value: Any,
        source: str = "system",
    ) -> None:
        with self._lock:
            self._context[key] = value

            self._history.append(
                ContextEntry(
                    key=key,
                    value=value,
                    source=source,
                )
            )

    def get(
        self,
        key: str,
        default: Optional[Any] = None,
    ) -> Any:
        with self._lock:
            return self._context.get(key, default)

    def exists(self, key: str) -> bool:
        with self._lock:
            return key in self._context

    def delete(self, key: str) -> None:
        with self._lock:
            self._context.pop(key, None)

    # --------------------------------------------------
    # Bulk Operations
    # --------------------------------------------------

    def update(
        self,
        values: Dict[str, Any],
        source: str = "system",
    ) -> None:
        for key, value in values.items():
            self.set(key, value, source)

    def all(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._context)

    # --------------------------------------------------
    # Workflow Context
    # --------------------------------------------------

    def set_workflow_goal(
        self,
        goal: str,
    ) -> None:
        self.set(
            "workflow_goal",
            goal,
            source="workflow"
        )

    def workflow_goal(self) -> Optional[str]:
        return self.get("workflow_goal")

    def set_workflow_constraints(
        self,
        constraints: Dict[str, Any],
    ) -> None:
        self.set(
            "workflow_constraints",
            constraints,
            source="workflow"
        )

    def workflow_constraints(self) -> Dict[str, Any]:
        return self.get(
            "workflow_constraints",
            {}
        )

    # --------------------------------------------------
    # User Context
    # --------------------------------------------------

    def set_user_context(
        self,
        user_context: Dict[str, Any],
    ) -> None:
        self.set(
            "user_context",
            user_context,
            source="user"
        )

    def user_context(self) -> Dict[str, Any]:
        return self.get(
            "user_context",
            {}
        )

    # --------------------------------------------------
    # Agent Context
    # --------------------------------------------------

    def set_agent_context(
        self,
        agent_id: str,
        context: Dict[str, Any],
    ) -> None:
        self.set(
            f"agent:{agent_id}:context",
            context,
            source=agent_id,
        )

    def get_agent_context(
        self,
        agent_id: str,
    ) -> Dict[str, Any]:
        return self.get(
            f"agent:{agent_id}:context",
            {}
        )

    # --------------------------------------------------
    # Environment Context
    # --------------------------------------------------

    def set_environment(
        self,
        environment: Dict[str, Any],
    ) -> None:
        self.set(
            "environment",
            environment,
            source="system",
        )

    def environment(self) -> Dict[str, Any]:
        return self.get(
            "environment",
            {}
        )

    # --------------------------------------------------
    # Context Retrieval
    # --------------------------------------------------

    def get_relevant_context(
        self,
        keys: List[str],
    ) -> Dict[str, Any]:

        result = {}

        for key in keys:
            if key in self._context:
                result[key] = self._context[key]

        return result

    # --------------------------------------------------
    # Prompt Context Builder
    # --------------------------------------------------

    def build_llm_context(
        self,
        keys: Optional[List[str]] = None,
    ) -> Dict[str, Any]:

        if keys is None:
            return dict(self._context)

        return self.get_relevant_context(keys)

    # --------------------------------------------------
    # History
    # --------------------------------------------------

    def history(self) -> List[ContextEntry]:
        return self._history.copy()

    # --------------------------------------------------
    # Maintenance
    # --------------------------------------------------

    def clear(self) -> None:
        with self._lock:
            self._context.clear()

    def summary(self) -> Dict[str, Any]:
        return {
            "context_items": len(self._context),
            "history_entries": len(self._history),
        }