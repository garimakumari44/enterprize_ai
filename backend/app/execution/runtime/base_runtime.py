"""
Base Runtime

Abstract base class for all workflow node runtimes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.execution.engine.context_manager import ContextManager
from app.execution.utils.variable_resolver import VariableResolver


class BaseRuntime(ABC):
    """
    Base runtime for all node executors.

    Every runtime should inherit from this class.

    Example:
        HTTPRuntime
        DatabaseRuntime
        ConditionRuntime
        DelayRuntime
        WebhookRuntime
    """

    def __init__(self, context_manager: ContextManager):
        self.context_manager = context_manager

    @property
    @abstractmethod
    def node_type(self) -> str:
        """
        Runtime node type.

        Example:
            "http"
            "condition"
        """
        ...

    @abstractmethod
    def execute(
        self,
        node: Any,
        execution: Any,
    ) -> dict[str, Any]:
        """
        Execute the node.

        Returns:
            Dictionary containing runtime output.

        Example:
            {
                "status": 200,
                "body": {...}
            }
        """
        ...

    # ------------------------------------------------------------------
    # Shared Helpers
    # ------------------------------------------------------------------

    def resolve_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """
        Resolve template variables in the node configuration.
        """

        context = self.context_manager.get_context()

        return VariableResolver.resolve(
            config,
            context,
        )

    def save_output(
        self,
        node_id: str,
        output: dict[str, Any],
    ) -> None:
        """
        Save node output into execution context.
        """

        self.context_manager.set_node_output(
            node_id=node_id,
            output=output,
        )

    def get_context(self) -> dict[str, Any]:
        """
        Return the current execution context.
        """

        return self.context_manager.get_context()

    def log(
        self,
        message: str,
    ) -> None:
        """
        Basic runtime logger.

        Can later be replaced by ExecutionLogService.
        """

        print(
            f"[{self.node_type.upper()}] {message}"
        )