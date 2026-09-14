"""
app/knowledge/vector_store/qdrant.py

Qdrant vector-store implementation.

Responsibilities
----------------
- Store VectorDocument objects in Qdrant.
- Perform semantic similarity search.
- Support metadata filtering.
- Delete vectors by ID.
- Expose provider-independent SearchResult objects.

The provider implements the common VectorStore contract.
"""

from __future__ import annotations

from typing import Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from .base import (
    SearchResult,
    VectorDocument,
    VectorStore,
)


class QdrantVectorStore(VectorStore):
    """
    Qdrant implementation of VectorStore.
    """

    def __init__(
        self,
        url: str,
        api_key: str | None = None,
    ) -> None:

        self.client = AsyncQdrantClient(
            url=url,
            api_key=api_key,
        )

    # ==========================================================
    # Collection
    # ==========================================================

    async def create_collection(
        self,
        collection_name: str,
        dimension: int,
    ) -> None:

        if dimension <= 0:
            raise ValueError(
                "Vector dimension must be greater than zero."
            )

        collections = (
            await self.client.get_collections()
        )

        existing_names = {
            collection.name
            for collection in collections.collections
        }

        if collection_name in existing_names:
            return

        await self.client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=dimension,
                distance=Distance.COSINE,
            ),
        )

    # ==========================================================
    # Delete Collection
    # ==========================================================

    async def delete_collection(
        self,
        collection_name: str,
    ) -> None:

        await self.client.delete_collection(
            collection_name=collection_name,
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

        points: list[PointStruct] = []

        for document in documents:

            points.append(
                PointStruct(
                    id=document.id,
                    vector=document.vector,
                    payload={
                        "content": document.content,
                        "metadata": document.metadata,
                    },
                )
            )

        await self.client.upsert(
            collection_name=collection_name,
            points=points,
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

        query_filter = self._build_filter(
            filters
        )

        response = await self.client.query_points(
            collection_name=collection_name,
            query=vector,
            limit=limit,
            query_filter=query_filter,
            with_payload=True,
        )

        results: list[SearchResult] = []

        for point in response.points:

            payload = point.payload or {}

            results.append(
                SearchResult(
                    id=str(point.id),
                    content=str(
                        payload.get(
                            "content",
                            "",
                        )
                    ),
                    metadata=payload.get(
                        "metadata",
                        {},
                    ) or {},
                    score=float(
                        point.score
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

        await self.client.delete(
            collection_name=collection_name,
            points_selector=ids,
        )

    # ==========================================================
    # Count
    # ==========================================================

    async def count(
        self,
        collection_name: str,
    ) -> int:

        result = await self.client.count(
            collection_name=collection_name,
            exact=True,
        )

        return int(result.count)

    # ==========================================================
    # Health
    # ==========================================================

    async def health_check(
        self,
    ) -> dict[str, Any]:

        try:

            await self.client.get_collections()

            return {
                "status": "healthy",
                "provider": "qdrant",
            }

        except Exception as exc:

            return {
                "status": "unhealthy",
                "provider": "qdrant",
                "error": str(exc),
            }

    # ==========================================================
    # Close
    # ==========================================================

    async def close(self) -> None:

        await self.client.close()

    # ==========================================================
    # Helpers
    # ==========================================================

    @staticmethod
    def _build_filter(
        filters: dict[str, Any] | None,
    ) -> Filter | None:

        if not filters:
            return None

        conditions: list[FieldCondition] = []

        for key, value in filters.items():

            conditions.append(
                FieldCondition(
                    key=f"metadata.{key}",
                    match=MatchValue(
                        value=value
                    ),
                )
            )

        if not conditions:
            return None

        return Filter(
            must=conditions
        )


__all__ = [
    "QdrantVectorStore",
]