"""
Classification Node

Classifies input text into one of the provided categories.

Example Input:
{
    "text": "The customer wants a refund for the damaged product.",
    "labels": [
        "Sales",
        "Support",
        "Billing",
        "Refund"
    ],
    "provider": "openai",
    "model": "gpt-5.5",
    "temperature": 0.0
}

Example Output:
{
    "label": "Refund",
    "reasoning": "The text explicitly requests a refund.",
    "provider": "openai",
    "model": "gpt-5.5",
    "usage": {...},
    "finish_reason": "stop"
}
"""

from __future__ import annotations

from app.nodes.base.base_node import BaseNode
from app.nodes.base.node_context import NodeContext
from app.nodes.base.node_result import NodeResult
from app.services.ai.ai_service import AIService


class ClassificationNode(BaseNode):
    """
    AI Classification Node.
    """

    node_type = "classification"

    SYSTEM_PROMPT = """
You are an expert text classifier.

Return ONLY valid JSON.

Format:
{
    "label": "...",
    "reasoning": "..."
}

Choose exactly one label from the provided list.
"""

    def __init__(self) -> None:
        self.ai_service = AIService()

    async def execute(self, context: NodeContext) -> NodeResult:

        text = context.get_input("text")

        if not text:
            return NodeResult.failure(
                error="Input text is required."
            )

        labels = context.get_input("labels")

        if not labels:
            return NodeResult.failure(
                error="Classification labels are required."
            )

        if not isinstance(labels, list):
            return NodeResult.failure(
                error="Labels must be a list."
            )

        prompt = f"""
Classify the following text.

Available Labels:
{chr(10).join(f"- {label}" for label in labels)}

Text:
{text}
"""

        provider = context.get_input("provider")
        model = context.get_input("model")

        temperature = context.get_input(
            "temperature",
            0.0,
        )

        max_tokens = context.get_input(
            "max_tokens",
            200,
        )

        response = await self.ai_service.generate_json(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPT,
            provider=provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return NodeResult.success(
            output={
                "label": response.content.get("label"),
                "reasoning": response.content.get("reasoning"),
                "provider": response.provider,
                "model": response.model,
                "usage": response.usage,
                "finish_reason": response.finish_reason,
            }
        )