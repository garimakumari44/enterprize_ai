from typing import Dict, Any, List
from builder.dag_builder import DAGBuilder
from contracts.workflow import Workflow
from contracts.node import Node


class WorkflowBuilder:
    """
    High-level builder that constructs a full workflow from a spec.
    """

    def __init__(self):
        self.dag_builder = DAGBuilder()

    def from_spec(self, spec: Dict[str, Any]) -> Workflow:
        """
        spec format example:
        {
            "id": "wf_1",
            "nodes": [
                {"id": "n1", "type": "task", "task": {...}},
                {"id": "n2", "type": "task", "task": {...}}
            ],
            "edges": [
                ["n1", "n2"]
            ]
        }
        """

        workflow_id = spec["id"]
        nodes = spec.get("nodes", [])
        edges = spec.get("edges", [])

        # Step 1: Add nodes
        for n in nodes:
            node = Node(
                id=n["id"],
                type=n["type"],
                task=n.get("task")
            )
            self.dag_builder.add_node(node)

        # Step 2: Add edges
        for from_node, to_node in edges:
            self.dag_builder.add_edge(from_node, to_node)

        # Step 3: Build DAG
        dag = self.dag_builder.build()

        # Step 4: Wrap into workflow
        return Workflow(
            id=workflow_id,
            dag=dag,
            metadata=spec.get("metadata", {})
        )