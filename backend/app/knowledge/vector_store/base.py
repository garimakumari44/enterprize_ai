"""
app/knowledge/vector_store/base.py

Abstract interfaces for vector storage.

Responsibilities
----------------
- Define the contract for vector-store implementations.
- Represent documents/chunks that can be indexed.
- Represent vector-search results.
- Keep vector-store implementations independent from application services.

This module does NOT:
- connect to a database
- create embeddings
- perform document processing
- manage application workflows
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence


# ============================================================================
# VECTOR DOCUMENT
# ============================================================================


@dataclass(slots=True)
class VectorDocument:
    """
    A document/chunk that can be stored in a vector store.
    """

    id: str
    vector: Sequence[float]
    content: str
    metadata: Mapping[str, Any] = field(default_factory=dict)


# ============================================================================
# SEARCH RESULT
# ============================================================================


@dataclass(slots=True)
class SearchResult:
    """
    Result returned by a vector similarity search.
    """

    id: str
    score: float
    content: str
    metadata: Mapping[str, Any] = field(default_factory=dict)


# ============================================================================
# VECTOR STORE
# ============================================================================


class VectorStore(ABC):
    """
    Abstract vector-store interface.

    Concrete implementations can use:

        - PostgreSQL + pgvector
        - Qdrant
        - Pinecone
        - Weaviate
        - Milvus
        - another vector database
    """

    # ------------------------------------------------------------------------
    # UPSERT
    # ------------------------------------------------------------------------

    @abstractmethod
    async def upsert(
        self,
        documents: Iterable[VectorDocument],
        *,
        collection: str,
    ) -> dict[str, Any]:
        """
        Insert or update vector documents.

        Returns:
            A result dictionary containing at least ``indexed``.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------------

    @abstractmethod
    async def delete(
        self,
        ids: Iterable[str],
        *,
        collection: str,
    ) -> None:
        """
        Delete vector documents by ID.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------------
    # SEARCH
    # ------------------------------------------------------------------------

    @abstractmethod
    async def search(
        self,
        vector: Sequence[float],
        *,
        collection: str,
        top_k: int = 5,
        filters: Mapping[str, Any] | None = None,
    ) -> list[SearchResult]:
        """
        Perform vector similarity search.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------------
    # COLLECTION
    # ------------------------------------------------------------------------

    @abstractmethod
    async def ensure_collection(
        self,
        collection: str,
        *,
        dimension: int,
    ) -> None:
        """
        Ensure that the vector collection/index exists.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------------
    # HEALTH CHECK
    # ------------------------------------------------------------------------

    async def health_check(self) -> bool:
        """
        Basic vector-store health check.
        """
        return True


# ============================================================================
# BACKWARD-COMPATIBILITY ALIASES
# ============================================================================

BaseVectorStore = VectorStore

# IMPORTANT:
#
# Do NOT write:
#
#     VectorSearchResult = SearchResult,
#
# because that creates a tuple.
#
# Correct alias:
VectorSearchResult = SearchResult


__all__ = [
    "VectorDocument",
    "SearchResult",
    "VectorStore",
    "BaseVectorStore",
    "VectorSearchResult",
]