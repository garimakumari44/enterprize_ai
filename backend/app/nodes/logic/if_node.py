"""
nodes/logic/if_node.py

Conditional branching node.

Routes workflow execution to either the "true" or "false" output
based on evaluation of a condition.
"""

from __future__ import annotations

from typing import Any

from app.nodes.base.base_node import BaseNode
from app.nodes.base.node_context import NodeContext
from app.nodes.base.node_result import NodeResult
from app.nodes.metadata.node_categories import NodeCategory


class IfNode(BaseNode):
    """
    Conditional workflow node.

    Outputs:
        true
        false
    """

    node_type = "if"
    category = NodeCategory.LOGIC
    display_name = "If"

    async def execute(self, context: NodeContext) -> NodeResult:
        """
        Evaluate condition and choose branch.
        """

        config = self.config

        condition = config.get("condition")

        result = self._evaluate_condition(
            condition=condition,
            variables=context.variables,
            inputs=context.inputs,
        )

        return NodeResult.success(
            output={
                "condition": result,
            },
            next_output="true" if result else "false",
        )

    # ---------------------------------------------------------
    # Internal Helpers
    # ---------------------------------------------------------

    def _evaluate_condition(
        self,
        condition: Any,
        variables: dict,
        inputs: dict,
    ) -> bool:
        """
        Evaluates a workflow condition.

        Currently supports:

        - bool
        - callable
        - python expression (string)

        Future:
            - JSONLogic
            - JMESPath
            - CEL
            - Rule Engine
        """

        if condition is None:
            return False

        if isinstance(condition, bool):
            return condition

        if callable(condition):
            return bool(condition(variables, inputs))

        if isinstance(condition, str):
            return self._safe_eval(
                expression=condition,
                variables=variables,
                inputs=inputs,
            )

        return bool(condition)

    def _safe_eval(
        self,
        expression: str,
        variables: dict,
        inputs: dict,
    ) -> bool:
        """
        Very small safe evaluator.

        Example:

            variables["score"] > 80

            inputs["status"] == "approved"
        """

        allowed_globals = {
            "__builtins__": {},
        }

        allowed_locals = {
            "variables": variables,
            "inputs": inputs,
        }

        try:
            value = eval(expression, allowed_globals, allowed_locals)
            return bool(value)
        except Exception as exc:
            raise ValueError(
                f"Failed to evaluate condition '{expression}': {exc}"
            ) from exc