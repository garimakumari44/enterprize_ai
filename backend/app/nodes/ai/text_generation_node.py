"""
Text Generation Node

Generates text using an LLM.

This node is intended for single-turn generation tasks such as:
- Summarization
- Translation
- Content generation
- Rewriting
- Classification
- Extraction

Input:
{
    "prompt": "...",
    "system_prompt": "...",
    "provider": "openai",
    "model": "gpt-5.5",
    "temperature": 0.7,
    "max_tokens": 1000
}

Output:
{
    "text": "...",
    "provider": "...",
    "model": "...",
    "usage": {...},
    "finish_reason": "stop"
}
"""

from __future__ import annotations

from app.nodes.base.base_node import BaseNode
from app.nodes.base.node_context import NodeContext
from app.nodes.base.node_result import NodeResult
from app.services.ai.ai_service import AIService


class TextGenerationNode(BaseNode):
    """
    AI Text Generation Node.
    """

    node_type = "text_generation"

    def __init__(self) -> None:
        self.ai_service = AIService()

    async def execute(self, context: NodeContext) -> NodeResult:
        """
        Generate text from a prompt.
        """

        prompt = context.get_input("prompt")

        if not prompt:
            return NodeResult.failure(
                error="Prompt is required."
            )

        system_prompt = context.get_input("system_prompt")

        provider = context.get_input("provider")
        model = context.get_input("model")

        temperature = context.get_input(
            "temperature",
            0.7,
        )

        max_tokens = context.get_input(
            "max_tokens",
            1000,
        )

        response = await self.ai_service.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            provider=provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return NodeResult.success(
            output={
                "text": response.content,
                "provider": response.provider,
                "model": response.model,
                "usage": response.usage,
                "finish_reason": response.finish_reason,
            }
        )