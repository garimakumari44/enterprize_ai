"""
OCR Node

Extracts text from images and PDF documents.

Supported Inputs:
- Local file path
- PDF
- Image
- URL (optional)
- Base64 image (optional)

Output:
{
    "text": "...",
    "pages": [...],
    "metadata": {...}
}
"""

from __future__ import annotations

from pathlib import Path

from app.nodes.base.base_node import BaseNode
from app.nodes.base.node_context import NodeContext
from app.nodes.base.node_result import NodeResult
from app.services.ai.ocr_service import OCRService


class OCRNode(BaseNode):
    """
    Optical Character Recognition Node.
    """

    node_type = "ocr"

    def __init__(self) -> None:
        self.ocr_service = OCRService()

    async def execute(self, context: NodeContext) -> NodeResult:
        """
        Execute OCR.
        """

        file_path = context.get_input("file_path")

        if not file_path:
            return NodeResult.failure(
                error="file_path is required."
            )

        if not Path(file_path).exists():
            return NodeResult.failure(
                error=f"File not found: {file_path}"
            )

        provider = context.get_input("provider")
        language = context.get_input("language", "eng")

        result = await self.ocr_service.extract_text(
            file_path=file_path,
            provider=provider,
            language=language,
        )

        return NodeResult.success(
            output={
                "text": result.text,
                "pages": result.pages,
                "metadata": result.metadata,
                "provider": result.provider,
            }
        )