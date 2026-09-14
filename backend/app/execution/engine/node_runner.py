"""
Node Runner.

Executes a single workflow node by delegating
execution to the appropriate runtime.
"""

from typing import Dict, Any

from app.execution.runtime.http_runtime import HTTPRuntime
from app.execution.runtime.condition_runtime import ConditionRuntime
from app.execution.runtime.database_runtime import DatabaseRuntime
from app.execution.runtime.delay_runtime import DelayRuntime
from app.execution.runtime.webhook_runtime import WebhookRuntime

from app.execution.exceptions.node_exception import NodeExecutionException
from app.execution.constants.node_types import NodeType


class NodeRunner:
    """
    Executes workflow nodes.
    """

    def __init__(self) -> None:
        self._runtimes = {
            NodeType.HTTP: HTTPRuntime(),
            NodeType.CONDITION: ConditionRuntime(),
            NodeType.DATABASE: DatabaseRuntime(),
            NodeType.DELAY: DelayRuntime(),
            NodeType.WEBHOOK: WebhookRuntime(),
        }

    def run(
        self,
        node: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute a workflow node.

        Args:
            node: Workflow node
            context: Execution context

        Returns:
            Execution result
        """

        node_type = node.get("type")

        runtime = self._runtimes.get(node_type)

        if runtime is None:
            raise NodeExecutionException(
                f"Unsupported node type: {node_type}"
            )

        return runtime.execute(node, context)