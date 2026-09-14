"""
app/knowledge/services/search_service.py

Application service for enterprise knowledge search.

Responsibilities
----------------
- Validate user search requests.
- Parse natural-language queries.
- Dispatch semantic / keyword / hybrid retrieval.
- Apply score filtering.
- Normalize API results.
- Return a response compatible with SearchResponse.

Search flow
-----------

    SearchRequest
         |
         v
    SearchService
         |
         +--> QueryParser
         |
         v
    RetrievalPipeline
         |
         +--> semantic
         +--> keyword
         +--> hybrid
         |
         v
    Score filtering
         |
         v
    Result normalization
         |
         v
    SearchResponse-compatible dictionary
"""

from __future__ import annotations

from collections.abc import Mapping
from time import perf_counter
from typing import Any


class SearchService:
    """
    Application-level knowledge search service.

    This service is responsible for orchestrating knowledge retrieval.
    It does not directly access the database or vector store.
    """

    SEARCH_TYPES = {
        "semantic",
        "keyword",
        "hybrid",
    }

    MAX_TOP_K = 100

    def __init__(
        self,
        pipeline: Any,
        query_parser: Any | None = None,
    ) -> None:

        if pipeline is None:
            raise ValueError(
                "pipeline is required"
            )

        self.pipeline = pipeline
        self.query_parser = query_parser

    # ==================================================================
    # SEARCH
    # ==================================================================

    async def search(
        self,
        query: str,
        search_type: str = "semantic",
        top_k: int = 10,
        filters: Mapping[str, Any] | None = None,
        collection_id: str | None = None,
        score_threshold: float | None = None,
    ) -> dict[str, Any]:
        """
        Execute a knowledge search.

        Exhaustive queries such as:

            find all invoices
            show all contracts
            list all resumes

        automatically use MAX_TOP_K so that the retrieval layer has a
        chance to return every matching result available through the
        configured retrieval backend.
        """

        started_at = perf_counter()

        # --------------------------------------------------------------
        # Validate query
        # --------------------------------------------------------------

        query = (query or "").strip()

        if not query:
            raise ValueError(
                "Search query cannot be empty."
            )

        # --------------------------------------------------------------
        # Validate search type
        # --------------------------------------------------------------

        search_type = (
            search_type or "semantic"
        ).lower()

        if search_type not in self.SEARCH_TYPES:
            raise ValueError(
                f"Unsupported search_type: {search_type}"
            )

        # --------------------------------------------------------------
        # Validate top_k
        # --------------------------------------------------------------

        requested_top_k = self._validate_top_k(
            top_k
        )

        # --------------------------------------------------------------
        # Validate score threshold
        # --------------------------------------------------------------

        if score_threshold is not None:

            try:
                score_threshold = float(
                    score_threshold
                )
            except (
                TypeError,
                ValueError,
            ) as exc:

                raise ValueError(
                    "score_threshold must be a number."
                ) from exc

            if not 0.0 <= score_threshold <= 1.0:
                raise ValueError(
                    "score_threshold must be between 0 and 1."
                )

        # --------------------------------------------------------------
        # Parse query
        # --------------------------------------------------------------

        parsed_query = None

        if self.query_parser is not None:

            parse_method = getattr(
                self.query_parser,
                "parse",
                None,
            )

            if parse_method is not None:

                parsed_query = parse_method(
                    query
                )

                if hasattr(
                    parsed_query,
                    "__await__",
                ):
                    parsed_query = await parsed_query

        # --------------------------------------------------------------
        # Normalize parsed query
        # --------------------------------------------------------------

        normalized_query = query

        parsed_filters: dict[str, Any] = {}

        exhaustive = False

        if parsed_query is not None:

            normalized_query = getattr(
                parsed_query,
                "normalized_query",
                None,
            ) or query

            exhaustive = bool(
                getattr(
                    parsed_query,
                    "exhaustive",
                    False,
                )
            )

            filter_object = getattr(
                parsed_query,
                "filters",
                None,
            )

            if filter_object is not None:

                # ------------------------------------------------------
                # Filter object with to_dict()
                # ------------------------------------------------------

                to_dict = getattr(
                    filter_object,
                    "to_dict",
                    None,
                )

                if to_dict is not None:

                    parsed_filters = (
                        to_dict()
                        or {}
                    )

                # ------------------------------------------------------
                # Mapping-based filters
                # ------------------------------------------------------

                elif isinstance(
                    filter_object,
                    Mapping,
                ):

                    parsed_filters = dict(
                        filter_object
                    )

        # --------------------------------------------------------------
        # Merge filters
        # --------------------------------------------------------------

        effective_filters = dict(
            parsed_filters
        )

        if filters:
            effective_filters.update(
                dict(filters)
            )

        # --------------------------------------------------------------
        # Exhaustive search handling
        # --------------------------------------------------------------
        #
        # "find all invoices" should not be limited to the default
        # top_k=10.
        #
        # We cap at MAX_TOP_K rather than using an unlimited query,
        # because the API contract already defines a maximum result
        # window.
        # --------------------------------------------------------------

        if exhaustive:
            effective_top_k = self.MAX_TOP_K
        else:
            effective_top_k = requested_top_k

        # --------------------------------------------------------------
        # Collection handling
        # --------------------------------------------------------------

        # collection_id remains part of the public API contract.
        #
        # It is intentionally not injected into generic metadata filters
        # because the lower-level retrieval implementation is responsible
        # for collection-aware filtering.

        # --------------------------------------------------------------
        # Retrieval
        # --------------------------------------------------------------

        results = await self._retrieve(
            query=normalized_query,
            search_type=search_type,
            top_k=effective_top_k,
            filters=effective_filters,
        )

        # --------------------------------------------------------------
        # Ensure retrieval result is a list
        # --------------------------------------------------------------

        if results is None:
            results = []

        elif not isinstance(
            results,
            list,
        ):
            results = list(results)

        # --------------------------------------------------------------
        # Score filtering
        # --------------------------------------------------------------

        if score_threshold is not None:

            filtered_results: list[
                Mapping[str, Any]
            ] = []

            for result in results:

                if not isinstance(
                    result,
                    Mapping,
                ):
                    continue

                try:
                    score = float(
                        result.get(
                            "score",
                            0.0,
                        )
                        or 0.0
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    score = 0.0

                if score >= score_threshold:
                    filtered_results.append(
                        result
                    )

            results = filtered_results

        # --------------------------------------------------------------
        # Normalize results
        # --------------------------------------------------------------

        normalized_results = [
            self._normalize_result(
                result
            )
            for result in results
            if isinstance(
                result,
                Mapping,
            )
        ]

        # --------------------------------------------------------------
        # Calculate elapsed time
        # --------------------------------------------------------------

        elapsed_ms = (
            perf_counter() - started_at
        ) * 1000.0

        # --------------------------------------------------------------
        # API response
        # --------------------------------------------------------------

        return {
            "query": query,
            "total_results": len(
                normalized_results
            ),
            "elapsed_ms": elapsed_ms,
            "search_type": search_type,
            "results": normalized_results,
        }

    # ==================================================================
    # HYBRID SEARCH
    # ==================================================================

    async def hybrid_search(
        self,
        query: str,
        top_k: int = 10,
        filters: Mapping[str, Any] | None = None,
        collection_id: str | None = None,
        score_threshold: float | None = None,
    ) -> dict[str, Any]:

        return await self.search(
            query=query,
            search_type="hybrid",
            top_k=top_k,
            filters=filters,
            collection_id=collection_id,
            score_threshold=score_threshold,
        )

    # ==================================================================
    # RETRIEVE
    # ==================================================================

    async def _retrieve(
        self,
        query: str,
        search_type: str,
        top_k: int,
        filters: Mapping[str, Any] | None,
    ) -> list[dict[str, Any]]:

        # --------------------------------------------------------------
        # Semantic
        # --------------------------------------------------------------

        if search_type == "semantic":

            results = await self.pipeline.retrieve(
                query=query,
                top_k=top_k,
                filters=filters,
            )

            return self._ensure_result_list(
                results
            )

        # --------------------------------------------------------------
        # Keyword
        # --------------------------------------------------------------

        if search_type == "keyword":

            results = await self.pipeline.keyword_search(
                query=query,
                top_k=top_k,
                filters=filters,
            )

            return self._ensure_result_list(
                results
            )

        # --------------------------------------------------------------
        # Hybrid
        # --------------------------------------------------------------

        if search_type == "hybrid":

            results = await self.pipeline.hybrid_search(
                query=query,
                top_k=top_k,
                filters=filters,
            )

            return self._ensure_result_list(
                results
            )

        raise ValueError(
            f"Unsupported search_type: {search_type}"
        )

    # ==================================================================
    # SIMILAR DOCUMENTS
    # ==================================================================

    async def similar_documents(
        self,
        document_id: str,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:

        if not document_id:
            raise ValueError(
                "document_id is required."
            )

        top_k = self._validate_top_k(
            top_k
        )

        results = await self.pipeline.retrieve_similar(
            document_id=document_id,
            top_k=top_k,
        )

        return self._ensure_result_list(
            results
        )

    # ==================================================================
    # HISTORY
    # ==================================================================

    async def history(
        self,
    ) -> list[dict[str, Any]]:

        return []

    # ==================================================================
    # RESULT NORMALIZATION
    # ==================================================================

    @staticmethod
    def _normalize_result(
        result: Mapping[str, Any],
    ) -> dict[str, Any]:

        metadata = (
            result.get("metadata")
            or {}
        )

        if not isinstance(
            metadata,
            dict,
        ):

            try:
                metadata = dict(
                    metadata
                )
            except (
                TypeError,
                ValueError,
            ):

                metadata = {}

        try:

            score = float(
                result.get(
                    "score",
                    0.0,
                )
                or 0.0
            )

        except (
            TypeError,
            ValueError,
        ):

            score = 0.0

        semantic_score = (
            SearchService._safe_float(
                result.get(
                    "semantic_score"
                )
            )
        )

        keyword_score = (
            SearchService._safe_float(
                result.get(
                    "keyword_score"
                )
            )
        )

        return {
            "chunk_id": result.get(
                "chunk_id"
            ),
            "document_id": result.get(
                "document_id"
            ),
            "document_version_id": result.get(
                "document_version_id"
            ),
            "collection_id": result.get(
                "collection_id"
            ),
            "content": result.get(
                "content",
                "",
            ) or "",
            "score": score,
            "metadata": metadata,
            "semantic_score": semantic_score,
            "keyword_score": keyword_score,
        }

    # ==================================================================
    # RESULT HELPERS
    # ==================================================================

    @staticmethod
    def _ensure_result_list(
        results: Any,
    ) -> list[dict[str, Any]]:

        if results is None:
            return []

        nested_results = getattr(
            results,
            "results",
            None,
        )

        if nested_results is not None:
            results = nested_results

        if isinstance(
            results,
            list,
        ):

            return [
                dict(result)
                for result in results
                if isinstance(
                    result,
                    Mapping,
                )
            ]

        try:

            return [
                dict(result)
                for result in results
                if isinstance(
                    result,
                    Mapping,
                )
            ]

        except TypeError:

            return []

    @staticmethod
    def _safe_float(
        value: Any,
    ) -> float | None:

        if value is None:
            return None

        try:
            return float(value)

        except (
            TypeError,
            ValueError,
        ):

            return None

    # ==================================================================
    # VALIDATION
    # ==================================================================

    @classmethod
    def _validate_top_k(
        cls,
        top_k: int,
    ) -> int:

        try:

            top_k = int(
                top_k
            )

        except (
            TypeError,
            ValueError,
        ) as exc:

            raise ValueError(
                "top_k must be an integer."
            ) from exc

        if top_k < 1:

            raise ValueError(
                "top_k must be >= 1."
            )

        return min(
            top_k,
            cls.MAX_TOP_K,
        )


__all__ = [
    "SearchService",
]