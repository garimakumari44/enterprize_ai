"""
Summarization Node

Summarizes input text using an LLM.

Supported summary styles:
- brief
- detailed
- bullet
- executive

Input:
{
    "text": "...",
    "style": "brief",
    "provider": "openai",
    "model": "gpt-5.5",
    "temperature": 0.2,
    "max_tokens": 500
}

Output:
{
    "summary": "...",
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


class SummarizationNode(BaseNode):
    """
    AI Summarization Node.
    """

    node_type = "summarization"

    DEFAULT_SYSTEM_PROMPT = (
        "You are an expert document summarization assistant. "
        "Produce clear, accurate, and concise summaries."
    )

    STYLE_INSTRUCTIONS = {
        "brief": "Summarize the text in one concise paragraph.",
        "detailed": "Provide a detailed summary while preserving all important information.",
        "bullet": "Summarize the text using clear bullet points.",
        "executive": (
            "Create an executive summary highlighting the key findings, "
            "decisions, risks, and recommendations."
        ),
    }

    def __init__(self) -> None:
        self.ai_service = AIService()

    async def execute(self, context: NodeContext) -> NodeResult:
        """
        Execute text summarization.
        """

        text = context.get_input("text")

        if not text:
            return NodeResult.failure(
                error="Input text is required."
            )

        style = context.get_input("style", "brief").lower()

        instruction = self.STYLE_INSTRUCTIONS.get(
            style,
            self.STYLE_INSTRUCTIONS["brief"],
        )

        prompt = (
            f"{instruction}\n\n"
            f"Text:\n"
            f"{text}"
        )

        provider = context.get_input("provider")
        model = context.get_input("model")

        temperature = context.get_input(
            "temperature",
            0.2,
        )

        max_tokens = context.get_input(
            "max_tokens",
            500,
        )

        response = await self.ai_service.generate_text(
            prompt=prompt,
            system_prompt=self.DEFAULT_SYSTEM_PROMPT,
            provider=provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return NodeResult.success(
            output={
                "summary": response.content,
                "provider": response.provider,
                "model": response.model,
                "usage": response.usage,
                "finish_reason": response.finish_reason,
            }
        )