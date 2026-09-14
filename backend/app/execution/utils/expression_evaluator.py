"""
Expression Evaluator

Safely evaluates conditional expressions used by
Condition Nodes.

Examples:
    user.age >= 18
    http.status == 200
    amount > 1000 and approved
"""

from __future__ import annotations

import ast
import operator
from typing import Any


class ExpressionEvaluator:
    """
    Safe expression evaluator.

    Supports:
    - == != > >= < <=
    - and
    - or
    - not
    - arithmetic (+ - * / %)
    - parentheses
    - nested variables
    """

    OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Mod: operator.mod,

        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,

        ast.And: lambda a, b: a and b,
        ast.Or: lambda a, b: a or b,

        ast.USub: operator.neg,
        ast.Not: operator.not_,
    }

    @classmethod
    def evaluate(cls, expression: str, context: dict[str, Any]) -> bool:
        """
        Evaluate an expression.

        Args:
            expression: Expression string.
            context: Execution variables.

        Returns:
            Boolean result.
        """

        tree = ast.parse(expression, mode="eval")
        result = cls._eval(tree.body, context)
        return bool(result)

    @classmethod
    def _eval(cls, node: ast.AST, context: dict[str, Any]) -> Any:

        if isinstance(node, ast.Constant):
            return node.value

        if isinstance(node, ast.Name):
            return context.get(node.id)

        if isinstance(node, ast.Attribute):
            value = cls._eval(node.value, context)

            if isinstance(value, dict):
                return value.get(node.attr)

            return getattr(value, node.attr, None)

        if isinstance(node, ast.BinOp):
            left = cls._eval(node.left, context)
            right = cls._eval(node.right, context)

            return cls.OPERATORS[type(node.op)](left, right)

        if isinstance(node, ast.UnaryOp):
            operand = cls._eval(node.operand, context)
            return cls.OPERATORS[type(node.op)](operand)

        if isinstance(node, ast.BoolOp):

            values = [
                cls._eval(v, context)
                for v in node.values
            ]

            result = values[0]

            for value in values[1:]:
                result = cls.OPERATORS[type(node.op)](result, value)

            return result

        if isinstance(node, ast.Compare):

            left = cls._eval(node.left, context)

            for op, comparator in zip(node.ops, node.comparators):

                right = cls._eval(comparator, context)

                if not cls.OPERATORS[type(op)](left, right):
                    return False

                left = right

            return True

        raise ValueError(
            f"Unsupported expression: {ast.dump(node)}"
        )