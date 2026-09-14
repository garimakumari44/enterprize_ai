"""
app/api/v1/knowledge/search.py

Knowledge Search API.

Final API paths:

    POST /api/v1/knowledge/
    POST /api/v1/knowledge/hybrid/
    GET  /api/v1/knowledge/history
    GET  /api/v1/knowledge/similar/{document_id}
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_db

from app.knowledge.repositories.search_repository import (
    SearchRepository,
)

from app.knowledge.retrieval.hybrid_search import (
    HybridSearch,
)

from app.knowledge.retrieval.keyword_search import (
    KeywordSearch,
)

from app.knowledge.retrieval.retrieval_pipeline import (
    RetrievalPipeline,
)

from app.knowledge.retrieval.semantic_search import (
    SemanticSearch,
)

from app.knowledge.retrieval.retriever import (
    Retriever,
)

from app.knowledge.retrieval.reranker import (
    Reranker,
)

from app.knowledge.services.search_service import (
    SearchService,
)

from app.knowledge.vector_store.vector_manager import (
    VectorStoreManager,
)

from app.schemas.knowledge.search_schema import (
    SearchRequest,
    SearchResponse,
)


# ============================================================================
# ROUTER
# ============================================================================

router = APIRouter(
    tags=["Knowledge Search"],
)


# ============================================================================
# VECTOR STORE
# ============================================================================

async def get_vector_store_manager(
    db: AsyncSession = Depends(get_async_db),
) -> VectorStoreManager:
    """
    Create the application vector-store manager.
    """

    return VectorStoreManager(
        provider="pgvector",
        session=db,
    )


# ============================================================================
# RETRIEVER
# ============================================================================

async def get_retriever(
    vector_store: VectorStoreManager = Depends(
        get_vector_store_manager
    ),
) -> Retriever:
    """
    Build semantic Retriever.

    Model:
        BAAI/bge-small-en-v1.5

    Dimensions:
        384

    Device:
        CPU
    """

    from app.knowledge.embeddings.embedding_manager import (
        EmbeddingManager,
    )

    from app.knowledge.embeddings.local_embedding import (
        LocalEmbedding,
    )

    embedding_provider = LocalEmbedding(
        model_name="BAAI/bge-small-en-v1.5",
        device="cpu",
    )

    embedding_manager = EmbeddingManager(
        provider=embedding_provider,
    )

    return Retriever(
        embedding_service=embedding_manager,
        vector_store_manager=vector_store,
        collection_name="document_chunk_vectors",
    )


# ============================================================================
# SEARCH REPOSITORY
# ============================================================================

async def get_search_repository(
    db: AsyncSession = Depends(get_async_db),
) -> SearchRepository:
    """
    Create database search repository.
    """

    return SearchRepository(
        db=db,
    )


# ============================================================================
# KEYWORD BACKEND
# ============================================================================

class KeywordSearchBackend:
    """
    Adapter between KeywordSearch and SearchRepository.

    SearchRepository returns normalized dictionaries from
    document_chunk_vectors.
    """

    def __init__(
        self,
        repository: SearchRepository,
    ) -> None:
        self.repository = repository

    async def search(
        self,
        query: str,
        *,
        limit: int = 10,
        top_k: int | None = None,
        filters: Mapping[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Execute keyword search.
        """

        effective_limit = (
            top_k
            if top_k is not None
            else limit
        )

        results = await self.repository.keyword_search(
            query=query,
            limit=effective_limit,
            filters=filters,
        )

        normalized: list[dict[str, Any]] = []

        for result in results or []:

            item = self._normalize_result(
                result
            )

            if item is not None:
                normalized.append(item)

        return normalized

    @staticmethod
    def _normalize_result(
        result: Any,
    ) -> dict[str, Any] | None:

        if result is None:
            return None

        # --------------------------------------------------------------
        # Mapping result
        # --------------------------------------------------------------

        if isinstance(result, Mapping):

            metadata_value = (
                result.get("metadata")
                or result.get("metadata_")
                or {}
            )

            if isinstance(
                metadata_value,
                Mapping,
            ):
                metadata = dict(metadata_value)
            else:
                try:
                    metadata = dict(metadata_value)
                except (
                    TypeError,
                    ValueError,
                ):
                    metadata = {}

            chunk_id = (
                result.get("chunk_id")
                or metadata.get("chunk_id")
                or result.get("id")
            )

            document_id = (
                result.get("document_id")
                or metadata.get("document_id")
            )

            document_version_id = (
                result.get("document_version_id")
                or metadata.get(
                    "document_version_id"
                )
            )

            collection_id = (
                result.get("collection_id")
                or metadata.get("collection_id")
            )

            content = (
                result.get("content")
                or result.get("text")
                or ""
            )

            raw_score = result.get(
                "score",
                0.5,
            )

            try:
                score = float(raw_score)
            except (
                TypeError,
                ValueError,
            ):
                score = 0.5

            if chunk_id is not None:
                metadata.setdefault(
                    "chunk_id",
                    str(chunk_id),
                )

            if document_id is not None:
                metadata.setdefault(
                    "document_id",
                    str(document_id),
                )

            if document_version_id is not None:
                metadata.setdefault(
                    "document_version_id",
                    str(document_version_id),
                )

            return {
                "id": (
                    str(result.get("id"))
                    if result.get("id") is not None
                    else (
                        str(chunk_id)
                        if chunk_id is not None
                        else None
                    )
                ),
                "chunk_id": (
                    str(chunk_id)
                    if chunk_id is not None
                    else None
                ),
                "document_id": (
                    str(document_id)
                    if document_id is not None
                    else None
                ),
                "document_version_id": (
                    str(document_version_id)
                    if document_version_id is not None
                    else None
                ),
                "collection_id": (
                    str(collection_id)
                    if collection_id is not None
                    else None
                ),
                "content": str(content),
                "score": max(
                    0.0,
                    min(score, 1.0),
                ),
                "metadata": metadata,
            }

        # --------------------------------------------------------------
        # ORM/object fallback
        # --------------------------------------------------------------

        chunk_id = (
            getattr(
                result,
                "chunk_id",
                None,
            )
            or getattr(
                result,
                "id",
                None,
            )
        )

        document_id = getattr(
            result,
            "document_id",
            None,
        )

        document_version_id = getattr(
            result,
            "document_version_id",
            None,
        )

        collection_id = getattr(
            result,
            "collection_id",
            None,
        )

        content = (
            getattr(result, "content", None)
            or getattr(result, "text", None)
            or ""
        )

        metadata_value = (
            getattr(result, "metadata_", None)
            or getattr(result, "metadata", None)
            or {}
        )

        if isinstance(
            metadata_value,
            Mapping,
        ):
            metadata = dict(metadata_value)
        else:
            try:
                metadata = dict(metadata_value)
            except (
                TypeError,
                ValueError,
            ):
                metadata = {}

        raw_score = getattr(
            result,
            "score",
            0.5,
        )

        try:
            score = float(raw_score)
        except (
            TypeError,
            ValueError,
        ):
            score = 0.5

        return {
            "id": (
                str(chunk_id)
                if chunk_id is not None
                else None
            ),
            "chunk_id": (
                str(chunk_id)
                if chunk_id is not None
                else None
            ),
            "document_id": (
                str(document_id)
                if document_id is not None
                else None
            ),
            "document_version_id": (
                str(document_version_id)
                if document_version_id is not None
                else None
            ),
            "collection_id": (
                str(collection_id)
                if collection_id is not None
                else None
            ),
            "content": str(content),
            "score": max(
                0.0,
                min(score, 1.0),
            ),
            "metadata": metadata,
        }


