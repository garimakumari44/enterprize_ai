"""
nodes/logic/loop_node.py

Loop node.

Initializes iteration over a collection and controls workflow
execution through the loop body until all items are processed.
"""

from __future__ import annotations

from typing import Any, Iterable

from app.nodes.base.base_node import BaseNode
from app.nodes.base.node_context import NodeContext
from app.nodes.base.node_result import NodeResult
from app.nodes.metadata.node_categories import NodeCategory


class LoopNode(BaseNode):
    """
    Iterates over a collection.

    Output ports:
        loop      -> execute loop body
        completed -> loop finished
    """

    node_type = "loop"
    display_name = "Loop"
    category = NodeCategory.LOGIC

    LOOP_STATE_KEY = "__loop_state__"

    async def execute(self, context: NodeContext) -> NodeResult:
        config = self.config

        collection = self._resolve_collection(
            config.get("collection"),
            context,
        )

        collection = list(collection)

        loop_id = self.id

        state = context.execution_state.setdefault(
            self.LOOP_STATE_KEY,
            {}
        )

        loop_state = state.setdefault(
            loop_id,
            {
                "index": 0,
                "items": collection,
                "total": len(collection),
            },
        )

        index = loop_state["index"]
        total = loop_state["total"]

        # Finished
        if index >= total:
            state.pop(loop_id, None)

            return NodeResult.success(
                output={
                    "completed": True,
                    "total": total,
                },
                next_output="completed",
            )

        current_item = loop_state["items"][index]

        # Expose iteration variables
        context.variables["loop"] = {
            "index": index,
            "item": current_item,
            "first": index == 0,
            "last": index == total - 1,
            "total": total,
        }

        # Increment for next execution
        loop_state["index"] += 1

        return NodeResult.success(
            output={
                "index": index,
                "item": current_item,
                "remaining": total - index - 1,
            },
            next_output="loop",
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _resolve_collection(
        self,
        collection: Any,
        context: NodeContext,
    ) -> Iterable[Any]:
        """
        Resolves the collection to iterate.

        Supports:
            - list
            - tuple
            - set
            - callable
            - Python expression (temporary)
        """

        if collection is None:
            return []

        if callable(collection):
            return collection(context)

        if isinstance(collection, str):
            return self._safe_eval(collection, context)

        if isinstance(collection, Iterable):
            return collection

        return [collection]

    def _safe_eval(
        self,
        expression: str,
        context: NodeContext,
    ) -> Any:
        """
        Temporary expression evaluator.

        Replace with CEL/JSONLogic later.
        """

        try:
            return eval(
                expression,
                {"__builtins__": {}},
                {
                    "variables": context.variables,
                    "inputs": context.inputs,
                },
            )
        except Exception as exc:
            raise ValueError(
                f"Invalid loop expression '{expression}': {exc}"
            ) from exc