# runtime/dependency_resolver.py

from collections import defaultdict, deque
from typing import Dict, List, Set

from contracts.dag import DAG
from contracts.node import Node


class DependencyResolver:
    """
    Resolves DAG dependencies and execution order.
    """

    def __init__(self, dag: DAG):
        self.dag = dag

    def topological_sort(self) -> List[str]:
        """
        Returns execution order for DAG nodes.
        Raises ValueError if cycle exists.
        """

        in_degree = defaultdict(int)
        graph = defaultdict(list)

        for node in self.dag.nodes.values():
            for dep in node.dependencies:
                graph[dep].append(node.id)
                in_degree[node.id] += 1

        queue = deque()

        for node_id in self.dag.nodes:
            if in_degree[node_id] == 0:
                queue.append(node_id)

        order = []

        while queue:
            current = queue.popleft()
            order.append(current)

            for neighbor in graph[current]:
                in_degree[neighbor] -= 1

                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(order) != len(self.dag.nodes):
            raise ValueError("Cycle detected in workflow DAG.")

        return order

    def get_root_nodes(self) -> List[str]:
        """
        Nodes with no dependencies.
        """

        return [
            node.id
            for node in self.dag.nodes.values()
            if not node.dependencies
        ]

    def get_leaf_nodes(self) -> List[str]:
        """
        Nodes with no outgoing edges.
        """

        parents = set()

        for node in self.dag.nodes.values():
            parents.update(node.dependencies)

        return [
            node.id
            for node in self.dag.nodes.values()
            if node.id not in parents
        ]

    def get_ready_nodes(
        self,
        completed_nodes: Set[str]
    ) -> List[str]:
        """
        Returns nodes whose dependencies are satisfied.
        """

        ready = []

        for node in self.dag.nodes.values():

            if node.id in completed_nodes:
                continue

            if all(
                dep in completed_nodes
                for dep in node.dependencies
            ):
                ready.append(node.id)

        return ready

    def validate(self) -> bool:
        """
        Validates DAG structure.
        """

        self.topological_sort()

        for node in self.dag.nodes.values():
            for dep in node.dependencies:

                if dep not in self.dag.nodes:
                    raise ValueError(
                        f"Node '{node.id}' depends on "
                        f"unknown node '{dep}'"
                    )

        return True