# ============================================================================
# RETRIEVAL PIPELINE
# ============================================================================

async def get_retrieval_pipeline(
    retriever: Retriever = Depends(
        get_retriever
    ),
    repository: SearchRepository = Depends(
        get_search_repository
    ),
) -> RetrievalPipeline:
    """
    Build complete retrieval pipeline.
    """

    semantic_search = SemanticSearch(
        retriever=RetrieverAdapter(
            retriever=retriever,
        ),
    )

    keyword_backend = KeywordSearchBackend(
        repository=repository,
    )

    keyword_search = KeywordSearch(
        search_engine=keyword_backend,
    )

    hybrid_search = HybridSearch(
        semantic_search=semantic_search,
        keyword_search=keyword_search,
        semantic_weight=0.70,
        keyword_weight=0.30,
    )

    reranker = Reranker()

    return RetrievalPipeline(
        semantic_search=semantic_search,
        keyword_search=keyword_search,
        hybrid_search=hybrid_search,
        reranker=reranker,
    )


# ============================================================================
# SEARCH SERVICE
# ============================================================================

async def get_search_service(
    retrieval_pipeline: RetrievalPipeline = Depends(
        get_retrieval_pipeline
    ),
) -> SearchService:
    """
    Create SearchService.
    """

    from app.knowledge.query.query_parser import (
        QueryParser,
    )

    return SearchService(
        pipeline=retrieval_pipeline,
        query_parser=QueryParser(),
    )


