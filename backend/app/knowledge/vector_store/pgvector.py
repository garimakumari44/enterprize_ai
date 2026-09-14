"""
app/knowledge/vector_store/pgvector.py

PostgreSQL + pgvector vector store.

Responsibilities
----------------
- Store document/chunk embeddings in PostgreSQL.
- Perform cosine-distance vector similarity search.
- Support metadata equality filters.
- Support numeric range filters.
- Support date range filters.
- Retrieve representative document vectors.
- Provide compatibility helpers used by the retrieval layer.

The SQLAlchemy AsyncSession is injected by the application.
PGVectorStore does not own the session lifecycle.
"""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Mapping, Sequence
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .base import VectorDocument


logger = logging.getLogger(__name__)


class PGVectorStore:
    """
    PostgreSQL vector store backed by pgvector.
    """

    DEFAULT_COLLECTION = "document_chunk_vectors"
    DEFAULT_TOP_K = 10
    MAX_TOP_K = 100

    DEFAULT_EMBEDDING_DIMENSION = 384

    _IDENTIFIER_PATTERN = re.compile(
        r"^[A-Za-z_][A-Za-z0-9_]*$"
    )

    _NUMERIC_PATTERN = r"^-?[0-9]+(?:\.[0-9]+)?$"

    _DATE_PATTERN = r"^\d{4}-\d{2}-\d{2}"

    _COMPARISON_OPERATORS = {
        "gt": ">",
        "gte": ">=",
        "lt": "<",
        "lte": "<=",
        "eq": "=",
        "ne": "!=",
    }

    def __init__(
        self,
        session: AsyncSession,
        embedding_dimension: int = DEFAULT_EMBEDDING_DIMENSION,
        collection: str = DEFAULT_COLLECTION,
        **kwargs: Any,
    ) -> None:
        self.session = session

        self.embedding_dimension = int(
            embedding_dimension
        )

        if self.embedding_dimension <= 0:
            raise ValueError(
                "embedding_dimension must be greater than zero."
            )

        self.collection = self._validate_identifier(
            collection,
            field_name="collection",
        )

        self.config = dict(kwargs)

    # ========================================================================
    # COLLECTION
    # ========================================================================

    async def ensure_collection(
        self,
        collection: str | None = None,
        *,
        dimension: int | None = None,
    ) -> None:
        """
        Ensure the vector table exists.

        `dimension` is optional for compatibility with VectorStoreManager.

        If supplied, it must match the provider's configured embedding
        dimension. This prevents accidentally creating a table with a
        different vector dimension from the embedding provider.
        """

        collection_name = self._resolve_collection(
            collection
        )

        if dimension is not None:
            resolved_dimension = int(dimension)

            if resolved_dimension <= 0:
                raise ValueError(
                    "Embedding dimension must be greater than zero."
                )

            if (
                resolved_dimension
                != self.embedding_dimension
            ):
                raise ValueError(
                    "Embedding dimension mismatch: "
                    f"provider is configured for "
                    f"{self.embedding_dimension}, "
                    f"but collection creation requested "
                    f"{resolved_dimension}."
                )

        await self.session.execute(
            text(
                "CREATE EXTENSION IF NOT EXISTS vector"
            )
        )

        sql = f"""
            CREATE TABLE IF NOT EXISTS {collection_name} (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                embedding VECTOR({self.embedding_dimension}) NOT NULL,
                metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb
            )
        """

        await self.session.execute(
            text(sql)
        )

        metadata_index_name = self._index_name(
            collection_name,
            "metadata",
        )

        await self.session.execute(
            text(
                f"""
                CREATE INDEX IF NOT EXISTS {metadata_index_name}
                ON {collection_name}
                USING GIN (metadata)
                """
            )
        )

        await self.session.commit()

    async def create_collection(
        self,
        collection: str | None = None,
        *,
        dimension: int | None = None,
    ) -> None:
        """
        Compatibility alias for ensure_collection().
        """

        await self.ensure_collection(
            collection=collection,
            dimension=dimension,
        )

    async def delete_collection(
        self,
        collection_name: str | None = None,
    ) -> None:
        """
        Drop a vector collection/table.
        """

        resolved_collection = self._resolve_collection(
            collection_name
        )

        await self.session.execute(
            text(
                f"DROP TABLE IF EXISTS {resolved_collection}"
            )
        )

        await self.session.commit()

    # ========================================================================
    # SEARCH
    # ========================================================================

    async def search(
        self,
        vector: Sequence[float],
        *,
        collection: str | None = None,
        top_k: int = DEFAULT_TOP_K,
        filters: Mapping[str, Any] | None = None,
    ) -> list[dict[str, Any]]:

        collection_name = self._resolve_collection(
            collection
        )

        limit = self._validate_top_k(top_k)

        normalized_vector = self._validate_vector(
            vector
        )

        where_sql, bind_params = (
            self._build_filter_clause(
                filters or {}
            )
        )

        vector_literal = (
            self._vector_to_pgvector_literal(
                normalized_vector
            )
        )

        sql = f"""
            SELECT
                id,
                content,
                metadata,
                1 - (
                    embedding <=> CAST(:query_vector AS vector)
                ) AS score
            FROM {collection_name}
            {where_sql}
            ORDER BY embedding <=> CAST(:query_vector AS vector)
            LIMIT :limit
        """

        params: dict[str, Any] = {
            "query_vector": vector_literal,
            "limit": limit,
            **bind_params,
        }

        result = await self.session.execute(
            text(sql),
            params,
        )

        rows = result.mappings().all()

        return [
            self._normalize_search_result(row)
            for row in rows
        ]

    async def similarity_search(
        self,
        vector: Sequence[float],
        *,
        collection: str | None = None,
        top_k: int = DEFAULT_TOP_K,
        filters: Mapping[str, Any] | None = None,
    ) -> list[dict[str, Any]]:

        return await self.search(
            vector,
            collection=collection,
            top_k=top_k,
            filters=filters,
        )

    # ========================================================================
    # UPSERT
    # ========================================================================

    async def upsert(
        self,
        *,
        documents: Sequence[VectorDocument] | None = None,
        collection: str | None = None,
        record_id: str | None = None,
        vector: Sequence[float] | None = None,
        content: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Insert or update one or more vector documents.

        Canonical manager API:

            await store.upsert(
                documents=[VectorDocument(...)]
            )

        Legacy single-document API is also supported:

            await store.upsert(
                record_id="chunk-1",
                vector=[...],
                content="...",
                metadata={...},
            )
        """

        collection_name = self._resolve_collection(
            collection
        )

        # --------------------------------------------------------------------
        # Normalize input into VectorDocument objects.
        # --------------------------------------------------------------------

        if documents is not None:
            document_list = list(documents)
        else:
            if record_id is None:
                raise ValueError(
                    "record_id is required when documents "
                    "are not provided."
                )

            if vector is None:
                raise ValueError(
                    "vector is required when documents "
                    "are not provided."
                )

            document_list = [
                VectorDocument(
                    id=str(record_id),
                    vector=vector,
                    content=content or "",
                    metadata=metadata or {},
                )
            ]

        if not document_list:
            return {
                "indexed": 0,
            }

        indexed = 0

        for document in document_list:
            document_id = str(
                getattr(document, "id", None)
            )

            if not document_id:
                raise ValueError(
                    "VectorDocument.id cannot be empty."
                )

            document_vector = getattr(
                document,
                "vector",
                None,
            )

            if document_vector is None:
                raise ValueError(
                    f"VectorDocument '{document_id}' "
                    "does not contain a vector."
                )

            document_content = getattr(
                document,
                "content",
                "",
            )

            document_metadata = getattr(
                document,
                "metadata",
                {},
            )

            normalized_vector = (
                self._validate_vector(
                    document_vector
                )
            )

            normalized_metadata = (
                self._normalize_metadata(
                    document_metadata or {}
                )
            )

            vector_literal = (
                self._vector_to_pgvector_literal(
                    normalized_vector
                )
            )

            sql = f"""
                INSERT INTO {collection_name}
                    (
                        id,
                        content,
                        embedding,
                        metadata
                    )
                VALUES
                    (
                        :id,
                        :content,
                        CAST(:embedding AS vector),
                        CAST(:metadata AS jsonb)
                    )
                ON CONFLICT (id)
                DO UPDATE SET
                    content = EXCLUDED.content,
                    embedding = EXCLUDED.embedding,
                    metadata = EXCLUDED.metadata
            """

            await self.session.execute(
                text(sql),
                {
                    "id": document_id,
                    "content": str(
                        document_content or ""
                    ),
                    "embedding": vector_literal,
                    "metadata": json.dumps(
                        normalized_metadata,
                        default=self._json_default,
                    ),
                },
            )

            indexed += 1

        await self.session.commit()

        return {
            "indexed": indexed,
        }

    # ========================================================================
    # DELETE
    # ========================================================================

    async def delete(
        self,
        ids: Sequence[str] | None = None,
        *,
        collection: str | None = None,
        record_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Delete one or more vector records.

        Supports both:

            ids=["chunk-1", "chunk-2"]

        and legacy:

            record_id="chunk-1"
        """

        collection_name = self._resolve_collection(
            collection
        )

        resolved_ids: list[str] = []

        if ids is not None:
            resolved_ids.extend(
                str(item)
                for item in ids
                if item is not None
            )

        if record_id is not None:
            resolved_ids.append(
                str(record_id)
            )

        if not resolved_ids:
            return {
                "deleted": 0,
            }

        result = await self.session.execute(
            text(
                f"""
                DELETE FROM {collection_name}
                WHERE id = ANY(:ids)
                """
            ),
            {
                "ids": resolved_ids,
            },
        )

        await self.session.commit()

        deleted = (
            result.rowcount
            if result.rowcount is not None
            else 0
        )

        return {
            "deleted": int(deleted),
        }

    # ========================================================================
    # DOCUMENT VECTOR
    # ========================================================================

    async def get_document_vector(
        self,
        document_id: str,
        *,
        collection: str | None = None,
    ) -> list[float] | None:

        collection_name = self._resolve_collection(
            collection
        )

        if not document_id:
            raise ValueError(
                "document_id cannot be empty."
            )

        sql = f"""
            SELECT embedding::text AS embedding
            FROM {collection_name}
            WHERE metadata ->> 'document_id' = :document_id
            ORDER BY id
            LIMIT 1
        """

        result = await self.session.execute(
            text(sql),
            {
                "document_id": str(
                    document_id
                ),
            },
        )

        row = result.mappings().first()

        if row is None:
            return None

        raw_embedding = row.get(
            "embedding"
        )

        if raw_embedding is None:
            return None

        return self._parse_pgvector(
            raw_embedding
        )

    # ========================================================================
    # COUNT
    # ========================================================================

    async def count(
        self,
        *,
        collection: str | None = None,
        filters: Mapping[str, Any] | None = None,
        collection_name: str | None = None,
    ) -> int:
        """
        Count records matching optional metadata filters.
        """

        resolved_collection = (
            collection
            if collection is not None
            else collection_name
        )

        collection_name = self._resolve_collection(
            resolved_collection
        )

        where_sql, bind_params = (
            self._build_filter_clause(
                filters or {}
            )
        )

        sql = f"""
            SELECT COUNT(*) AS count
            FROM {collection_name}
            {where_sql}
        """

        result = await self.session.execute(
            text(sql),
            bind_params,
        )

        row = result.mappings().first()

        if row is None:
            return 0

        return int(
            row["count"]
        )

    # ========================================================================
    # HEALTH
    # ========================================================================

    async def health_check(self) -> dict[str, Any]:
        """
        Check PostgreSQL/pgvector availability.
        """

        try:
            result = await self.session.execute(
                text(
                    "SELECT 1"
                )
            )

            result.scalar_one()

            return {
                "status": "healthy",
                "provider": "pgvector",
                "collection": self.collection,
                "embedding_dimension": (
                    self.embedding_dimension
                ),
            }

        except Exception as exc:
            logger.exception(
                "PGVectorStore health check failed."
            )

            return {
                "status": "unhealthy",
                "provider": "pgvector",
                "collection": self.collection,
                "error": str(exc),
            }

    # ========================================================================
    # CLOSE
    # ========================================================================

    async def close(self) -> None:
        """
        Provider cleanup hook.

        PGVectorStore does not own the AsyncSession, so there is
        intentionally nothing to close here.

        The application/session dependency owns the session lifecycle.
        """

        return None

    # ========================================================================
    # FILTER BUILDING
    # ========================================================================

    def _build_filter_clause(
        self,
        filters: Mapping[str, Any],
    ) -> tuple[str, dict[str, Any]]:

        if not filters:
            return "", {}

        conditions: list[str] = []
        params: dict[str, Any] = {}

        parameter_index = 0

        for raw_key, raw_value in filters.items():

            key = str(raw_key).strip()

            if not key:
                continue

            if key == "amount_min":
                condition, value = (
                    self._build_numeric_condition(
                        metadata_key="amount",
                        operator="gte",
                        value=raw_value,
                        parameter_name=(
                            f"filter_{parameter_index}"
                        ),
                    )
                )

                if condition:
                    conditions.append(condition)
                    params.update(value)
                    parameter_index += 1

                continue

            if key == "amount_max":
                condition, value = (
                    self._build_numeric_condition(
                        metadata_key="amount",
                        operator="lte",
                        value=raw_value,
                        parameter_name=(
                            f"filter_{parameter_index}"
                        ),
                    )
                )

                if condition:
                    conditions.append(condition)
                    params.update(value)
                    parameter_index += 1

                continue

            if key == "created_after":
                condition, value = (
                    self._build_date_condition(
                        metadata_key="created_at",
                        operator="gte",
                        value=raw_value,
                        parameter_name=(
                            f"filter_{parameter_index}"
                        ),
                    )
                )

                if condition:
                    conditions.append(condition)
                    params.update(value)
                    parameter_index += 1

                continue

            if key == "created_before":
                condition, value = (
                    self._build_date_condition(
                        metadata_key="created_at",
                        operator="lte",
                        value=raw_value,
                        parameter_name=(
                            f"filter_{parameter_index}"
                        ),
                    )
                )

                if condition:
                    conditions.append(condition)
                    params.update(value)
                    parameter_index += 1

                continue

            if isinstance(
                raw_value,
                Mapping,
            ):
                for operator, operator_value in raw_value.items():

                    operator_name = (
                        str(operator)
                        .lower()
                        .strip()
                    )

                    if (
                        operator_name
                        not in self._COMPARISON_OPERATORS
                    ):
                        raise ValueError(
                            f"Unsupported filter operator "
                            f"'{operator_name}' for '{key}'. "
                            f"Supported operators: "
                            f"{sorted(self._COMPARISON_OPERATORS)}"
                        )

                    if self._looks_like_date_key(
                        key
                    ):
                        condition, value = (
                            self._build_date_condition(
                                metadata_key=key,
                                operator=operator_name,
                                value=operator_value,
                                parameter_name=(
                                    f"filter_{parameter_index}"
                                ),
                            )
                        )

                    elif self._looks_like_numeric_key(
                        key
                    ):
                        condition, value = (
                            self._build_numeric_condition(
                                metadata_key=key,
                                operator=operator_name,
                                value=operator_value,
                                parameter_name=(
                                    f"filter_{parameter_index}"
                                ),
                            )
                        )

                    else:
                        condition, value = (
                            self._build_generic_condition(
                                metadata_key=key,
                                operator=operator_name,
                                value=operator_value,
                                parameter_name=(
                                    f"filter_{parameter_index}"
                                ),
                            )
                        )

                    if condition:
                        conditions.append(condition)
                        params.update(value)
                        parameter_index += 1

                continue

            condition, value = (
                self._build_generic_condition(
                    metadata_key=key,
                    operator="eq",
                    value=raw_value,
                    parameter_name=(
                        f"filter_{parameter_index}"
                    ),
                )
            )

            if condition:
                conditions.append(condition)
                params.update(value)
                parameter_index += 1

        if not conditions:
            return "", params

        return (
            "WHERE " + "\nAND ".join(conditions),
            params,
        )

    def _build_generic_condition(
        self,
        *,
        metadata_key: str,
        operator: str,
        value: Any,
        parameter_name: str,
    ) -> tuple[str, dict[str, Any]]:

        key = self._validate_identifier(
            metadata_key,
            field_name="metadata key",
        )

        sql_operator = (
            self._COMPARISON_OPERATORS.get(
                operator
            )
        )

        if sql_operator is None:
            raise ValueError(
                f"Unsupported operator: {operator}"
            )

        expression = (
            f"metadata ->> '{key}' "
            f"{sql_operator} :{parameter_name}"
        )

        return (
            expression,
            {
                parameter_name:
                    self._normalize_filter_value(
                        value
                    )
            },
        )

    def _build_numeric_condition(
        self,
        *,
        metadata_key: str,
        operator: str,
        value: Any,
        parameter_name: str,
    ) -> tuple[str, dict[str, Any]]:

        key = self._validate_identifier(
            metadata_key,
            field_name="metadata key",
        )

        sql_operator = (
            self._COMPARISON_OPERATORS.get(
                operator
            )
        )

        if sql_operator is None:
            raise ValueError(
                f"Unsupported operator: {operator}"
            )

        numeric_expression = (
            "CASE "
            f"WHEN metadata ->> '{key}' "
            f"~ '{self._NUMERIC_PATTERN}' "
            f"THEN (metadata ->> '{key}')::numeric "
            "ELSE NULL "
            "END"
        )

        condition = (
            f"{numeric_expression} "
            f"{sql_operator} "
            f"CAST(:{parameter_name} AS numeric)"
        )

        return (
            condition,
            {
                parameter_name:
                    self._normalize_numeric_value(
                        value
                    )
            },
        )

    def _build_date_condition(
        self,
        *,
        metadata_key: str,
        operator: str,
        value: Any,
        parameter_name: str,
    ) -> tuple[str, dict[str, Any]]:

        key = self._validate_identifier(
            metadata_key,
            field_name="metadata key",
        )

        sql_operator = (
            self._COMPARISON_OPERATORS.get(
                operator
            )
        )

        if sql_operator is None:
            raise ValueError(
                f"Unsupported operator: {operator}"
            )

        condition = (
            f"metadata ->> '{key}' "
            f"{sql_operator} :{parameter_name}"
        )

        return (
            condition,
            {
                parameter_name:
                    self._normalize_date_value(
                        value
                    )
            },
        )

    # ========================================================================
    # FILTER TYPE DETECTION
    # ========================================================================

    @staticmethod
    def _looks_like_numeric_key(
        key: str,
    ) -> bool:

        normalized = key.lower()

        numeric_keys = {
            "amount",
            "total_amount",
            "invoice_amount",
            "subtotal",
            "tax",
            "tax_amount",
            "discount",
            "discount_amount",
            "price",
            "salary",
            "revenue",
            "cost",
            "value",
            "score",
            "confidence",
        }

        if normalized in numeric_keys:
            return True

        return any(
            token in normalized
            for token in (
                "_amount",
                "_price",
                "_cost",
                "_value",
                "_score",
                "_confidence",
            )
        )

    @staticmethod
    def _looks_like_date_key(
        key: str,
    ) -> bool:

        normalized = key.lower()

        date_keys = {
            "created_at",
            "updated_at",
            "created_date",
            "updated_date",
            "document_date",
            "invoice_date",
            "due_date",
            "effective_date",
            "expiry_date",
            "expiration_date",
            "processed_at",
        }

        if normalized in date_keys:
            return True

        return any(
            token in normalized
            for token in (
                "_date",
                "_at",
            )
        )

    # ========================================================================
    # RESULT NORMALIZATION
    # ========================================================================

    @classmethod
    def _normalize_search_result(
        cls,
        row: Mapping[str, Any],
    ) -> dict[str, Any]:

        metadata = (
            row.get("metadata")
            or {}
        )

        if isinstance(
            metadata,
            str,
        ):
            try:
                metadata = json.loads(
                    metadata
                )
            except json.JSONDecodeError:
                metadata = {}

        if not isinstance(
            metadata,
            Mapping,
        ):
            metadata = {}

        metadata_dict = dict(
            metadata
        )

        result_id = row.get(
            "id"
        )

        chunk_id = (
            metadata_dict.get("chunk_id")
            or metadata_dict.get("chunkId")
            or result_id
        )

        document_id = (
            metadata_dict.get("document_id")
            or metadata_dict.get("documentId")
        )

        collection_id = (
            metadata_dict.get("collection_id")
            or metadata_dict.get("collectionId")
        )

        score = row.get(
            "score",
            0.0,
        )

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
            "id": result_id,
            "chunk_id": chunk_id,
            "document_id": document_id,
            "collection_id": collection_id,
            "content": row.get(
                "content"
            ) or "",
            "score": normalized_score,
            "metadata": metadata_dict,
        }

    # ========================================================================
    # VALIDATION
    # ========================================================================

    def _resolve_collection(
        self,
        collection: str | None,
    ) -> str:

        if collection is None:
            return self.collection

        return self._validate_identifier(
            collection,
            field_name="collection",
        )

    @classmethod
    def _validate_identifier(
        cls,
        value: str,
        *,
        field_name: str,
    ) -> str:

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                f"{field_name} must be a string."
            )

        value = value.strip()

        if not value:
            raise ValueError(
                f"{field_name} cannot be empty."
            )

        if not cls._IDENTIFIER_PATTERN.fullmatch(
            value
        ):
            raise ValueError(
                f"Invalid {field_name}: {value!r}. "
                "Only letters, numbers and underscores are allowed, "
                "and the identifier must not start with a number."
            )

        return value

    def _validate_top_k(
        self,
        top_k: int,
    ) -> int:

        try:
            value = int(top_k)
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                "top_k must be an integer."
            ) from exc

        if value < 1:
            raise ValueError(
                "top_k must be greater than zero."
            )

        return min(
            value,
            self.MAX_TOP_K,
        )

    def _validate_vector(
        self,
        vector: Sequence[float],
    ) -> list[float]:

        if vector is None:
            raise ValueError(
                "vector cannot be None."
            )

        if isinstance(
            vector,
            (
                str,
                bytes,
            ),
        ):
            raise TypeError(
                "vector must be a sequence of numbers."
            )

        try:
            normalized = [
                float(value)
                for value in vector
            ]
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                "vector must contain only numeric values."
            ) from exc

        if not normalized:
            raise ValueError(
                "vector cannot be empty."
            )

        if len(normalized) != self.embedding_dimension:
            raise ValueError(
                "Embedding dimension mismatch: "
                f"expected {self.embedding_dimension}, "
                f"received {len(normalized)}."
            )

        for value in normalized:
            if not self._is_finite(value):
                raise ValueError(
                    "vector contains a non-finite value."
                )

        return normalized

    # ========================================================================
    # VALUE NORMALIZATION
    # ========================================================================

    @staticmethod
    def _normalize_filter_value(
        value: Any,
    ) -> str:

        if value is None:
            return ""

        if isinstance(
            value,
            bool,
        ):
            return (
                "true"
                if value
                else "false"
            )

        if isinstance(
            value,
            (
                datetime,
                date,
            ),
        ):
            return value.isoformat()

        if isinstance(
            value,
            Decimal,
        ):
            return str(value)

        return str(value)

    @staticmethod
    def _normalize_numeric_value(
        value: Any,
    ) -> str:

        if value is None:
            raise ValueError(
                "Numeric filter value cannot be None."
            )

        if isinstance(
            value,
            bool,
        ):
            raise ValueError(
                "Boolean values are not valid numeric filters."
            )

        try:
            decimal_value = Decimal(
                str(value).replace(
                    ",",
                    "",
                )
            )
        except Exception as exc:
            raise ValueError(
                f"Invalid numeric filter value: {value!r}"
            ) from exc

        if not decimal_value.is_finite():
            raise ValueError(
                "Numeric filter value must be finite."
            )

        return str(
            decimal_value
        )

    @staticmethod
    def _normalize_date_value(
        value: Any,
    ) -> str:

        if value is None:
            raise ValueError(
                "Date filter value cannot be None."
            )

        if isinstance(
            value,
            datetime,
        ):
            return value.isoformat()

        if isinstance(
            value,
            date,
        ):
            return value.isoformat()

        normalized = str(
            value
        ).strip()

        if not normalized:
            raise ValueError(
                "Date filter value cannot be empty."
            )

        if not re.match(
            PGVectorStore._DATE_PATTERN,
            normalized,
        ):
            raise ValueError(
                "Date filters must use ISO format."
            )

        return normalized

    @staticmethod
    def _normalize_metadata(
        metadata: Mapping[str, Any],
    ) -> dict[str, Any]:

        def normalize(
            value: Any,
        ) -> Any:

            if value is None:
                return None

            if isinstance(
                value,
                (
                    datetime,
                    date,
                ),
            ):
                return value.isoformat()

            if isinstance(
                value,
                Decimal,
            ):
                return str(value)

            if isinstance(
                value,
                Mapping,
            ):
                return {
                    str(key): normalize(item)
                    for key, item in value.items()
                }

            if isinstance(
                value,
                Sequence,
            ) and not isinstance(
                value,
                (
                    str,
                    bytes,
                ),
            ):
                return [
                    normalize(item)
                    for item in value
                ]

            if isinstance(
                value,
                float,
            ):
                if not PGVectorStore._is_finite(
                    value
                ):
                    return None

            return value

        return {
            str(key): normalize(value)
            for key, value in metadata.items()
        }

    @staticmethod
    def _json_default(
        value: Any,
    ) -> Any:

        if isinstance(
            value,
            (
                datetime,
                date,
            ),
        ):
            return value.isoformat()

        if isinstance(
            value,
            Decimal,
        ):
            return str(value)

        raise TypeError(
            f"Object of type {type(value).__name__} "
            "is not JSON serializable."
        )

    # ========================================================================
    # VECTOR CONVERSION
    # ========================================================================

    @staticmethod
    def _vector_to_pgvector_literal(
        vector: Sequence[float],
    ) -> str:

        return (
            "["
            + ",".join(
                format(
                    float(value),
                    ".17g",
                )
                for value in vector
            )
            + "]"
        )

    @staticmethod
    def _parse_pgvector(
        value: Any,
    ) -> list[float]:

        if isinstance(
            value,
            Sequence,
        ) and not isinstance(
            value,
            (
                str,
                bytes,
            ),
        ):
            return [
                float(item)
                for item in value
            ]

        raw = str(
            value
        ).strip()

        if (
            raw.startswith("[")
            and raw.endswith("]")
        ):
            raw = raw[1:-1]

        if not raw:
            return []

        return [
            float(item.strip())
            for item in raw.split(",")
        ]

    # ========================================================================
    # INDEX HELPERS
    # ========================================================================

    @classmethod
    def _index_name(
        cls,
        collection: str,
        suffix: str,
    ) -> str:

        base = (
            f"idx_{collection}_{suffix}"
        )

        return base[:63]

    # ========================================================================
    # NUMERIC / FLOAT HELPERS
    # ========================================================================

    @staticmethod
    def _is_finite(
        value: float,
    ) -> bool:

        return (
            value == value
            and value != float("inf")
            and value != float("-inf")
        )


__all__ = [
    "PGVectorStore",
]