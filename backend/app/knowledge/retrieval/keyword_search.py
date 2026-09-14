"""
app/knowledge/retrieval/keyword_search.py

Keyword retrieval adapter.

Architecture:

    RetrievalPipeline
          |
          v
    KeywordSearch
          |
          v
    SearchRepository
          |
          v
    PostgreSQL
"""

from __future__ import annotations

import inspect
from collections.abc import Mapping
from typing import Any


class KeywordSearch:
    """
    Generic keyword-search adapter.

    The underlying search engine may expose:

        search(query=..., limit=..., filters=...)

    or:

        search(query=..., top_k=..., filters=...)

    This class normalizes both interfaces.
    """

    MAX_TOP_K = 100

    def __init__(self, search_engine: Any) -> None:
        if search_engine is None:
            raise ValueError(
                "search_engine is required"
            )

        self.search_engine = search_engine

    # ==================================================================
    # SEARCH
    # ==================================================================

    async def search(
        self,
        query: str,
        top_k: int = 10,
        filters: Mapping[str, Any] | None = None,
    ) -> list[dict[str, Any]]:

        query = (query or "").strip()

        if not query:
            return []

        try:
            top_k = int(top_k)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "top_k must be an integer"
            ) from exc

        top_k = max(
            1,
            min(top_k, self.MAX_TOP_K),
        )

        results = await self._execute_search(
            query=query,
            top_k=top_k,
            filters=filters,
        )

        normalized: list[dict[str, Any]] = []

        for result in results:
            item = self._normalize_result(
                result
            )

            if item is not None:
                normalized.append(item)

        return normalized[:top_k]

    # ==================================================================
    # EXECUTION
    # ==================================================================

    async def _execute_search(
        self,
        query: str,
        top_k: int,
        filters: Mapping[str, Any] | None,
    ) -> list[Any]:

        search_method = getattr(
            self.search_engine,
            "search",
            None,
        )

        if not callable(search_method):
            raise RuntimeError(
                "Keyword search engine does not expose "
                "a callable search() method."
            )

        # First try the canonical interface.
        try:
            result = search_method(
                query=query,
                limit=top_k,
                filters=filters,
            )
        except TypeError as exc:

            error_text = str(exc).lower()

            # Only retry when the interface itself rejected `limit`.
            if (
                "limit" not in error_text
                and "unexpected keyword" not in error_text
                and "keyword argument" not in error_text
            ):
                raise

            result = search_method(
                query=query,
                top_k=top_k,
                filters=filters,
            )

        if inspect.isawaitable(result):
            result = await result

        if result is None:
            return []

        if isinstance(result, Mapping):
            return [result]

        return list(result)

    # ==================================================================
    # NORMALIZATION
    # ==================================================================

    @staticmethod
    def _normalize_result(
        result: Any,
    ) -> dict[str, Any] | None:

        if result is None:
            return None

        # --------------------------------------------------------------
        # Mapping
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
                except (TypeError, ValueError):
                    metadata = {}

            chunk_id = (
                result.get("chunk_id")
                or result.get("id")
                or metadata.get("chunk_id")
                or metadata.get("chunkId")
            )

            document_id = (
                result.get("document_id")
                or metadata.get("document_id")
                or metadata.get("documentId")
            )

            document_version_id = (
                result.get("document_version_id")
                or metadata.get("document_version_id")
                or metadata.get("documentVersionId")
            )

            collection_id = (
                result.get("collection_id")
                or metadata.get("collection_id")
                or metadata.get("collectionId")
            )

            content = (
                result.get("content")
                or result.get("text")
                or ""
            )

            raw_score = result.get(
                "score",
                result.get(
                    "relevance_score",
                    None,
                ),
            )

            # The repository may not provide a score.
            # Use a stable baseline rather than zero.
            if raw_score is None:
                raw_score = 0.5

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

            if collection_id is not None:
                metadata.setdefault(
                    "collection_id",
                    str(collection_id),
                )

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

        # --------------------------------------------------------------
        # ORM/object result
        # --------------------------------------------------------------

        chunk_id = getattr(
            result,
            "chunk_id",
            None,
        )

        if chunk_id is None:
            chunk_id = getattr(
                result,
                "id",
                None,
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
            except (TypeError, ValueError):
                metadata = {}

        raw_score = getattr(
            result,
            "score",
            None,
        )

        if raw_score is None:
            raw_score = 0.5

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


__all__ = ["KeywordSearch"]