# ============================================================================
# RETRIEVER ADAPTER
# ============================================================================

class RetrieverAdapter:
    """
    Adapter between Retriever and SemanticSearch.
    """

    def __init__(
        self,
        retriever: Retriever,
    ) -> None:
        self.retriever = retriever

    async def search(
        self,
        query: str,
        top_k: int = 10,
        filters: Mapping[str, Any] | None = None,
    ) -> list[dict[str, Any]]:

        return await self.retriever.search(
            query=query,
            top_k=top_k,
            filters=dict(filters or {}),
        )

    async def search_similar(
        self,
        document_id: str,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:

        return await self.retriever.search_similar(
            document_id=document_id,
            top_k=top_k,
        )


# ============================================================================
# POST /knowledge/
# ============================================================================

@router.post(
    "/",
    response_model=SearchResponse,
)
async def search(
    request: SearchRequest,
    service: SearchService = Depends(
        get_search_service
    ),
):
    """
    Search enterprise knowledge.
    """

    try:

        result = await service.search(
            query=request.query,
            search_type=request.search_type,
            top_k=request.top_k,
            filters=request.filters,
            collection_id=request.collection_id,
            score_threshold=request.score_threshold,
        )

        if isinstance(
            result,
            SearchResponse,
        ):
            return result

        return SearchResponse(
            **result
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:

        import logging

        logging.getLogger(__name__).exception(
            "Knowledge search failed"
        )

        raise HTTPException(
            status_code=500,
            detail="Knowledge search failed.",
        ) from exc


# ============================================================================
# POST /knowledge/hybrid/
# ============================================================================

@router.post(
    "/hybrid/",
    response_model=SearchResponse,
)
async def hybrid_search(
    request: SearchRequest,
    service: SearchService = Depends(
        get_search_service
    ),
):
    """
    Explicit hybrid search endpoint.
    """

    try:

        result = await service.hybrid_search(
            query=request.query,
            top_k=request.top_k,
            filters=request.filters,
            collection_id=request.collection_id,
            score_threshold=request.score_threshold,
        )

        if isinstance(
            result,
            SearchResponse,
        ):
            return result

        return SearchResponse(
            **result
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:

        import logging

        logging.getLogger(__name__).exception(
            "Hybrid knowledge search failed"
        )

        raise HTTPException(
            status_code=500,
            detail="Hybrid knowledge search failed.",
        ) from exc


# ============================================================================
# GET /knowledge/history
# ============================================================================

@router.get(
    "/history",
)
async def search_history(
    service: SearchService = Depends(
        get_search_service
    ),
):
    """
    Return search history.
    """

    try:
        return await service.history()

    except Exception as exc:

        import logging

        logging.getLogger(__name__).exception(
            "Knowledge search history failed"
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve search history.",
        ) from exc


# ============================================================================
# GET /knowledge/similar/{document_id}
# ============================================================================

@router.get(
    "/similar/{document_id}",
)
async def similar_documents(
    document_id: str,
    top_k: int = 5,
    service: SearchService = Depends(
        get_search_service
    ),
):
    """
    Retrieve documents similar to a given document.
    """

    try:

        return await service.similar_documents(
            document_id=document_id,
            top_k=top_k,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except NotImplementedError as exc:

        raise HTTPException(
            status_code=501,
            detail=str(exc),
        ) from exc

    except Exception as exc:

        import logging

        logging.getLogger(__name__).exception(
            "Similar document search failed"
        )

        raise HTTPException(
            status_code=500,
            detail="Similar document search failed.",
        ) from exc


__all__ = [
    "router",
]