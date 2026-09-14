"""
Execution Context Manager.

Maintains runtime state during workflow execution.
"""

from __future__ import annotations

from typing import Any


class ContextManager:
    """
    Stores execution context during workflow runtime.
    """

    def __init__(
        self,
        execution_id: int,
        workflow_id: int,
        inputs: dict[str, Any] | None = None,
        secrets: dict[str, Any] | None = None,
    ) -> None:
        self.execution_id = execution_id
        self.workflow_id = workflow_id

        self.inputs: dict[str, Any] = inputs or {}
        self.secrets: dict[str, Any] = secrets or {}

        self.variables: dict[str, Any] = {}
        self.node_outputs: dict[str, Any] = {}
        self.metadata: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Variables
    # ------------------------------------------------------------------

    def set_variable(self, key: str, value: Any) -> None:
        """Store a workflow variable."""
        self.variables[key] = value

    def get_variable(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """Retrieve a workflow variable."""
        return self.variables.get(key, default)

    # ------------------------------------------------------------------
    # Node Outputs
    # ------------------------------------------------------------------

    def set_node_output(
        self,
        node_id: str,
        output: Any,
    ) -> None:
        """Store a node's execution output."""
        self.node_outputs[node_id] = output

    def get_node_output(
        self,
        node_id: str,
        default: Any = None,
    ) -> Any:
        """Retrieve a node's output."""
        return self.node_outputs.get(node_id, default)

    # ------------------------------------------------------------------
    # Inputs
    # ------------------------------------------------------------------

    def get_input(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """Retrieve workflow input."""
        return self.inputs.get(key, default)

    # ------------------------------------------------------------------
    # Secrets
    # ------------------------------------------------------------------

    def get_secret(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """Retrieve workflow secret."""
        return self.secrets.get(key, default)

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def set_metadata(
        self,
        key: str,
        value: Any,
    ) -> None:
        """Store execution metadata."""
        self.metadata[key] = value

    def get_metadata(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """Retrieve execution metadata."""
        return self.metadata.get(key, default)

    # ------------------------------------------------------------------
    # Snapshot
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize the current execution context.
        """

        return {
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "inputs": self.inputs,
            "variables": self.variables,
            "node_outputs": self.node_outputs,
            "metadata": self.metadata,
        }