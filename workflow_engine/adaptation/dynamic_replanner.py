

from __future__ import annotations

from copy import deepcopy
from typing import List, Optional

from contracts.dag import DAG
from contracts.node import Node
from contracts.enums import NodeStatus


class DynamicReplanner:
    """
    Dynamically modifies workflow plans during execution.

    Responsibilities:
    - Skip failed branches
    - Insert recovery tasks
    - Replace unavailable nodes
    - Re-route dependencies
    - Optimize execution path
    """

    def replan(
        self,
        dag: DAG,
        trigger_node_id: str,
        reason: str,
    ) -> DAG:
        """
        Generate an updated DAG based on runtime conditions.
        """

        updated_dag = deepcopy(dag)

        if reason == "TASK_FAILED":
            self._handle_failure(updated_dag, trigger_node_id)

        elif reason == "RESOURCE_UNAVAILABLE":
            self._handle_resource_unavailable(
                updated_dag,
                trigger_node_id,
            )

        elif reason == "TIMEOUT":
            self._handle_timeout(
                updated_dag,
                trigger_node_id,
            )

        return updated_dag

    # --------------------------------------------------
    # Failure Recovery
    # --------------------------------------------------

    def _handle_failure(
        self,
        dag: DAG,
        node_id: str,
    ) -> None:

        failed_node = dag.nodes.get(node_id)

        if not failed_node:
            return

        recovery_node = Node(
            id=f"recovery_{node_id}",
            name=f"Recover {failed_node.name}",
            task_type="recovery",
            dependencies=[node_id],
        )

        dag.nodes[recovery_node.id] = recovery_node

    # --------------------------------------------------
    # Resource Recovery
    # --------------------------------------------------

    def _handle_resource_unavailable(
        self,
        dag: DAG,
        node_id: str,
    ) -> None:

        node = dag.nodes.get(node_id)

        if not node:
            return

        fallback = node.metadata.get("fallback_task")

        if fallback:
            node.task_type = fallback

    # --------------------------------------------------
    # Timeout Recovery
    # --------------------------------------------------

    def _handle_timeout(
        self,
        dag: DAG,
        node_id: str,
    ) -> None:

        node = dag.nodes.get(node_id)

        if not node:
            return

        node.metadata["priority"] = "high"

    # --------------------------------------------------
    # DAG Optimization
    # --------------------------------------------------

    def optimize(
        self,
        dag: DAG,
    ) -> DAG:
        """
        Runtime DAG optimization.
        """

        optimized = deepcopy(dag)

        removable_nodes = []

        for node in optimized.nodes.values():

            if (
                node.status == NodeStatus.SKIPPED
                and not node.dependencies
            ):
                removable_nodes.append(node.id)

        for node_id in removable_nodes:
            optimized.nodes.pop(node_id, None)

        return optimized