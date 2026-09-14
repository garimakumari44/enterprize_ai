"""
app/knowledge/vector_store/pinecone.py

Pinecone vector-store implementation.

Responsibilities
----------------
- Store VectorDocument objects in Pinecone.
- Perform semantic similarity search.
- Support metadata filtering.
- Delete vectors by ID.
- Expose provider-independent SearchResult objects.
"""

from __future__ import annotations

import asyncio
from typing import Any

from pinecone import Pinecone, ServerlessSpec

from app.core.config import settings

from .base import (
    SearchResult,
    VectorDocument,
    VectorStore,
)


class PineconeVectorStore(VectorStore):
    """
    Pinecone implementation of VectorStore.
    """

    def __init__(
        self,
        index_name: str,
        dimension: int,
        metric: str = "cosine",
    ) -> None:

        if dimension <= 0:
            raise ValueError(
                "Vector dimension must be greater than zero."
            )

        self.index_name = index_name
        self.dimension = dimension
        self.metric = metric

        self.client = Pinecone(
            api_key=settings.PINECONE_API_KEY
        )

        self._create_index()

        self.index = self.client.Index(
            self.index_name
        )

    # ==========================================================
    # Collection
    # ==========================================================

    async def create_collection(
        self,
        collection_name: str,
        dimension: int,
    ) -> None:

        # Pinecone uses indexes rather than collections.
        #
        # If the requested collection name is different
        # from the configured index, create/use that index.

        if dimension <= 0:
            raise ValueError(
                "Vector dimension must be greater than zero."
            )

        if collection_name != self.index_name:
            self.index_name = collection_name
            self.dimension = dimension

            await asyncio.to_thread(
                self._create_index
            )

            self.index = self.client.Index(
                self.index_name
            )

    # ==========================================================
    # Delete Collection
    # ==========================================================

    async def delete_collection(
        self,
        collection_name: str,
    ) -> None:

        await asyncio.to_thread(
            self.client.delete_index,
            collection_name,
        )

    # ==========================================================
    # Add / Upsert Documents
    # ==========================================================

    async def add_documents(
        self,
        collection_name: str,
        documents: list[VectorDocument],
    ) -> None:

        if not documents:
            return

        vectors = []

        for document in documents:

            metadata = dict(
                document.metadata
            )

            metadata["content"] = (
                document.content
            )

            vectors.append(
                {
                    "id": document.id,
                    "values": document.vector,
                    "metadata": metadata,
                }
            )

        await asyncio.to_thread(
            self.index.upsert,
            vectors=vectors,
        )

    # ==========================================================
    # Similarity Search
    # ==========================================================

    async def similarity_search(
        self,
        collection_name: str,
        vector: list[float],
        limit: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:

        if limit <= 0:
            return []

        result = await asyncio.to_thread(
            self.index.query,
            vector=vector,
            top_k=limit,
            include_metadata=True,
            filter=filters,
        )

        matches = getattr(
            result,
            "matches",
            [],
        )

        results: list[SearchResult] = []

        for match in matches:

            metadata = getattr(
                match,
                "metadata",
                None,
            ) or {}

            content = str(
                metadata.pop(
                    "content",
                    "",
                )
            )

            results.append(
                SearchResult(
                    id=str(match.id),
                    content=content,
                    metadata=metadata,
                    score=float(
                        match.score
                    ),
                )
            )

        return results

    # ==========================================================
    # Delete Documents
    # ==========================================================

    async def delete_documents(
        self,
        collection_name: str,
        ids: list[str],
    ) -> None:

        if not ids:
            return

        await asyncio.to_thread(
            self.index.delete,
            ids=ids,
        )

    # ==========================================================
    # Count
    # ==========================================================

    async def count(
        self,
        collection_name: str,
    ) -> int:

        stats = await asyncio.to_thread(
            self.index.describe_index_stats
        )

        return int(
            getattr(
                stats,
                "total_vector_count",
                0,
            )
        )

    # ==========================================================
    # Health
    # ==========================================================

    async def health_check(
        self,
    ) -> dict[str, Any]:

        try:

            await asyncio.to_thread(
                self.client.describe_index,
                self.index_name,
            )

            return {
                "status": "healthy",
                "provider": "pinecone",
                "index": self.index_name,
            }

        except Exception as exc:

            return {
                "status": "unhealthy",
                "provider": "pinecone",
                "error": str(exc),
            }

    # ==========================================================
    # Close
    # ==========================================================

    async def close(self) -> None:
        """
        Pinecone client does not currently require
        explicit async cleanup.
        """
        return None

    # ==========================================================
    # Helpers
    # ==========================================================

    def _create_index(self) -> None:

        existing_indexes = [
            index.name
            for index in self.client.list_indexes()
        ]

        if self.index_name in existing_indexes:
            return

        self.client.create_index(
            name=self.index_name,
            dimension=self.dimension,
            metric=self.metric,
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1",
            ),
        )


__all__ = [
    "PineconeVectorStore",
]