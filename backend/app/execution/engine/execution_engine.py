"""
Workflow Execution Engine.

Coordinates workflow execution.
"""

from typing import Any, Dict, List, Optional

from app.execution.engine.graph_traverser import GraphTraverser
from app.execution.engine.node_runner import NodeRunner
from app.execution.engine.context_manager import ContextManager


class ExecutionEngine:
    """
    Executes workflow graphs.
    """

    def __init__(self) -> None:
        self.runner = NodeRunner()

    def execute(
        self,
        workflow: Dict[str, Any],
        inputs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a workflow.

        Args:
            workflow: Workflow definition.
            inputs: Initial execution inputs.

        Returns:
            Execution result.
        """

        context = ContextManager(inputs or {})

        traverser = GraphTraverser(
            nodes=workflow["nodes"],
            edges=workflow["edges"],
        )

        current_node = traverser.get_start_node()

        if current_node is None:
            raise ValueError("Workflow has no start node.")

        while current_node is not None:

            result = self.runner.run(
                node=current_node,
                context=context.to_dict(),
            )

            context.set_node_output(
                current_node["id"],
                result,
            )

            if current_node["type"] == "condition":

                condition = result.get("condition", False)

                current_node = traverser.get_condition_node(
                    current_node["id"],
                    condition,
                )

            else:

                current_node = traverser.get_next_node(
                    current_node["id"]
                )

        return {
            "status": "completed",
            "outputs": context.outputs,
            "context": context.to_dict(),
        }