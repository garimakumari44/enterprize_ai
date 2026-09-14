

from __future__ import annotations

from typing import Dict, List, Optional, Callable

from contracts.workflow import Workflow
from contracts.task import Task
from contracts.state import WorkflowState


class RoutingEngine:
    """
    Determines the next node(s) to execute.

    Supports:
    - DAG edge traversal
    - Conditional routing
    - Parallel branches
    - Failure routing
    """

    def __init__(self):
        self._conditions: Dict[str, Callable] = {}

    # --------------------------------------------------
    # Registration
    # --------------------------------------------------

    def register_condition(
        self,
        condition_name: str,
        fn: Callable,
    ) -> None:
        self._conditions[condition_name] = fn

    # --------------------------------------------------
    # Main Routing Logic
    # --------------------------------------------------

    def next_nodes(
        self,
        workflow: Workflow,
        current_node_id: str,
        state: WorkflowState,
    ) -> List[str]:

        node = workflow.get_node(current_node_id)

        if not node:
            return []

        next_nodes = []

        for edge in node.edges:

            # unconditional route
            if edge.condition is None:
                next_nodes.append(edge.target)
                continue

            condition_fn = self._conditions.get(
                edge.condition
            )

            if not condition_fn:
                continue

            try:
                result = condition_fn(state)

                if result:
                    next_nodes.append(edge.target)

            except Exception:
                continue

        return next_nodes

    # --------------------------------------------------
    # Failure Routing
    # --------------------------------------------------

    def failure_nodes(
        self,
        workflow: Workflow,
        current_node_id: str,
    ) -> List[str]:

        node = workflow.get_node(current_node_id)

        if not node:
            return []

        return node.failure_routes

    # --------------------------------------------------
    # Terminal Check
    # --------------------------------------------------

    def is_terminal(
        self,
        workflow: Workflow,
        node_id: str,
    ) -> bool:

        node = workflow.get_node(node_id)

        if not node:
            return True

        return len(node.edges) == 0

    # --------------------------------------------------
    # Human Approval Routing
    # --------------------------------------------------

    def requires_approval(
        self,
        workflow: Workflow,
        node_id: str,
    ) -> bool:

        node = workflow.get_node(node_id)

        if not node:
            return False

        return getattr(
            node,
            "requires_approval",
            False,
        )