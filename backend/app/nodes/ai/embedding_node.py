"""
Embedding Node

Generates vector embeddings from text.

Typical uses:
- Semantic Search
- RAG
- Vector Database Storage
- Similarity Search
- Clustering
- Recommendation Systems

Example Input:
{
    "text": "Artificial Intelligence is transforming healthcare.",
    "provider": "openai",
    "model": "text-embedding-3-small"
}

Example Output:
{
    "embedding": [...],
    "dimensions": 1536,
    "provider": "openai",
    "model": "text-embedding-3-small",
    "usage": {...}
}
"""

from __future__ import annotations

from app.nodes.base.base_node import BaseNode
from app.nodes.base.node_context import NodeContext
from app.nodes.base.node_result import NodeResult
from app.services.ai.embedding_service import EmbeddingService


class EmbeddingNode(BaseNode):
    """
    AI Embedding Node.
    """

    node_type = "embedding"

    def __init__(self) -> None:
        self.embedding_service = EmbeddingService()

    async def execute(self, context: NodeContext) -> NodeResult:
        """
        Generate vector embeddings.
        """

        text = context.get_input("text")

        if not text:
            return NodeResult.failure(
                error="Input text is required."
            )

        provider = context.get_input("provider")
        model = context.get_input("model")

        response = await self.embedding_service.generate_embedding(
            text=text,
            provider=provider,
            model=model,
        )

        return NodeResult.success(
            output={
                "embedding": response.embedding,
                "dimensions": len(response.embedding),
                "provider": response.provider,
                "model": response.model,
                "usage": response.usage,
            }
        )