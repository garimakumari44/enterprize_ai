"""
Vision Node

Analyzes one or more images using a multimodal AI model.

Supported Tasks:
- Image description
- Visual question answering
- Chart analysis
- Screenshot analysis
- UI analysis
- Document understanding
- Scene understanding

Input:
{
    "images": [
        "/tmp/image1.png",
        "/tmp/chart.png"
    ],
    "prompt": "Explain what this chart shows.",
    "provider": "openai",
    "model": "gpt-5.5"
}

Output:
{
    "response": "...",
    "provider": "...",
    "model": "...",
    "usage": {...},
    "finish_reason": "stop"
}
"""

from __future__ import annotations

from pathlib import Path

from app.nodes.base.base_node import BaseNode
from app.nodes.base.node_context import NodeContext
from app.nodes.base.node_result import NodeResult
from app.services.ai.vision_service import VisionService


class VisionNode(BaseNode):
    """
    Multimodal Vision Node.
    """

    node_type = "vision"

    DEFAULT_PROMPT = (
        "Analyze the provided image and describe its contents."
    )

    def __init__(self) -> None:
        self.vision_service = VisionService()

    async def execute(self, context: NodeContext) -> NodeResult:
        """
        Execute image analysis.
        """

        images = context.get_input("images")

        if not images:
            return NodeResult.failure(
                error="At least one image is required."
            )

        if isinstance(images, str):
            images = [images]

        validated_images: list[str] = []

        for image in images:
            if not Path(image).exists():
                return NodeResult.failure(
                    error=f"Image not found: {image}"
                )
            validated_images.append(image)

        prompt = context.get_input(
            "prompt",
            self.DEFAULT_PROMPT,
        )

        provider = context.get_input("provider")
        model = context.get_input("model")

        temperature = context.get_input(
            "temperature",
            0.2,
        )

        max_tokens = context.get_input(
            "max_tokens",
            1000,
        )

        response = await self.vision_service.analyze(
            images=validated_images,
            prompt=prompt,
            provider=provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return NodeResult.success(
            output={
                "response": response.content,
                "provider": response.provider,
                "model": response.model,
                "usage": response.usage,
                "finish_reason": response.finish_reason,
            }
        )