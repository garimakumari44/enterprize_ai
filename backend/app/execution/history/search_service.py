"""
Advanced search service for execution history.
"""

from __future__ import annotations

from typing import Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.execution.history.filters import SearchFilter
from app.execution.history.history_repository import HistoryRepository
from app.execution.models.execution import Execution


class SearchService:
    """
    Provides search capabilities over execution history.

    This service hides the underlying search implementation,
    allowing future migration to PostgreSQL Full Text Search,
    Elasticsearch, OpenSearch, or Vector Search.
    """

    def __init__(self, db: AsyncSession):
        self.repository = HistoryRepository(db)

    # ---------------------------------------------------------
    # Keyword Search
    # ---------------------------------------------------------

    async def search(
        self,
        filters: SearchFilter,
    ) -> List[Execution]:
        """
        Search execution history.
        """

        if not filters.query.strip():
            return []

        return await self.repository.search(filters)

    # ---------------------------------------------------------
    # Suggestions
    # ---------------------------------------------------------

    async def suggestions(
        self,
        keyword: str,
        limit: int = 10,
    ) -> List[str]:
        """
        Returns search suggestions.

        Placeholder implementation.
        """

        if not keyword.strip():
            return []

        executions = await self.repository.search(
            SearchFilter(
                query=keyword,
                page=1,
                page_size=limit,
            )
        )

        suggestions = set()

        for execution in executions:

            if getattr(execution, "workflow_name", None):
                suggestions.add(execution.workflow_name)

            if getattr(execution, "status", None):
                suggestions.add(execution.status)

        return sorted(suggestions)

    # ---------------------------------------------------------
    # Facets
    # ---------------------------------------------------------

    async def search_facets(
        self,
        filters: SearchFilter,
    ) -> Dict:
        """
        Returns metadata useful for search UI.

        Example:
            Status counts
            Workflow names
            Total results
        """

        executions = await self.repository.search(filters)

        status_counts = {}

        workflow_names = set()

        for execution in executions:

            workflow_names.add(
                getattr(execution, "workflow_name", "")
            )

            status = getattr(
                execution,
                "status",
                "UNKNOWN",
            )

            status_counts[status] = (
                status_counts.get(status, 0) + 1
            )

        return {
            "total": len(executions),
            "statuses": status_counts,
            "workflow_names": sorted(
                workflow_names
            ),
        }

    # ---------------------------------------------------------
    # Recent Searches
    # ---------------------------------------------------------

    async def recent(
        self,
        limit: int = 20,
    ) -> List[Execution]:
        """
        Returns recent executions.

        Uses an empty search to retrieve
        newest executions.
        """

        return await self.repository.search(
            SearchFilter(
                query="",
                page=1,
                page_size=limit,
            )
        )

    # ---------------------------------------------------------
    # Future Extensions
    # ---------------------------------------------------------

    async def semantic_search(
        self,
        query: str,
    ) -> List[Execution]:
        """
        Placeholder for semantic/vector search.

        Future implementations may use:

        - pgvector
        - Pinecone
        - Weaviate
        - Milvus
        - Qdrant
        """

        raise NotImplementedError(
            "Semantic search is not implemented."
        )

    async def hybrid_search(
        self,
        query: str,
    ) -> List[Execution]:
        """
        Placeholder for hybrid search.

        Future:
        - Keyword search
        - BM25
        - Vector search
        - Reranking
        """

        raise NotImplementedError(
            "Hybrid search is not implemented."
        )