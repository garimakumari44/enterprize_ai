"""
nodes/logic/switch_node.py

Multi-branch conditional node.

Routes workflow execution to one of several outputs based on the
evaluated value of an expression.
"""

from __future__ import annotations

from typing import Any

from app.nodes.base.base_node import BaseNode
from app.nodes.base.node_context import NodeContext
from app.nodes.base.node_result import NodeResult
from app.nodes.metadata.node_categories import NodeCategory


class SwitchNode(BaseNode):
    """
    Multi-branch workflow node.

    Example configuration:

    {
        "expression": "variables['status']",
        "cases": {
            "approved": "approved",
            "rejected": "rejected",
            "pending": "pending"
        },
        "default": "unknown"
    }

    Output ports:
        approved
        rejected
        pending
        unknown
    """

    node_type = "switch"
    display_name = "Switch"
    category = NodeCategory.LOGIC

    async def execute(self, context: NodeContext) -> NodeResult:
        config = self.config

        expression = config.get("expression")
        cases = config.get("cases", {})
        default_output = config.get("default", "default")

        value = self._evaluate_expression(
            expression=expression,
            variables=context.variables,
            inputs=context.inputs,
        )

        next_output = cases.get(str(value), default_output)

        return NodeResult.success(
            output={
                "value": value,
                "matched": next_output != default_output,
            },
            next_output=next_output,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _evaluate_expression(
        self,
        expression: Any,
        variables: dict,
        inputs: dict,
    ) -> Any:
        """
        Evaluates a switch expression.

        Supported:
            - literal values
            - callable
            - python expression (temporary)
        """

        if expression is None:
            return None

        if callable(expression):
            return expression(variables, inputs)

        if isinstance(expression, str):
            return self._safe_eval(
                expression,
                variables,
                inputs,
            )

        return expression

    def _safe_eval(
        self,
        expression: str,
        variables: dict,
        inputs: dict,
    ) -> Any:
        """
        Temporary expression evaluator.

        Replace with CEL / JSONLogic in production.
        """

        try:
            return eval(
                expression,
                {"__builtins__": {}},
                {
                    "variables": variables,
                    "inputs": inputs,
                },
            )
        except Exception as exc:
            raise ValueError(
                f"Failed to evaluate switch expression '{expression}': {exc}"
            ) from exc