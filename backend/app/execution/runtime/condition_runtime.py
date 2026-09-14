"""
Condition Runtime

Evaluates conditional expressions and determines the
execution path.
"""

from __future__ import annotations

from typing import Any

from app.execution.runtime.base_runtime import BaseRuntime
from app.execution.utils.expression_evaluator import ExpressionEvaluator


class ConditionRuntime(BaseRuntime):
    """
    Runtime for Condition nodes.

    Expected node.config:

    {
        "expression": "user.age >= 18 and amount > 1000"
    }
    """

    @property
    def node_type(self) -> str:
        return "condition"

    def execute(
        self,
        node: Any,
        execution: Any,
    ) -> dict[str, Any]:
        """
        Execute the condition node.

        Returns:
            {
                "result": True
            }

        or

            {
                "result": False
            }
        """

        # Resolve template variables
        config = self.resolve_config(node.config)

        expression = config.get("expression")

        if not expression:
            raise ValueError(
                "Condition node requires an 'expression'."
            )

        self.log(f"Evaluating: {expression}")

        context = self.get_context()

        result = ExpressionEvaluator.evaluate(
            expression=expression,
            context=context,
        )

        output = {
            "result": result,
        }

        # Save result into execution context
        self.save_output(
            node_id=str(node.id),
            output=output,
        )

        self.log(f"Condition result: {result}")

        return output