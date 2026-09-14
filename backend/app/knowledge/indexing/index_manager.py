"""
app/knowledge/indexing/index_manager.py

Central indexing controller.

Responsibilities
----------------
- Coordinate vector indexing through VectorStoreManager.
- Create collections when required.
- Upsert document vectors.
- Search indexed vectors.
- Delete indexed vectors.
- Delete vectors by metadata.
- Retrieve document vectors.
- Expose vector-store health and statistics.

This module does NOT:
- create embedding models
- generate embeddings
- access PostgreSQL directly
- know pgvector implementation details
"""

from __future__ import annotations

from typing import Any

from app.knowledge.vector_store.base import (
    SearchResult,
    VectorDocument,
)
from app.knowledge.vector_store.vector_manager import (
    VectorStoreManager,
)


DEFAULT_COLLECTION = "document_chunks"


class IndexManager:
    """
    Application-level controller for vector indexing.

    Architecture:

        IndexingService
              |
              v
        IndexManager
              |
              v
        VectorStoreManager
              |
              v
        PGVectorStore
    """

    def __init__(
        self,
        vector_store: VectorStoreManager,
        collection_name: str = DEFAULT_COLLECTION,
        dimension: int | None = None,
    ) -> None:

        self.vector_store = vector_store
        self.collection_name = collection_name
        self.dimension = dimension

    # ========================================================================
    # COLLECTION
    # ========================================================================

    async def ensure_collection(
        self,
        dimension: int | None = None,
    ) -> Any:
        """
        Ensure the configured vector collection exists.
        """

        resolved_dimension = (
            dimension
            if dimension is not None
            else self.dimension
        )

        if resolved_dimension is None:
            raise ValueError(
                "Vector dimension is required to "
                "create the index collection."
            )

        if resolved_dimension <= 0:
            raise ValueError(
                "Vector dimension must be greater than zero."
            )

        self.dimension = resolved_dimension

        return await self.vector_store.create_collection(
            collection_name=self.collection_name,
            dimension=resolved_dimension,
        )

    async def create_index(
        self,
        name: str | None = None,
        dimension: int | None = None,
    ) -> Any:
        """
        Backward-compatible/public indexing API.

        Used by IndexingService:

            await index_manager.create_index(
                name="document_chunks",
                dimension=1536,
            )
        """

        if name is not None:
            self.collection_name = name

        return await self.ensure_collection(
            dimension=dimension
        )

    async def delete_collection(self) -> Any:
        """
        Delete the configured vector collection.
        """

        return await self.vector_store.delete_collection(
            collection_name=self.collection_name,
        )

    # ========================================================================
    # INDEXING
    # ========================================================================

    async def index(
        self,
        documents: list[VectorDocument],
    ) -> Any:
        """
        Add vector documents to the configured collection.
        """

        if not documents:
            return {
                "indexed": 0,
            }

        return await self.vector_store.add_documents(
            collection_name=self.collection_name,
            documents=documents,
        )

    async def add_documents(
        self,
        documents: list[VectorDocument],
    ) -> Any:
        """
        Alias for index().
        """

        return await self.index(
            documents
        )

    async def upsert(
        self,
        documents: list[VectorDocument],
    ) -> Any:
        """
        Upsert vector documents.
        """

        if not documents:
            return {
                "indexed": 0,
            }

        return await self.vector_store.upsert(
            collection_name=self.collection_name,
            documents=documents,
        )

    async def update_index(
        self,
        name: str | None = None,
        chunks: list[VectorDocument] | None = None,
    ) -> Any:
        """
        Public indexing API used by IndexingService.

        Example:

            await index_manager.update_index(
                name="document_chunks",
                chunks=vector_documents,
            )
        """

        if name is not None:
            self.collection_name = name

        if not chunks:
            return {
                "indexed": 0,
            }

        # --------------------------------------------------------------------
        # Automatically determine dimension when not already configured.
        # --------------------------------------------------------------------

        if self.dimension is None:

            first_vector = chunks[0].vector

            if not first_vector:
                raise ValueError(
                    "Cannot determine vector dimension from "
                    "an empty vector."
                )

            self.dimension = len(
                first_vector
            )

        # --------------------------------------------------------------------
        # Ensure collection exists.
        # --------------------------------------------------------------------

        await self.ensure_collection(
            dimension=self.dimension
        )

        # --------------------------------------------------------------------
        # Upsert vectors.
        # --------------------------------------------------------------------

        return await self.vector_store.upsert(
            collection_name=self.collection_name,
            documents=chunks,
        )

    # ========================================================================
    # SEARCH
    # ========================================================================

    async def search(
        self,
        vector: list[float],
        limit: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """
        Perform vector similarity search.
        """

        if not vector:
            return []

        if limit <= 0:
            raise ValueError(
                "Search limit must be greater than zero."
            )

        return await self.vector_store.search(
            collection_name=self.collection_name,
            vector=vector,
            limit=limit,
            filters=filters,
        )

    async def similarity_search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """
        Explicit similarity-search API.
        """

        if not query_vector:
            return []

        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than zero."
            )

        return await self.vector_store.similarity_search(
            collection_name=self.collection_name,
            vector=query_vector,
            limit=top_k,
            filters=filters,
        )

    # ========================================================================
    # DELETE
    # ========================================================================

    async def delete(
        self,
        ids: list[str],
    ) -> Any:
        """
        Delete vectors by ID.
        """

        if not ids:
            return {
                "deleted": 0,
            }

        return await self.vector_store.delete(
            collection_name=self.collection_name,
            ids=ids,
        )

    async def delete_documents(
        self,
        ids: list[str],
    ) -> Any:
        """
        Alias for delete().
        """

        return await self.delete(
            ids
        )

    async def delete_by_metadata(
        self,
        filters: dict[str, Any],
    ) -> Any:
        """
        Delete indexed vectors using metadata filters.

        This delegates to VectorStoreManager, which delegates to the
        underlying provider.
        """

        if not filters:
            raise ValueError(
                "Metadata filters are required."
            )

        return await self.vector_store.delete_by_metadata(
            collection_name=self.collection_name,
            filters=filters,
        )

    # ========================================================================
    # DOCUMENT VECTOR
    # ========================================================================

    async def get_document_vector(
        self,
        document_id: str,
    ) -> list[float] | None:
        """
        Retrieve a representative vector for a document.
        """

        return await self.vector_store.get_document_vector(
            collection_name=self.collection_name,
            document_id=document_id,
        )

    # ========================================================================
    # STATISTICS
    # ========================================================================

    async def count(self) -> int:
        """
        Return number of indexed vectors.
        """

        return await self.vector_store.count(
            collection_name=self.collection_name,
        )

    async def stats(self) -> dict[str, Any]:
        """
        Return vector-index statistics.
        """

        return await self.vector_store.stats(
            collection_name=self.collection_name,
        )

    # ========================================================================
    # HEALTH
    # ========================================================================

    async def health_check(
        self,
    ) -> dict[str, Any]:
        """
        Check vector-store health.
        """

        return await self.vector_store.health_check()

    # ========================================================================
    # SHUTDOWN
    # ========================================================================

    async def close(
        self,
    ) -> None:
        """
        Close the underlying vector-store provider.
        """

        await self.vector_store.close()


__all__ = [
    "IndexManager",
    "DEFAULT_COLLECTION",
]