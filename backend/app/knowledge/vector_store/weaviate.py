"""
app/knowledge/vector_store/weaviate.py

Weaviate vector-store implementation.

Responsibilities
----------------
- Store VectorDocument objects.
- Perform semantic similarity search.
- Support metadata filtering.
- Provide provider-independent SearchResult objects.
- Support hybrid search as an optional provider-specific feature.
"""

from __future__ import annotations

import asyncio
from typing import Any

import weaviate
from weaviate.classes.query import (
    Filter,
    MetadataQuery,
)

from .base import (
    SearchResult,
    VectorDocument,
    VectorStore,
)


class WeaviateVectorStore(VectorStore):
    """
    Weaviate implementation of VectorStore.
    """

    def __init__(
        self,
        url: str,
        api_key: str | None = None,
        collection_name: str = "Documents",
    ) -> None:

        self.url = url
        self.collection_name = collection_name

        if api_key:

            self.client = (
                weaviate.connect_to_weaviate_cloud(
                    cluster_url=url,
                    auth_credentials=(
                        weaviate.auth.AuthApiKey(
                            api_key
                        )
                    ),
                )
            )

        else:

            self.client = (
                weaviate.connect_to_local(
                    host=url
                )
            )

        self._create_collection()

    # ==========================================================
    # Collection
    # ==========================================================

    def _create_collection(self) -> None:

        existing = (
            self.client.collections.list_all()
        )

        if self.collection_name in existing:
            return

        self.client.collections.create(
            name=self.collection_name,
            properties=[
                {
                    "name": "content",
                    "dataType": ["text"],
                },
                {
                    "name": "document_id",
                    "dataType": ["text"],
                },
                {
                    "name": "metadata",
                    "dataType": ["object"],
                },
            ],
            vector_config=None,
        )

    def get_collection(self):

        return self.client.collections.get(
            self.collection_name
        )

    async def create_collection(
        self,
        collection_name: str,
        dimension: int,
    ) -> None:

        # Weaviate collection schema is normally configured
        # during initialization.
        #
        # The dimension is controlled by the external vector
        # supplied to the collection rather than a VECTOR(n)
        # declaration like PostgreSQL.

        if collection_name != self.collection_name:

            self.collection_name = collection_name

            await asyncio.to_thread(
                self._create_collection
            )

    # ==========================================================
    # Delete Collection
    # ==========================================================

    async def delete_collection(
        self,
        collection_name: str,
    ) -> None:

        self.client.collections.delete(
            collection_name
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

        collection = self.get_collection()

        def _insert() -> None:

            with collection.batch.dynamic() as batch:

                for document in documents:

                    batch.add_object(
                        uuid=document.id,
                        properties={
                            "content": (
                                document.content
                            ),
                            "document_id": (
                                document.id
                            ),
                            "metadata": (
                                document.metadata
                            ),
                        },
                        vector=document.vector,
                    )

        await asyncio.to_thread(
            _insert
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

        collection = self.get_collection()

        query_filter = (
            self._build_filter(filters)
            if filters
            else None
        )

        def _search():

            return collection.query.near_vector(
                near_vector=vector,
                limit=limit,
                filters=query_filter,
                return_metadata=MetadataQuery(
                    distance=True
                ),
            )

        response = await asyncio.to_thread(
            _search
        )

        results: list[SearchResult] = []

        for item in response.objects:

            properties = (
                item.properties or {}
            )

            distance = 0.0

            if item.metadata:
                distance = float(
                    item.metadata.distance
                    or 0.0
                )

            results.append(
                SearchResult(
                    id=str(item.uuid),
                    content=str(
                        properties.get(
                            "content",
                            "",
                        )
                    ),
                    metadata=properties.get(
                        "metadata",
                        {},
                    ) or {},
                    score=1.0 - distance,
                )
            )

        return results

    # ==========================================================
    # Optional Hybrid Search
    # ==========================================================

    async def hybrid_search(
        self,
        query: str,
        query_vector: list[float],
        alpha: float = 0.5,
        top_k: int = 5,
    ) -> list[SearchResult]:

        collection = self.get_collection()

        def _search():

            return collection.query.hybrid(
                query=query,
                vector=query_vector,
                alpha=alpha,
                limit=top_k,
                return_metadata=MetadataQuery(
                    score=True
                ),
            )

        response = await asyncio.to_thread(
            _search
        )

        results: list[SearchResult] = []

        for item in response.objects:

            properties = (
                item.properties or {}
            )

            score = 0.0

            if item.metadata:
                score = float(
                    item.metadata.score
                    or 0.0
                )

            results.append(
                SearchResult(
                    id=str(item.uuid),
                    content=str(
                        properties.get(
                            "content",
                            "",
                        )
                    ),
                    metadata=properties.get(
                        "metadata",
                        {},
                    ) or {},
                    score=score,
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

        collection = self.get_collection()

        def _delete() -> None:

            for document_id in ids:

                try:

                    collection.data.delete_by_id(
                        document_id
                    )

                except Exception:
                    continue

        await asyncio.to_thread(
            _delete
        )

    # ==========================================================
    # Count
    # ==========================================================

    async def count(
        self,
        collection_name: str,
    ) -> int:

        collection = self.get_collection()

        def _count() -> int:

            response = (
                collection.aggregate.over_all()
            )

            return int(
                response.total_count
            )

        return await asyncio.to_thread(
            _count
        )

    # ==========================================================
    # Health
    # ==========================================================

    async def health_check(
        self,
    ) -> dict[str, Any]:

        try:

            ready = await asyncio.to_thread(
                self.client.is_ready
            )

            if ready:

                return {
                    "status": "healthy",
                    "provider": "weaviate",
                    "collection": (
                        self.collection_name
                    ),
                }

            return {
                "status": "unhealthy",
                "provider": "weaviate",
            }

        except Exception as exc:

            return {
                "status": "unhealthy",
                "provider": "weaviate",
                "error": str(exc),
            }

    # ==========================================================
    # Close
    # ==========================================================

    async def close(self) -> None:

        await asyncio.to_thread(
            self.client.close
        )

    # ==========================================================
    # Helpers
    # ==========================================================

    @staticmethod
    def _build_filter(
        filters: dict[str, Any],
    ) -> Any:

        conditions = []

        for key, value in filters.items():

            conditions.append(
                Filter.by_property(
                    f"metadata.{key}"
                ).equal(
                    value
                )
            )

        if not conditions:
            return None

        current = conditions[0]

        for condition in conditions[1:]:
            current = current & condition

        return current


__all__ = [
    "WeaviateVectorStore",
]