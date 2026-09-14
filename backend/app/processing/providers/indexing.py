
"""
app.processing.providers.indexing

Canonical provider contract for document/chunk indexing.

The indexing layer receives processed chunks and optionally their
embeddings and persists them into a searchable backend.

Possible implementations:

    - PostgreSQL / pgvector
    - Qdrant
    - Pinecone
    - Elasticsearch
    - hybrid keyword/vector stores

This contract deliberately does not depend on any database client.
"""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from .base import (
    BaseProcessingProvider,
    ProviderResult,
)
from .capabilities import ProviderCapability


@dataclass(slots=True)
class IndexDocument:
    """
    One document/chunk to be indexed.
    """

    id: str

    text: str

    embedding: Sequence[float] | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    document_id: str | None = None

    chunk_id: str | None = None

    def __post_init__(self) -> None:
        self.id = str(self.id).strip()

        if not self.id:
            raise ValueError(
                "IndexDocument id cannot be empty."
            )

        if not isinstance(
            self.text,
            str,
        ):
            raise TypeError(
                "IndexDocument text must be a string."
            )

        if not self.text.strip():
            raise ValueError(
                "IndexDocument text cannot be empty."
            )

        if self.embedding is not None:
            self.embedding = [
                float(value)
                for value in self.embedding
            ]

    @property
    def has_embedding(self) -> bool:
        return bool(self.embedding)

    @property
    def embedding_dimension(self) -> int | None:
        if self.embedding is None:
            return None

        return len(self.embedding)

    def to_dict(
        self,
        *,
        include_embedding: bool = True,
    ) -> dict[str, Any]:
        result = {
            "id": self.id,
            "text": self.text,
            "metadata": dict(self.metadata),
            "document_id": self.document_id,
            "chunk_id": self.chunk_id,
        }

        if include_embedding:
            result["embedding"] = (
                list(self.embedding)
                if self.embedding is not None
                else None
            )

        return result


@dataclass(slots=True)
class IndexingRequest:
    """
    Input contract for indexing providers.
    """

    documents: Sequence[IndexDocument]

    collection: str | None = None

    namespace: str | None = None

    document_id: str | None = None

    upsert: bool = True

    create_index: bool = True

    options: dict[str, Any] = field(
        default_factory=dict
    )

    def validate(self) -> None:
        if not isinstance(
            self.documents,
            Sequence,
        ):
            raise TypeError(
                "documents must be a sequence."
            )

        if not self.documents:
            raise ValueError(
                "IndexingRequest requires at least one document."
            )

        for index, document in enumerate(
            self.documents
        ):
            if not isinstance(
                document,
                IndexDocument,
            ):
                raise TypeError(
                    f"documents[{index}] must be IndexDocument."
                )


@dataclass(slots=True)
class IndexingResult:
    """
    Canonical output from an indexing provider.
    """

    indexed_count: int = 0

    failed_count: int = 0

    skipped_count: int = 0

    collection: str | None = None

    namespace: str | None = None

    document_ids: list[str] = field(
        default_factory=list
    )

    failed_ids: list[str] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    warnings: list[str] = field(
        default_factory=list
    )

    errors: list[str] = field(
        default_factory=list
    )

    @property
    def total_count(self) -> int:
        return (
            self.indexed_count
            + self.failed_count
            + self.skipped_count
        )

    @property
    def success(self) -> bool:
        return self.failed_count == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "indexed_count": self.indexed_count,
            "failed_count": self.failed_count,
            "skipped_count": self.skipped_count,
            "collection": self.collection,
            "namespace": self.namespace,
            "document_ids": list(
                self.document_ids
            ),
            "failed_ids": list(
                self.failed_ids
            ),
            "metadata": dict(
                self.metadata
            ),
            "warnings": list(
                self.warnings
            ),
            "errors": list(
                self.errors
            ),
            "total_count": self.total_count,
            "success": self.success,
        }


class BaseIndexingProvider(
    BaseProcessingProvider
):
    """
    Base contract for indexing providers.
    """

    PROVIDER_TYPE = "indexing"

    PROCESSING_STAGE = "indexing"

    def capabilities(self) -> set[str]:
        return {
            ProviderCapability.INDEXING.value,
        }

    @abstractmethod
    async def index(
        self,
        request: IndexingRequest,
    ) -> IndexingResult:
        """
        Index documents into the configured backend.
        """

        raise NotImplementedError

    async def process(
        self,
        request: IndexingRequest,
    ) -> ProviderResult:
        request.validate()

        result = await self.index(
            request
        )

        return ProviderResult.ok(
            provider=self.name,
            operation="index",
            data=result.to_dict(),
            metadata={
                "indexed_count": (
                    result.indexed_count
                ),
                "failed_count": (
                    result.failed_count
                ),
                "skipped_count": (
                    result.skipped_count
                ),
                "collection": result.collection,
                "namespace": result.namespace,
                "success": result.success,
            },
            warnings=result.warnings,
        )

    async def delete(
        self,
        ids: Sequence[str],
        *,
        collection: str | None = None,
        namespace: str | None = None,
    ) -> int:
        """
        Delete indexed records.

        Concrete providers should override this when deletion is
        supported.
        """

        raise NotImplementedError(
            f"{self.name} does not implement delete()."
        )

    async def search(
        self,
        query: str,
        *,
        limit: int = 10,
        collection: str | None = None,
        namespace: str | None = None,
        filters: Mapping[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search indexed records.

        Concrete providers should override this.
        """

        raise NotImplementedError(
            f"{self.name} does not implement search()."
        )

    async def ensure_collection(
        self,
        collection: str,
        *,
        dimension: int | None = None,
    ) -> None:
        """
        Ensure the target collection/index exists.

        Concrete providers should override this when needed.
        """

        raise NotImplementedError(
            f"{self.name} does not implement "
            "ensure_collection()."
        )

