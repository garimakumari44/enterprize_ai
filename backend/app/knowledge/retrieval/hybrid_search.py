"""
app/knowledge/retrieval/hybrid_search.py

Hybrid retrieval combining:

    semantic search
    +
    keyword search

The implementation intentionally executes the two searches sequentially
because the current FastAPI dependency graph may provide both paths with
the same SQLAlchemy AsyncSession.

Once separate sessions are guaranteed, this can safely be parallelized.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class HybridSearch:
    """
    Combines semantic and keyword retrieval.
    """

    def __init__(
        self,
        semantic_search: Any,
        keyword_search: Any,
        semantic_weight: float = 0.70,
        keyword_weight: float = 0.30,
    ) -> None:

        if semantic_search is None:
            raise ValueError(
                "semantic_search is required"
            )

        if keyword_search is None:
            raise ValueError(
                "keyword_search is required"
            )

        if semantic_weight < 0:
            raise ValueError(
                "semantic_weight must be >= 0"
            )

        if keyword_weight < 0:
            raise ValueError(
                "keyword_weight must be >= 0"
            )

        total = semantic_weight + keyword_weight

        if total <= 0:
            raise ValueError(
                "At least one hybrid search weight must be > 0"
            )

        self.semantic_search = semantic_search
        self.keyword_search = keyword_search

        self.semantic_weight = (
            semantic_weight / total
        )

        self.keyword_weight = (
            keyword_weight / total
        )

    # ------------------------------------------------------------------
    # SEARCH
    # ------------------------------------------------------------------

    async def search(
        self,
        query: str,
        top_k: int = 10,
        filters: Mapping[str, Any] | None = None,
    ) -> list[dict[str, Any]]:

        query = (query or "").strip()

        if not query:
            return []

        top_k = max(
            1,
            min(int(top_k), 100),
        )

        # --------------------------------------------------------------
        # IMPORTANT
        #
        # Sequential execution avoids sharing one AsyncSession across
        # concurrent database operations.
        # --------------------------------------------------------------

        semantic_results = await self.semantic_search.search(
            query=query,
            top_k=top_k,
            filters=filters,
        )

        keyword_results = await self.keyword_search.search(
            query=query,
            top_k=top_k,
            filters=filters,
        )

        return self._merge_results(
            semantic_results=semantic_results,
            keyword_results=keyword_results,
            top_k=top_k,
        )

    # ------------------------------------------------------------------
    # MERGE
    # ------------------------------------------------------------------

    def _merge_results(
        self,
        semantic_results: list[Any],
        keyword_results: list[Any],
        top_k: int,
    ) -> list[dict[str, Any]]:

        merged: dict[str, dict[str, Any]] = {}

        # --------------------------------------------------------------
        # Semantic
        # --------------------------------------------------------------

        for raw in semantic_results:

            result = self._normalize_result(raw)

            key = self._result_key(result)

            if key is None:
                continue

            semantic_score = float(
                result.get("score") or 0.0
            )

            merged[key] = {
                **result,
                "semantic_score": semantic_score,
                "keyword_score": 0.0,
                "score": (
                    semantic_score
                    * self.semantic_weight
                ),
            }

        # --------------------------------------------------------------
        # Keyword
        # --------------------------------------------------------------

        for raw in keyword_results:

            result = self._normalize_result(raw)

            key = self._result_key(result)

            if key is None:
                continue

            keyword_score = float(
                result.get("score") or 0.0
            )

            if key in merged:

                existing = merged[key]

                semantic_score = float(
                    existing.get(
                        "semantic_score",
                        0.0,
                    )
                )

                existing["keyword_score"] = (
                    keyword_score
                )

                existing["score"] = (
                    semantic_score
                    * self.semantic_weight
                    +
                    keyword_score
                    * self.keyword_weight
                )

            else:

                merged[key] = {
                    **result,
                    "semantic_score": 0.0,
                    "keyword_score": keyword_score,
                    "score": (
                        keyword_score
                        * self.keyword_weight
                    ),
                }

        # --------------------------------------------------------------
        # Sort
        # --------------------------------------------------------------

        results = list(merged.values())

        results.sort(
            key=lambda item: float(
                item.get("score") or 0.0
            ),
            reverse=True,
        )

        return results[:top_k]

    # ------------------------------------------------------------------
    # NORMALIZATION
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_result(
        result: Any,
    ) -> dict[str, Any]:

        if isinstance(result, Mapping):

            metadata = (
                result.get("metadata")
                or result.get("metadata_")
                or {}
            )

            if not isinstance(metadata, dict):
                metadata = dict(metadata)

            return {
                "id": result.get(
                    "id"
                ),
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
                "content": (
                    result.get("content")
                    or result.get("text")
                    or ""
                ),
                "score": float(
                    result.get(
                        "score",
                        result.get(
                            "relevance_score",
                            0.0,
                        ),
                    )
                    or 0.0
                ),
                "metadata": metadata,
            }

        metadata = (
            getattr(result, "metadata_", None)
            or getattr(result, "metadata", None)
            or {}
        )

        if not isinstance(metadata, dict):
            metadata = dict(metadata)

        return {
            "id": getattr(
                result,
                "id",
                None,
            ),
            "chunk_id": getattr(
                result,
                "chunk_id",
                getattr(result, "id", None),
            ),
            "document_id": getattr(
                result,
                "document_id",
                None,
            ),
            "document_version_id": getattr(
                result,
                "document_version_id",
                None,
            ),
            "collection_id": getattr(
                result,
                "collection_id",
                None,
            ),
            "content": (
                getattr(result, "content", None)
                or getattr(result, "text", None)
                or ""
            ),
            "score": float(
                getattr(
                    result,
                    "score",
                    0.0,
                )
                or 0.0
            ),
            "metadata": metadata,
        }

    # ------------------------------------------------------------------
    # DEDUPLICATION KEY
    # ------------------------------------------------------------------

    @staticmethod
    def _result_key(
        result: Mapping[str, Any],
    ) -> str | None:

        chunk_id = result.get("chunk_id")

        if chunk_id is not None:
            return f"chunk:{chunk_id}"

        result_id = result.get("id")

        if result_id is not None:
            return f"id:{result_id}"

        document_version_id = result.get(
            "document_version_id"
        )

        if document_version_id is not None:
            return (
                f"document_version:"
                f"{document_version_id}"
            )

        return None


__all__ = ["HybridSearch"]