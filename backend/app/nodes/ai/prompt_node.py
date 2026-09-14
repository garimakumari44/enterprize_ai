"""
Prompt Node

Responsible for rendering prompts from templates.

This node does NOT call any AI provider.
It only prepares the prompt.

Example:

Template:
    Summarize the following text:

    {{text}}

Input:
{
    "text": "Artificial Intelligence is transforming..."
}

Output:
{
    "prompt": "Summarize the following text:\n\nArtificial Intelligence is transforming..."
}
"""

from __future__ import annotations

from typing import Any

from app.nodes.base.base_node import BaseNode
from app.nodes.base.node_context import NodeContext
from app.nodes.base.node_result import NodeResult
from app.prompts.prompt_renderer import PromptRenderer


class PromptNode(BaseNode):
    """
    Workflow Prompt Node.
    """

    node_type = "prompt"

    def __init__(self):
        self.renderer = PromptRenderer()

    async def execute(self, context: NodeContext) -> NodeResult:
        """
        Render a prompt using workflow inputs.
        """

        template: str = context.get_input("template", "")
        variables: dict[str, Any] = context.get_input("variables", {})

        prompt = self.renderer.render(
            template=template,
            variables=variables,
        )

        return NodeResult.success(
            output={
                "prompt": prompt,
            }
        )