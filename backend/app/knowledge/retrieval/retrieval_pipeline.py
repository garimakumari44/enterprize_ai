"""
app/knowledge/retrieval/retrieval_pipeline.py

Canonical retrieval orchestration.

Flow:

    query
      |
      +-----------------------+
      |                       |
      v                       v
  semantic                keyword
      |                       |
      +-----------+-----------+
                  |
                  v
               hybrid
                  |
                  v
               reranker
                  |
                  v
               results
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class RetrievalPipeline:
    """
    Central retrieval orchestration layer.
    """

    MAX_TOP_K = 100

    def __init__(
        self,
        semantic_search: Any,
        keyword_search: Any,
        hybrid_search: Any,
        reranker: Any | None = None,
    ) -> None:

        if semantic_search is None:
            raise ValueError(
                "semantic_search is required"
            )

        if keyword_search is None:
            raise ValueError(
                "keyword_search is required"
            )

        if hybrid_search is None:
            raise ValueError(
                "hybrid_search is required"
            )

        self.semantic_search = semantic_search
        self.keyword_search_engine = keyword_search
        self.hybrid_search_engine = hybrid_search
        self.reranker = reranker

    # ==================================================================
    # SEMANTIC
    # ==================================================================

    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        filters: Mapping[str, Any] | None = None,
    ) -> list[dict[str, Any]]:

        query = (query or "").strip()

        if not query:
            return []

        top_k = self._validate_top_k(
            top_k
        )

        # --------------------------------------------------------------
        # Retrieve a larger candidate pool before reranking.
        # --------------------------------------------------------------

        candidate_k = min(
            max(top_k * 10, 50),
            500,
        )

        candidates = await self.semantic_search.search(
            query=query,
            top_k=candidate_k,
            filters=filters,
        )

        candidates = self._unwrap_results(
            candidates
        )

        normalized: list[dict[str, Any]] = []

        for candidate in candidates:

            item = self._normalize_candidate(
                candidate
            )

            if item is not None:
                normalized.append(
                    item
                )

        return await self._rerank(
            query=query,
            documents=normalized,
            top_k=top_k,
        )

    # ==================================================================
    # KEYWORD
    # ==================================================================

    async def keyword_search(
        self,
        query: str,
        top_k: int = 10,
        filters: Mapping[str, Any] | None = None,
    ) -> list[dict[str, Any]]:

        query = (query or "").strip()

        if not query:
            return []

        top_k = self._validate_top_k(
            top_k
        )

        results = await self.keyword_search_engine.search(
            query=query,
            top_k=top_k,
            filters=filters,
        )

        results = self._unwrap_results(
            results
        )

        normalized: list[dict[str, Any]] = []

        for result in results:

            candidate = self._normalize_candidate(
                result
            )

            if candidate is not None:
                normalized.append(
                    candidate
                )

        return normalized[:top_k]

    # ==================================================================
    # HYBRID
    # ==================================================================

    async def hybrid_search(
        self,
        query: str,
        top_k: int = 10,
        filters: Mapping[str, Any] | None = None,
    ) -> list[dict[str, Any]]:

        query = (query or "").strip()

        if not query:
            return []

        top_k = self._validate_top_k(
            top_k
        )

        results = await self.hybrid_search_engine.search(
            query=query,
            top_k=top_k,
            filters=filters,
        )

        results = self._unwrap_results(
            results
        )

        normalized: list[dict[str, Any]] = []

        for result in results:

            candidate = self._normalize_candidate(
                result
            )

            if candidate is not None:
                normalized.append(
                    candidate
                )

        return normalized[:top_k]

    # ==================================================================
    # SIMILAR
    # ==================================================================

    async def retrieve_similar(
        self,
        document_id: str,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:

        top_k = self._validate_top_k(
            top_k
        )

        search_similar = getattr(
            self.semantic_search,
            "search_similar",
            None,
        )

        if search_similar is None:

            retriever = getattr(
                self.semantic_search,
                "retriever",
                None,
            )

            search_similar = getattr(
                retriever,
                "search_similar",
                None,
            )

        if search_similar is None:
            raise NotImplementedError(
                "Semantic search does not implement "
                "search_similar()."
            )

        results = search_similar(
            document_id=document_id,
            top_k=top_k,
        )

        if hasattr(
            results,
            "__await__",
        ):
            results = await results

        results = self._unwrap_results(
            results
        )

        normalized: list[dict[str, Any]] = []

        for result in results:

            candidate = self._normalize_candidate(
                result
            )

            if candidate is not None:
                normalized.append(
                    candidate
                )

        return normalized[:top_k]

    # ==================================================================
    # RERANK
    # ==================================================================

    async def _rerank(
        self,
        query: str,
        documents: list[dict[str, Any]],
        top_k: int,
    ) -> list[dict[str, Any]]:

        if not documents:
            return []

        # --------------------------------------------------------------
        # No reranker
        # --------------------------------------------------------------

        if self.reranker is None:

            documents.sort(
                key=lambda item: float(
                    item.get("score")
                    or 0.0
                ),
                reverse=True,
            )

            return documents[:top_k]

        # --------------------------------------------------------------
        # Discover reranker method
        # --------------------------------------------------------------

        rerank_method = getattr(
            self.reranker,
            "rerank",
            None,
        )

        rank_method = getattr(
            self.reranker,
            "rank",
            None,
        )

        if (
            rerank_method is None
            and rank_method is None
        ):

            documents.sort(
                key=lambda item: float(
                    item.get("score")
                    or 0.0
                ),
                reverse=True,
            )

            return documents[:top_k]

        # --------------------------------------------------------------
        # Execute reranker
        # --------------------------------------------------------------

        if rerank_method is not None:

            result = rerank_method(
                query=query,
                documents=documents,
                top_k=top_k,
            )

        else:

            result = rank_method(
                query=query,
                documents=documents,
                top_k=top_k,
            )

        if hasattr(
            result,
            "__await__",
        ):
            result = await result

        result = self._unwrap_results(
            result
        )

        if not result:
            return documents[:top_k]

        normalized: list[
            dict[str, Any]
        ] = []

        for item in result:

            candidate = self._normalize_candidate(
                item
            )

            if candidate is not None:
                normalized.append(
                    candidate
                )

        return normalized[:top_k]

    # ==================================================================
    # RESULT UNWRAPPING
    # ==================================================================

    @staticmethod
    def _unwrap_results(
        results: Any,
    ) -> list[Any]:
        """
        Normalize retrieval wrappers into a plain list.

        Supports:

            list
            tuple
            iterable
            object.results
            object.data
        """

        if results is None:
            return []

        # --------------------------------------------------------------
        # Standard result wrapper
        # --------------------------------------------------------------

        nested_results = getattr(
            results,
            "results",
            None,
        )

        if nested_results is not None:
            results = nested_results

        # --------------------------------------------------------------
        # Some search implementations expose .data
        # --------------------------------------------------------------

        if not isinstance(
            results,
            (list, tuple),
        ):

            nested_data = getattr(
                results,
                "data",
                None,
            )

            if nested_data is not None:
                results = nested_data

        # --------------------------------------------------------------
        # List / tuple
        # --------------------------------------------------------------

        if isinstance(
            results,
            (list, tuple),
        ):
            return list(results)

        # --------------------------------------------------------------
        # Generic iterable
        # --------------------------------------------------------------

        try:
            return list(results)

        except TypeError:
            return []

    # ==================================================================
    # NORMALIZATION
    # ==================================================================

    @staticmethod
    def _normalize_candidate(
        candidate: Any,
    ) -> dict[str, Any] | None:

        if candidate is None:
            return None

        # ==============================================================
        # Mapping
        # ==============================================================

        if isinstance(
            candidate,
            Mapping,
        ):

            metadata_value = (
                candidate.get("metadata")
                or candidate.get("metadata_")
                or {}
            )

            if isinstance(
                metadata_value,
                Mapping,
            ):

                metadata = dict(
                    metadata_value
                )

            else:

                try:
                    metadata = dict(
                        metadata_value
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    metadata = {}

            chunk_id = (
                candidate.get("chunk_id")
                or metadata.get("chunk_id")
                or candidate.get("id")
            )

            document_id = (
                candidate.get("document_id")
                or metadata.get("document_id")
            )

            document_version_id = (
                candidate.get(
                    "document_version_id"
                )
                or metadata.get(
                    "document_version_id"
                )
            )

            collection_id = (
                candidate.get(
                    "collection_id"
                )
                or metadata.get(
                    "collection_id"
                )
            )

            content = (
                candidate.get("content")
                or candidate.get("text")
                or ""
            )

            score = RetrievalPipeline._safe_score(
                candidate.get(
                    "score",
                    candidate.get(
                        "relevance_score",
                        0.0,
                    ),
                )
            )

            normalized = {
                "id": (
                    str(
                        candidate.get("id")
                    )
                    if candidate.get("id") is not None
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
                "score": score,
                "metadata": metadata,
            }

            if "semantic_score" in candidate:
                normalized[
                    "semantic_score"
                ] = candidate[
                    "semantic_score"
                ]

            if "keyword_score" in candidate:
                normalized[
                    "keyword_score"
                ] = candidate[
                    "keyword_score"
                ]

            return normalized

        # ==============================================================
        # Object result
        # ==============================================================

        metadata_value = (
            getattr(
                candidate,
                "metadata_",
                None,
            )
            or getattr(
                candidate,
                "metadata",
                None,
            )
            or {}
        )

        if isinstance(
            metadata_value,
            Mapping,
        ):

            metadata = dict(
                metadata_value
            )

        else:

            try:
                metadata = dict(
                    metadata_value
                )
            except (
                TypeError,
                ValueError,
            ):
                metadata = {}

        item_id = getattr(
            candidate,
            "id",
            None,
        )

        chunk_id = (
            getattr(
                candidate,
                "chunk_id",
                None,
            )
            or metadata.get(
                "chunk_id"
            )
            or item_id
        )

        document_id = (
            getattr(
                candidate,
                "document_id",
                None,
            )
            or metadata.get(
                "document_id"
            )
        )

        document_version_id = (
            getattr(
                candidate,
                "document_version_id",
                None,
            )
            or metadata.get(
                "document_version_id"
            )
        )

        collection_id = (
            getattr(
                candidate,
                "collection_id",
                None,
            )
            or metadata.get(
                "collection_id"
            )
        )

        content = (
            getattr(
                candidate,
                "content",
                None,
            )
            or getattr(
                candidate,
                "text",
                None,
            )
            or ""
        )

        score = RetrievalPipeline._safe_score(
            getattr(
                candidate,
                "score",
                0.0,
            )
        )

        normalized = {
            "id": (
                str(item_id)
                if item_id is not None
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
            "score": score,
            "metadata": metadata,
        }

        semantic_score = getattr(
            candidate,
            "semantic_score",
            None,
        )

        if semantic_score is not None:
            normalized[
                "semantic_score"
            ] = semantic_score

        keyword_score = getattr(
            candidate,
            "keyword_score",
            None,
        )

        if keyword_score is not None:
            normalized[
                "keyword_score"
            ] = keyword_score

        return normalized

    # ==================================================================
    # VALIDATION
    # ==================================================================

    @classmethod
    def _validate_top_k(
        cls,
        top_k: int,
    ) -> int:

        try:

            value = int(
                top_k
            )

        except (
            TypeError,
            ValueError,
        ) as exc:

            raise ValueError(
                "top_k must be an integer"
            ) from exc

        if value < 1:

            raise ValueError(
                "top_k must be >= 1"
            )

        return min(
            value,
            cls.MAX_TOP_K,
        )

    # ==================================================================
    # SAFE SCORE
    # ==================================================================

    @staticmethod
    def _safe_score(
        value: Any,
    ) -> float:

        try:

            score = float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            return 0.0

        if score != score:
            return 0.0

        if score == float("inf"):
            return 1.0

        if score == float("-inf"):
            return 0.0

        return max(
            0.0,
            min(
                score,
                1.0,
            ),
        )


__all__ = [
    "RetrievalPipeline",
]