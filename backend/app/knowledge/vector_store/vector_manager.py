"""
app/knowledge/vector_store/vector_manager.py

Central vector-store controller.

Current provider:
    PostgreSQL + pgvector

Future providers can be added without changing
IndexingService, IndexManager, or Retriever.
"""

from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .base import (
    SearchResult,
    VectorDocument,
    VectorStore,
)
from .pgvector import PGVectorStore


class VectorStoreManager:
    """
    Central Vector Database Controller.

    Architecture:

        SearchService
              |
              v
        RetrievalPipeline
              |
              v
        Retriever
              |
              v
        IndexManager
              |
              v
        VectorStoreManager
              |
              v
        PGVectorStore
              |
              v
        PostgreSQL + pgvector

    The SQLAlchemy AsyncSession is injected into this manager.

    Important:
        The manager owns the provider object, but it does NOT own
        the SQLAlchemy AsyncSession lifecycle.
    """

    def __init__(
        self,
        provider: str = "pgvector",
        *,
        session: AsyncSession,
        config: dict[str, Any] | None = None,
    ) -> None:
        self.provider = provider.lower().strip()
        self.session = session
        self.config = config or {}

        self.store: VectorStore = self._initialize_store()

    # ========================================================================
    # PROVIDER FACTORY
    # ========================================================================

    def _initialize_store(self) -> VectorStore:
        """
        Initialize the configured vector-store provider.
        """

        if self.provider == "pgvector":
            embedding_dimension = int(
                self.config.get(
                    "embedding_dimension",
                    PGVectorStore.DEFAULT_EMBEDDING_DIMENSION,
                )
            )

            collection = self.config.get(
                "collection",
                PGVectorStore.DEFAULT_COLLECTION,
            )

            return PGVectorStore(
                session=self.session,
                embedding_dimension=embedding_dimension,
                collection=collection,
            )

        raise ValueError(
            f"Unsupported vector provider: {self.provider}"
        )

    # ========================================================================
    # COLLECTION
    # ========================================================================

    async def create_collection(
        self,
        collection_name: str,
        dimension: int,
    ) -> None:
        """
        Create/ensure a vector collection.

        `dimension` is accepted here because the manager API exposes
        embedding dimensions to callers.

        The provider receives it through the canonical compatibility
        method.
        """

        await self.store.ensure_collection(
            collection=collection_name,
            dimension=dimension,
        )

    async def ensure_collection(
        self,
        collection_name: str,
        *,
        dimension: int,
    ) -> None:
        """
        Canonical collection initialization method.
        """

        await self.store.ensure_collection(
            collection=collection_name,
            dimension=dimension,
        )

    async def delete_collection(
        self,
        collection_name: str,
    ) -> None:
        """
        Delete an entire vector collection.
        """

        method = getattr(
            self.store,
            "delete_collection",
            None,
        )

        if method is None:
            raise NotImplementedError(
                f"Vector provider '{self.provider}' "
                "does not support deleting collections."
            )

        await method(
            collection_name=collection_name,
        )

    # ========================================================================
    # DOCUMENTS / UPSERT
    # ========================================================================

    async def add_documents(
        self,
        collection_name: str,
        documents: Sequence[VectorDocument],
    ) -> dict[str, Any]:
        """
        Add/upsert multiple vector documents.
        """

        if not documents:
            return {
                "indexed": 0,
            }

        return await self.store.upsert(
            documents=list(documents),
            collection=collection_name,
        )

    async def upsert(
        self,
        collection_name: str,
        documents: Sequence[VectorDocument] | None = None,
        *,
        vectors: Sequence[VectorDocument] | None = None,
        vector_id: str | None = None,
        vector: Sequence[float] | None = None,
        content: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Insert or update vector documents.

        Supported APIs:

            await manager.upsert(
                collection_name="document_chunk_vectors",
                documents=[
                    VectorDocument(...)
                ],
            )

        or:

            await manager.upsert(
                collection_name="document_chunk_vectors",
                vectors=[
                    VectorDocument(...)
                ],
            )

        or:

            await manager.upsert(
                collection_name="document_chunk_vectors",
                vector_id="chunk-1",
                vector=[...],
                content="...",
                metadata={...},
            )
        """

        # --------------------------------------------------------------------
        # Canonical documents API
        # --------------------------------------------------------------------

        if documents is not None:
            document_list = list(documents)

            if not document_list:
                return {
                    "indexed": 0,
                }

            return await self.store.upsert(
                documents=document_list,
                collection=collection_name,
            )

        # --------------------------------------------------------------------
        # Backward-compatible vectors API
        # --------------------------------------------------------------------

        if vectors is not None:
            vector_list = list(vectors)

            if not vector_list:
                return {
                    "indexed": 0,
                }

            return await self.store.upsert(
                documents=vector_list,
                collection=collection_name,
            )

        # --------------------------------------------------------------------
        # Single vector API
        # --------------------------------------------------------------------

        if vector_id is None:
            raise ValueError(
                "vector_id is required when "
                "documents/vectors are not provided."
            )

        if vector is None:
            raise ValueError(
                "vector is required when "
                "documents/vectors are not provided."
            )

        if content is None:
            raise ValueError(
                "content is required when "
                "documents/vectors are not provided."
            )

        document = VectorDocument(
            id=vector_id,
            vector=vector,
            content=content,
            metadata=metadata or {},
        )

        return await self.store.upsert(
            documents=[document],
            collection=collection_name,
        )

    # ========================================================================
    # SEARCH
    # ========================================================================

    async def similarity_search(
        self,
        collection_name: str,
        query_vector: Sequence[float] | None = None,
        top_k: int = 5,
        filters: Mapping[str, Any] | None = None,
        *,
        vector: Sequence[float] | None = None,
        limit: int | None = None,
    ) -> list[SearchResult]:
        """
        Perform vector similarity search.
        """

        resolved_vector = (
            query_vector
            if query_vector is not None
            else vector
        )

        if not resolved_vector:
            return []

        resolved_limit = (
            limit
            if limit is not None
            else top_k
        )

        if resolved_limit <= 0:
            raise ValueError(
                "Search limit must be greater than zero."
            )

        return await self.store.search(
            vector=resolved_vector,
            collection=collection_name,
            top_k=resolved_limit,
            filters=filters,
        )

    async def search(
        self,
        collection_name: str,
        vector: Sequence[float],
        limit: int = 5,
        filters: Mapping[str, Any] | None = None,
    ) -> list[SearchResult]:
        """
        Canonical vector search method.
        """

        if not vector:
            return []

        if limit <= 0:
            raise ValueError(
                "Search limit must be greater than zero."
            )

        return await self.store.search(
            vector=vector,
            collection=collection_name,
            top_k=limit,
            filters=filters,
        )

    # ========================================================================
    # DELETE
    # ========================================================================

    async def delete(
        self,
        collection_name: str,
        ids: Sequence[str],
    ) -> None:
        """
        Delete vector documents by ID.
        """

        if not ids:
            return

        await self.store.delete(
            ids=list(ids),
            collection=collection_name,
        )

    async def delete_documents(
        self,
        collection_name: str,
        ids: Sequence[str],
    ) -> None:
        """
        Backward-compatible alias for delete().
        """

        await self.delete(
            collection_name=collection_name,
            ids=ids,
        )

    async def delete_by_metadata(
        self,
        collection_name: str,
        filters: Mapping[str, Any],
    ) -> dict[str, Any]:
        """
        Delete vectors matching metadata filters.
        """

        if not filters:
            raise ValueError(
                "Metadata filters cannot be empty."
            )

        if not re.fullmatch(
            r"[A-Za-z_][A-Za-z0-9_]*",
            collection_name,
        ):
            raise ValueError(
                f"Invalid SQL collection name: {collection_name}"
            )

        conditions: list[str] = []
        parameters: dict[str, Any] = {}

        for index, (key, value) in enumerate(filters.items()):
            parameter_name = f"metadata_value_{index}"
            key_parameter = f"metadata_key_{index}"

            conditions.append(
                "metadata ->> "
                f":{key_parameter} = "
                f":{parameter_name}"
            )

            parameters[key_parameter] = str(key)
            parameters[parameter_name] = str(value)

        where_clause = " AND ".join(conditions)

        query = text(
            f"""
            DELETE FROM {collection_name}
            WHERE {where_clause}
            """
        )

        result = await self.session.execute(
            query,
            parameters,
        )

        deleted = (
            result.rowcount
            if result.rowcount is not None
            else 0
        )

        return {
            "deleted": int(deleted),
        }

    # ========================================================================
    # DOCUMENT VECTOR
    # ========================================================================

    async def get_document_vector(
        self,
        collection_name: str,
        document_id: str,
    ) -> list[float] | None:
        """
        Retrieve one representative vector for a document.
        """

        if not re.fullmatch(
            r"[A-Za-z_][A-Za-z0-9_]*",
            collection_name,
        ):
            raise ValueError(
                f"Invalid SQL collection name: {collection_name}"
            )

        query = text(
            f"""
            SELECT embedding
            FROM {collection_name}
            WHERE metadata ->> 'document_id' = :document_id
            LIMIT 1
            """
        )

        result = await self.session.execute(
            query,
            {
                "document_id": str(document_id),
            },
        )

        row = result.fetchone()

        if row is None:
            return None

        embedding = row[0]

        if isinstance(embedding, str):
            embedding = (
                embedding
                .strip()
                .strip("[]")
            )

            if not embedding:
                return None

            return [
                float(value.strip())
                for value in embedding.split(",")
            ]

        try:
            return [
                float(value)
                for value in embedding
            ]
        except TypeError:
            return None

    # ========================================================================
    # COUNT
    # ========================================================================

    async def count(
        self,
        collection_name: str,
    ) -> int:
        """
        Return number of vectors in a collection.
        """

        method = getattr(
            self.store,
            "count",
            None,
        )

        if method is None:
            raise NotImplementedError(
                f"Vector provider '{self.provider}' "
                "does not support count()."
            )

        return await method(
            collection=collection_name,
        )

    # ========================================================================
    # STATS
    # ========================================================================

    async def stats(
        self,
        collection_name: str,
    ) -> dict[str, Any]:
        """
        Return vector-store statistics.
        """

        count = await self.count(
            collection_name=collection_name,
        )

        return {
            "document_count": count,
            "provider": self.provider,
            "collection": collection_name,
        }

    # ========================================================================
    # HEALTH
    # ========================================================================

    async def health_check(
        self,
    ) -> dict[str, Any]:
        """
        Check vector-store health.
        """

        result = await self.store.health_check()

        if isinstance(result, dict):
            return result

        return {
            "status": (
                "healthy"
                if result
                else "unhealthy"
            ),
            "provider": self.provider,
        }

    # ========================================================================
    # CLOSE
    # ========================================================================

    async def close(self) -> None:
        """
        Close the vector-store provider.

        The SQLAlchemy AsyncSession remains owned by the
        application/session dependency.

        Therefore this method only invokes provider cleanup
        when the provider explicitly exposes it.
        """

        method = getattr(
            self.store,
            "close",
            None,
        )

        if method is None:
            # PGVectorStore uses the injected AsyncSession and
            # therefore has nothing independently owned to close.
            return

        result = method()

        if result is not None:
            await result


__all__ = [
    "VectorStoreManager",
]