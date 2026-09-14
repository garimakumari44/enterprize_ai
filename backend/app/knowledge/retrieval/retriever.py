"""
app/knowledge/retrieval/retriever.py

Retriever responsible for converting natural-language queries into
vector-search requests.

Responsibilities
----------------
- Generate an embedding for the query.
- Search the configured vector store.
- Apply collection/filter constraints.
- Normalize vector-store results.
- Support semantic search.
- Provide a hybrid-search entry point.
- Provide similar-document search.

This class does NOT:
- perform reranking
- create database sessions
- commit database transactions
- expose FastAPI endpoints
"""

from __future__ import annotations

import inspect
from collections.abc import Mapping, Sequence
from typing import Any

from app.knowledge.vector_store.base import SearchResult
from app.knowledge.vector_store.vector_manager import (
    VectorStoreManager,
)


class Retriever:
    """
    Enterprise knowledge retriever.

    Pipeline:

        query
          |
          v
        EmbeddingService
          |
          v
        query vector
          |
          v
        VectorStoreManager
          |
          v
        PGVectorStore
          |
          v
        candidate chunks
    """

    DEFAULT_COLLECTION_NAME = "document_chunks"

    MAX_TOP_K = 100

    def __init__(
        self,
        embedding_service: Any,
        vector_store_manager: VectorStoreManager,
        *,
        collection_name: str = DEFAULT_COLLECTION_NAME,
    ) -> None:
        """
        Initialize Retriever.
        """

        if embedding_service is None:
            raise ValueError(
                "embedding_service cannot be None."
            )

        if vector_store_manager is None:
            raise ValueError(
                "vector_store_manager cannot be None."
            )

        self.embedding_service = embedding_service
        self.vector_store = vector_store_manager
        self.collection_name = (
            collection_name.strip()
            if collection_name
            else self.DEFAULT_COLLECTION_NAME
        )

    # ========================================================================
    # SEMANTIC SEARCH
    # ========================================================================

    async def search(
        self,
        query: str,
        *,
        top_k: int = 50,
        filters: Mapping[str, Any] | None = None,
        collection_name: str | None = None,
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
        # Resolve collection
        # --------------------------------------------------------------------

        collection = (
            collection_name
            or self.collection_name
        )

        collection = str(
            collection
        ).strip()

        if not collection:
            raise ValueError(
                "collection_name cannot be empty."
            )

        # --------------------------------------------------------------------
        # Generate query embedding
        # --------------------------------------------------------------------

        query_vector = await self._embed_query(
            query
        )

        if not query_vector:
            return []

        # --------------------------------------------------------------------
        # Validate vector
        # --------------------------------------------------------------------

        query_vector = [
            float(value)
            for value in query_vector
        ]

        # --------------------------------------------------------------------
        # Search vector store
        # --------------------------------------------------------------------

        search_method = getattr(
            self.vector_store,
            "search",
            None,
        )

        if search_method is None:
            raise AttributeError(
                "VectorStoreManager must provide "
                "search()."
            )

        results = await search_method(
            collection_name=collection,
            vector=query_vector,
            limit=top_k,
            filters=dict(
                filters or {}
            ),
        )

        if results is None:
            return []

        # --------------------------------------------------------------------
        # Normalize
        # --------------------------------------------------------------------

        normalized: list[dict[str, Any]] = []

        for result in results:
            normalized.append(
                self._normalize_result(
                    result
                )
            )

        return normalized

    # ========================================================================
    # HYBRID SEARCH
    # ========================================================================

    async def hybrid_search(
        self,
        query: str,
        *,
        top_k: int = 50,
        filters: Mapping[str, Any] | None = None,
        collection_name: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Perform hybrid search.

        The current implementation uses semantic retrieval as the
        retrieval component.

        A dedicated PostgreSQL full-text/BM25 retriever can later
        be introduced without changing the public Retriever API.
        """

        return await self.search(
            query=query,
            top_k=top_k,
            filters=filters,
            collection_name=collection_name,
        )

    # ========================================================================
    # SIMILAR DOCUMENTS
    # ========================================================================

    async def search_similar(
        self,
        document_id: str,
        *,
        top_k: int = 5,
        collection_name: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Retrieve chunks/documents similar to an existing document.

        The vector store must provide a method capable of retrieving
        a representative embedding for the source document.
        """

        if not document_id or not str(
            document_id
        ).strip():
            return []

        if top_k <= 0:
            return []

        top_k = min(
            int(top_k),
            self.MAX_TOP_K,
        )

        collection = (
            collection_name
            or self.collection_name
        )

        collection = str(
            collection
        ).strip()

        # --------------------------------------------------------------------
        # Resolve underlying store
        # --------------------------------------------------------------------

        store = getattr(
            self.vector_store,
            "store",
            None,
        )

        if store is None:
            raise NotImplementedError(
                "VectorStoreManager does not expose "
                "an underlying store."
            )

        # --------------------------------------------------------------------
        # Resolve document-vector method
        # --------------------------------------------------------------------

        get_document_vector = getattr(
            store,
            "get_document_vector",
            None,
        )

        if get_document_vector is None:
            raise NotImplementedError(
                "The configured vector store does not implement "
                "get_document_vector(). "
                "search_similar() requires access to the source "
                "document's embedding."
            )

        # --------------------------------------------------------------------
        # Retrieve representative vector
        # --------------------------------------------------------------------

        query_vector = get_document_vector(
            document_id=str(document_id),
            collection=collection,
        )

        if inspect.isawaitable(
            query_vector
        ):
            query_vector = await query_vector

        if not query_vector:
            return []

        query_vector = [
            float(value)
            for value in query_vector
        ]

        # --------------------------------------------------------------------
        # Search
        # --------------------------------------------------------------------

        results = await self.vector_store.search(
            collection_name=collection,
            vector=query_vector,
            limit=top_k + 1,
            filters={},
        )

        normalized: list[dict[str, Any]] = []

        for result in results or []:

            item = self._normalize_result(
                result
            )

            result_document_id = item.get(
                "document_id"
            )

            # Exclude source document.
            if str(
                result_document_id
            ) == str(
                document_id
            ):
                continue

            normalized.append(
                item
            )

            if len(normalized) >= top_k:
                break

        return normalized

    # ========================================================================
    # EMBEDDING
    # ========================================================================

    async def _embed_query(
        self,
        query: str,
    ) -> Sequence[float]:
        """
        Generate an embedding for a query.

        Supported methods:

            embed_query()
            embed_text()
            embed()

        Both synchronous and asynchronous implementations are supported.
        """

        # --------------------------------------------------------------------
        # Preferred API
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
        # Common alternative
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

        # --------------------------------------------------------------------
        # Generic embed()
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

        raise AttributeError(
            "Embedding service must provide one of: "
            "embed_query(), embed_text(), or embed()."
        )

    # ========================================================================
    # RESULT NORMALIZATION
    # ========================================================================

    @staticmethod
    def _normalize_result(
        result: SearchResult | Mapping[str, Any] | Any,
    ) -> dict[str, Any]:
        """
        Convert a vector-store SearchResult into the normalized format:

            id
            chunk_id
            document_id
            collection_id
            content
            score
            metadata
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

            metadata_value = getattr(
                result,
                "metadata",
                {},
            )

            metadata = dict(
                metadata_value or {}
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
        # Normalize ID
        # --------------------------------------------------------------------

        normalized_id = (
            str(result_id)
            if result_id is not None
            else None
        )

        # --------------------------------------------------------------------
        # Extract chunk ID
        # --------------------------------------------------------------------

        chunk_id = (
            metadata.get("chunk_id")
            or metadata.get("chunkId")
            or metadata.get("id")
            or normalized_id
        )

        # --------------------------------------------------------------------
        # Extract document ID
        # --------------------------------------------------------------------

        document_id = (
            metadata.get("document_id")
            or metadata.get("documentId")
        )

        # --------------------------------------------------------------------
        # Extract collection ID
        # --------------------------------------------------------------------

        collection_id = (
            metadata.get("collection_id")
            or metadata.get("collectionId")
        )

        # --------------------------------------------------------------------
        # Normalize content
        # --------------------------------------------------------------------

        if content is None:
            content = ""

        # --------------------------------------------------------------------
        # Normalize score
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
        Normalize different embedding-service return formats.

        Supported:

            [0.1, 0.2, 0.3]

        or:

            {
                "embedding": [0.1, 0.2, 0.3]
            }

        or:

            {
                "vector": [0.1, 0.2, 0.3]
            }

        or an object exposing `.embedding`.

        Also supports a list containing one embedding vector.
        """

        if result is None:
            return []

        # --------------------------------------------------------------------
        # Dictionary response
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
                    "Embedding service returned a dictionary "
                    "without 'embedding' or 'vector'."
                )

            return Retriever._coerce_embedding(
                embedding
            )

        # --------------------------------------------------------------------
        # Object response
        # --------------------------------------------------------------------

        embedding = getattr(
            result,
            "embedding",
            None,
        )

        if embedding is not None:
            return Retriever._coerce_embedding(
                embedding
            )

        # --------------------------------------------------------------------
        # Object exposing vector
        # --------------------------------------------------------------------

        vector = getattr(
            result,
            "vector",
            None,
        )

        if vector is not None:
            return Retriever._coerce_embedding(
                vector
            )

        # --------------------------------------------------------------------
        # Direct vector
        # --------------------------------------------------------------------

        if isinstance(
            result,
            Sequence,
        ) and not isinstance(
            result,
            (str, bytes),
        ):

            # Handle a single vector:
            #
            # [0.1, 0.2, 0.3]
            #

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

            # Handle:
            #
            # [[0.1, 0.2, 0.3]]
            #

            if len(result) == 1 and isinstance(
                result[0],
                Sequence,
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
    ) -> Sequence[float]:
        """
        Convert an embedding-like value into a list of floats.
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
    "Retriever",
]