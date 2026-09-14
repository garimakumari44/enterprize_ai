from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Set, Optional

from contracts.dag import DAG
from contracts.node import Node
from contracts.enums import NodeStatus


class DAGRuntime:
    """
    Runtime representation of a DAG.

    Responsible for:

    - Dependency tracking
    - Node state tracking
    - Runnable node discovery
    - Completion checks

    Does NOT execute nodes.
    """

    def __init__(self, dag: DAG):

        self.dag = dag

        self.nodes: Dict[str, Node] = {
            node.id: node
            for node in dag.nodes
        }

        self.node_status: Dict[str, NodeStatus] = {
            node.id: NodeStatus.PENDING
            for node in dag.nodes
        }

        self.dependencies: Dict[str, Set[str]] = defaultdict(set)

        self.dependents: Dict[str, Set[str]] = defaultdict(set)

        self._build_graph()

    # ---------------------------------------------------------
    # Graph Initialization
    # ---------------------------------------------------------

    def _build_graph(self) -> None:

        for node in self.dag.nodes:

            for dep in node.dependencies:

                self.dependencies[node.id].add(dep)
                self.dependents[dep].add(node.id)

    # ---------------------------------------------------------
    # State Updates
    # ---------------------------------------------------------

    def mark_running(self, node_id: str) -> None:
        self.node_status[node_id] = NodeStatus.RUNNING

    def mark_completed(self, node_id: str) -> None:
        self.node_status[node_id] = NodeStatus.COMPLETED

    def mark_failed(self, node_id: str) -> None:
        self.node_status[node_id] = NodeStatus.FAILED

    def mark_skipped(self, node_id: str) -> None:
        self.node_status[node_id] = NodeStatus.SKIPPED

    # ---------------------------------------------------------
    # Query Methods
    # ---------------------------------------------------------

    def get_status(self, node_id: str) -> NodeStatus:
        return self.node_status[node_id]

    def get_node(self, node_id: str) -> Node:
        return self.nodes[node_id]

    # ---------------------------------------------------------
    # Scheduling Logic
    # ---------------------------------------------------------

    def is_runnable(self, node_id: str) -> bool:

        status = self.node_status[node_id]

        if status != NodeStatus.PENDING:
            return False

        deps = self.dependencies.get(node_id, set())

        return all(
            self.node_status[d] == NodeStatus.COMPLETED
            for d in deps
        )

    def get_runnable_nodes(self) -> List[Node]:

        runnable = []

        for node_id in self.nodes:

            if self.is_runnable(node_id):
                runnable.append(
                    self.nodes[node_id]
                )

        return runnable

    # ---------------------------------------------------------
    # Runtime State
    # ---------------------------------------------------------

    def is_finished(self) -> bool:

        return all(
            status in {
                NodeStatus.COMPLETED,
                NodeStatus.FAILED,
                NodeStatus.SKIPPED
            }
            for status in self.node_status.values()
        )

    def has_failures(self) -> bool:

        return any(
            status == NodeStatus.FAILED
            for status in self.node_status.values()
        )

    def completed_count(self) -> int:

        return sum(
            1
            for s in self.node_status.values()
            if s == NodeStatus.COMPLETED
        )

    def pending_count(self) -> int:

        return sum(
            1
            for s in self.node_status.values()
            if s == NodeStatus.PENDING
        )

    # ---------------------------------------------------------
    # Diagnostics
    # ---------------------------------------------------------

    def summary(self) -> dict:

        counts = defaultdict(int)

        for status in self.node_status.values():
            counts[status.value] += 1

        return dict(counts)

    def __repr__(self) -> str:

        return (
            f"DAGRuntime("
            f"nodes={len(self.nodes)}, "
            f"completed={self.completed_count()}, "
            f"pending={self.pending_count()}"
            f")"
        )