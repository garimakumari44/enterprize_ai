"""
app/knowledge/services/knowledge_service.py

High-level Knowledge lifecycle service.

Responsibilities
----------------
- Ingest documents.
- Index documents.
- Delete indexed documents.
- Reindex documents.

This service is NOT responsible for conversational retrieval.

Conversational retrieval should use:

    SearchService
        ↓
    RetrievalPipeline
        ↓
    Vector / Hybrid Search
        ↓
    Reranking
        ↓
    Retrieved Context

The Assistant should therefore use SearchService / RetrievalPipeline
through ContextService rather than calling KnowledgeService directly.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .indexing_service import IndexingService
from .ingestion_service import IngestionService


class KnowledgeService:
    """
    High-level service that coordinates the Knowledge lifecycle.

    This class owns document ingestion and indexing operations.

    It deliberately does not implement conversational search.
    """

    def __init__(
        self,
        ingestion_service: IngestionService,
        indexing_service: IndexingService,
    ) -> None:
        if ingestion_service is None:
            raise ValueError(
                "KnowledgeService requires an IngestionService."
            )

        if indexing_service is None:
            raise ValueError(
                "KnowledgeService requires an IndexingService."
            )

        self.ingestion = ingestion_service
        self.indexing = indexing_service

    # =================================================================
    # INGESTION
    # =================================================================

    async def ingest_document(
        self,
        file_path: str,
        metadata: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """
        Ingest and index a single document.
        """

        if not isinstance(
            file_path,
            str,
        ):
            raise TypeError(
                "file_path must be a string."
            )

        file_path = file_path.strip()

        if not file_path:
            raise ValueError(
                "file_path cannot be empty."
            )

        document = await self.ingestion.ingest_document(
            file_path=file_path,
            metadata=metadata or {},
        )

        await self.indexing.index_document(
            document
        )

        return document

    async def ingest_documents(
        self,
        files: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Ingest and index multiple documents.
        """

        if not isinstance(
            files,
            list,
        ):
            raise TypeError(
                "files must be a list."
            )

        results: List[Dict[str, Any]] = []

        for file_path in files:
            document = await self.ingest_document(
                file_path=file_path,
            )

            results.append(
                document
            )

        return results

    # =================================================================
    # DELETION
    # =================================================================

    async def delete_document(
        self,
        document_id: str,
    ) -> bool:
        """
        Remove a document from the Knowledge indexes.
        """

        if not isinstance(
            document_id,
            str,
        ):
            raise TypeError(
                "document_id must be a string."
            )

        document_id = document_id.strip()

        if not document_id:
            raise ValueError(
                "document_id cannot be empty."
            )

        return await self.indexing.remove_document(
            document_id
        )

    # =================================================================
    # REINDEX
    # =================================================================

    async def reindex_document(
        self,
        document_id: str,
    ) -> bool:
        """
        Rebuild Knowledge indexes for one document.
        """

        if not isinstance(
            document_id,
            str,
        ):
            raise TypeError(
                "document_id must be a string."
            )

        document_id = document_id.strip()

        if not document_id:
            raise ValueError(
                "document_id cannot be empty."
            )

        return await self.indexing.reindex_document(
            document_id
        )


__all__ = [
    "KnowledgeService",
]