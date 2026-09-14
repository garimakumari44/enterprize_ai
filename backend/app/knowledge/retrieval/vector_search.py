"""
app/knowledge/retrieval/vector_search.py

Semantic/vector retrieval component.

Responsibilities
----------------
- Convert a natural-language query into an embedding.
- Execute vector similarity search.
- Apply metadata filters.
- Normalize vector-store results.
- Return a consistent list[dict] structure.

This class does NOT:
- perform keyword retrieval
- perform hybrid merging
- perform reranking
- create database sessions
- expose API routes
"""

from __future__ import annotations

import inspect
from collections.abc import Mapping, Sequence
from typing import Any


class VectorSearch:
    """
    Semantic/vector search engine.

    Pipeline:

        Query
          |
          v
        EmbeddingService
          |
          v
        Query Embedding
          |
          v
        Vector Store
          |
          v
        Similar Chunks
    """

    DEFAULT_TOP_K = 10
    MAX_TOP_K = 100

    def __init__(
        self,
        vector_store: Any,
        embedding_service: Any,
    ) -> None:
        """
        Initialize VectorSearch.
        """

        if vector_store is None:
            raise ValueError(
                "vector_store cannot be None."
            )

        if embedding_service is None:
            raise ValueError(
                "embedding_service cannot be None."
            )

        self.vector_store = vector_store
        self.embedding_service = embedding_service

    # ========================================================================
    # SEARCH
    # ========================================================================

    async def search(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        filters: Mapping[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Perform semantic vector search.
        """

        # --------------------------------------------------------------------
        # Validate query
        # --------------------------------------------------------------------

        if not isinstance(
            query,
            str,
        ):
            raise TypeError(
                "query must be a string."
            )

        query = query.strip()

        if not query:
            return []

        # --------------------------------------------------------------------
        # Validate top_k
        # --------------------------------------------------------------------

        if top_k <= 0:
            return []

        top_k = min(
            int(top_k),
            self.MAX_TOP_K,
        )

        # --------------------------------------------------------------------
        # Generate query embedding
        # --------------------------------------------------------------------

        query_embedding = await self._embed_query(
            query
        )

        if not query_embedding:
            return []

        # --------------------------------------------------------------------
        # Search vector store
        # --------------------------------------------------------------------

        results = await self._search_vector_store(
            query_embedding=query_embedding,
            top_k=top_k,
            filters=filters,
        )

        if results is None:
            return []

        # --------------------------------------------------------------------
        # Normalize results
        # --------------------------------------------------------------------

        normalized: list[dict[str, Any]] = []

        for result in results:

            if result is None:
                continue

            normalized.append(
                self._normalize_result(
                    result
                )
            )

        return normalized

    # ========================================================================
    # EMBEDDING
    # ========================================================================

    async def _embed_query(
        self,
        query: str,
    ) -> Sequence[float]:
        """
        Generate an embedding.

        Supported embedding-service methods:

            embed()
            embed_query()
            embed_text()

        Both synchronous and asynchronous implementations
        are supported.
        """

        # --------------------------------------------------------------------
        # Preferred generic API
        # --------------------------------------------------------------------

        embed = getattr(
            self.embedding_service,
            "embed",
            None,
        )

        if callable(embed):

            result = embed(
                query
            )

            if inspect.isawaitable(
                result
            ):
                result = await result

            return self._extract_embedding(
                result
            )

        # --------------------------------------------------------------------
        # Query-specific API
        # --------------------------------------------------------------------

        embed_query = getattr(
            self.embedding_service,
            "embed_query",
            None,
        )

        if callable(embed_query):

            result = embed_query(
                query
            )

            if inspect.isawaitable(
                result
            ):
                result = await result

            return self._extract_embedding(
                result
            )

        # --------------------------------------------------------------------
        # Text-specific API
        # --------------------------------------------------------------------

        embed_text = getattr(
            self.embedding_service,
            "embed_text",
            None,
        )

        if callable(embed_text):

            result = embed_text(
                query
            )

            if inspect.isawaitable(
                result
            ):
                result = await result

            return self._extract_embedding(
                result
            )

        raise AttributeError(
            "Embedding service must provide one of: "
            "embed(), embed_query(), or embed_text()."
        )

    # ========================================================================
    # VECTOR STORE SEARCH
    # ========================================================================

    async def _search_vector_store(
        self,
        *,
        query_embedding: Sequence[float],
        top_k: int,
        filters: Mapping[str, Any] | None,
    ) -> Any:
        """
        Execute the actual vector-store search.

        Supported APIs:

            similarity_search(
                embedding=...,
                limit=...,
                filters=...
            )

        or:

            search(
                vector=...,
                limit=...,
                filters=...
            )

        This allows VectorSearch to work with both the older vector-store
        abstraction and the newer VectorStoreManager abstraction.
        """

        search_filters = dict(
            filters or {}
        )

        # --------------------------------------------------------------------
        # Newer VectorStoreManager-style API
        # --------------------------------------------------------------------

        search = getattr(
            self.vector_store,
            "search",
            None,
        )

        if callable(search):

            result = search(
                vector=list(
                    query_embedding
                ),
                limit=top_k,
                filters=search_filters,
            )

            if inspect.isawaitable(
                result
            ):
                result = await result

            return result

        # --------------------------------------------------------------------
        # Existing similarity_search API
        # --------------------------------------------------------------------

        similarity_search = getattr(
            self.vector_store,
            "similarity_search",
            None,
        )

        if callable(
            similarity_search
        ):

            result = similarity_search(
                embedding=list(
                    query_embedding
                ),
                limit=top_k,
                filters=search_filters,
            )

            if inspect.isawaitable(
                result
            ):
                result = await result

            return result

        raise AttributeError(
            "Vector store must provide either "
            "search() or similarity_search()."
        )

    # ========================================================================
    # RESULT NORMALIZATION
    # ========================================================================

    @staticmethod
    def _normalize_result(
        result: Any,
    ) -> dict[str, Any]:
        """
        Normalize a vector-store result.

        Output:

            {
                "id": ...,
                "chunk_id": ...,
                "document_id": ...,
                "collection_id": ...,
                "content": ...,
                "score": ...,
                "metadata": {...}
            }
        """

        # --------------------------------------------------------------------
        # Object result
        # --------------------------------------------------------------------

        if hasattr(
            result,
            "id",
        ):

            result_id = getattr(
                result,
                "id",
                None,
            )

            score = getattr(
                result,
                "score",
                0.0,
            )

            content = getattr(
                result,
                "content",
                "",
            )

            metadata = dict(
                getattr(
                    result,
                    "metadata",
                    {},
                )
                or {}
            )

        # --------------------------------------------------------------------
        # Mapping result
        # --------------------------------------------------------------------

        elif isinstance(
            result,
            Mapping,
        ):

            result_id = result.get(
                "id"
            )

            score = result.get(
                "score",
                0.0,
            )

            content = result.get(
                "content",
                "",
            )

            metadata = dict(
                result.get(
                    "metadata",
                    {},
                )
                or {}
            )

        else:

            raise TypeError(
                "Unsupported vector search result type: "
                f"{type(result).__name__}"
            )

        # --------------------------------------------------------------------
        # IDs
        # --------------------------------------------------------------------

        chunk_id = (
            metadata.get("chunk_id")
            or metadata.get("chunkId")
            or metadata.get("id")
            or result_id
        )

        document_id = (
            metadata.get("document_id")
            or metadata.get("documentId")
        )

        collection_id = (
            metadata.get("collection_id")
            or metadata.get("collectionId")
        )

        # --------------------------------------------------------------------
        # Content
        # --------------------------------------------------------------------

        if content is None:
            content = ""

        # --------------------------------------------------------------------
        # Score
        # --------------------------------------------------------------------

        try:
            normalized_score = float(
                score
            )
        except (
            TypeError,
            ValueError,
        ):
            normalized_score = 0.0

        # --------------------------------------------------------------------
        # ID normalization
        # --------------------------------------------------------------------

        normalized_id = (
            str(result_id)
            if result_id is not None
            else (
                str(chunk_id)
                if chunk_id is not None
                else None
            )
        )

        return {
            "id": normalized_id,
            "chunk_id": chunk_id,
            "document_id": document_id,
            "collection_id": collection_id,
            "content": str(content),
            "score": normalized_score,
            "metadata": metadata,
        }

    # ========================================================================
    # EMBEDDING NORMALIZATION
    # ========================================================================

    @staticmethod
    def _extract_embedding(
        result: Any,
    ) -> Sequence[float]:
        """
        Normalize embedding-service output.

        Supported:

            [0.1, 0.2, 0.3]

        or:

            {
                "embedding": [...]
            }

        or:

            {
                "vector": [...]
            }

        or:

            object.embedding
        """

        if result is None:
            return []

        # --------------------------------------------------------------------
        # Mapping
        # --------------------------------------------------------------------

        if isinstance(
            result,
            Mapping,
        ):

            embedding = result.get(
                "embedding"
            )

            if embedding is None:
                embedding = result.get(
                    "vector"
                )

            if embedding is None:
                raise ValueError(
                    "Embedding response does not contain "
                    "'embedding' or 'vector'."
                )

            return VectorSearch._coerce_embedding(
                embedding
            )

        # --------------------------------------------------------------------
        # Object
        # --------------------------------------------------------------------

        embedding = getattr(
            result,
            "embedding",
            None,
        )

        if embedding is not None:
            return VectorSearch._coerce_embedding(
                embedding
            )

        vector = getattr(
            result,
            "vector",
            None,
        )

        if vector is not None:
            return VectorSearch._coerce_embedding(
                vector
            )

        # --------------------------------------------------------------------
        # Direct sequence
        # --------------------------------------------------------------------

        if isinstance(
            result,
            Sequence,
        ) and not isinstance(
            result,
            (str, bytes),
        ):

            # Single vector.
            if all(
                isinstance(
                    value,
                    (int, float),
                )
                for value in result
            ):
                return [
                    float(value)
                    for value in result
                ]

            # Nested single vector.
            if (
                len(result) == 1
                and isinstance(
                    result[0],
                    Sequence,
                )
            ):
                return [
                    float(value)
                    for value in result[0]
                ]

        raise TypeError(
            "Unsupported embedding result type: "
            f"{type(result).__name__}"
        )

    # ========================================================================
    # EMBEDDING COERCION
    # ========================================================================

    @staticmethod
    def _coerce_embedding(
        embedding: Any,
    ) -> list[float]:
        """
        Convert an embedding into a list of floats.
        """

        if embedding is None:
            return []

        if not isinstance(
            embedding,
            Sequence,
        ) or isinstance(
            embedding,
            (str, bytes),
        ):
            raise TypeError(
                "Embedding must be a sequence of numeric values."
            )

        try:
            return [
                float(value)
                for value in embedding
            ]

        except (
            TypeError,
            ValueError,
        ) as exc:

            raise ValueError(
                "Embedding contains non-numeric values."
            ) from exc


__all__ = [
    "VectorSearch",
]