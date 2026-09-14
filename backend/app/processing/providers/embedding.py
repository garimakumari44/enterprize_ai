
"""
app.processing.providers.embedding

Canonical contract for embedding providers.

The interface is deliberately independent of any specific embedding
library or vendor.

Supported implementations may include:

    - SentenceTransformers
    - BAAI BGE models
    - Cohere
    - OpenAI
    - other local embedding models
    - future enterprise embedding services

The preferred local implementation can therefore use:

    BAAI/bge-small-en-v1.5

without changing this contract.
"""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any, Sequence

from .base import (
    BaseProcessingProvider,
    ProviderResult,
)
from .capabilities import ProviderCapability


@dataclass(slots=True)
class EmbeddingRequest:
    """
    Request for generating one or more embeddings.
    """

    texts: Sequence[str]

    document_id: str | None = None

    chunk_ids: Sequence[str] = field(
        default_factory=list
    )

    normalize: bool = True

    batch_size: int | None = None

    options: dict[str, Any] = field(
        default_factory=dict
    )

    def validate(self) -> None:
        if not isinstance(
            self.texts,
            Sequence,
        ):
            raise TypeError(
                "texts must be a sequence."
            )

        if not self.texts:
            raise ValueError(
                "EmbeddingRequest requires at least one text."
            )

        for index, text in enumerate(
            self.texts
        ):
            if not isinstance(
                text,
                str,
            ):
                raise TypeError(
                    f"texts[{index}] must be a string."
                )

            if not text.strip():
                raise ValueError(
                    f"texts[{index}] cannot be empty."
                )

        if self.chunk_ids:
            if len(self.chunk_ids) != len(
                self.texts
            ):
                raise ValueError(
                    "chunk_ids length must match texts length."
                )

        if self.batch_size is not None:
            if self.batch_size < 1:
                raise ValueError(
                    "batch_size must be >= 1."
                )


@dataclass(slots=True)
class EmbeddingVector:
    """
    One embedding vector associated with a text/chunk.
    """

    vector: list[float]

    index: int

    chunk_id: str | None = None

    dimension: int | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        self.vector = [
            float(value)
            for value in self.vector
        ]

        if not self.vector:
            raise ValueError(
                "Embedding vector cannot be empty."
            )

        if self.index < 0:
            raise ValueError(
                "Embedding index cannot be negative."
            )

        actual_dimension = len(
            self.vector
        )

        if self.dimension is None:
            self.dimension = actual_dimension
        elif self.dimension != actual_dimension:
            raise ValueError(
                "Embedding dimension does not match vector length."
            )

    def to_dict(
        self,
        *,
        include_vector: bool = True,
    ) -> dict[str, Any]:
        result = {
            "index": self.index,
            "chunk_id": self.chunk_id,
            "dimension": self.dimension,
            "metadata": dict(self.metadata),
        }

        if include_vector:
            result["vector"] = list(
                self.vector
            )

        return result


@dataclass(slots=True)
class EmbeddingResult:
    """
    Canonical output from an embedding provider.
    """

    embeddings: list[EmbeddingVector] = field(
        default_factory=list
    )

    model: str | None = None

    provider: str | None = None

    dimension: int | None = None

    normalized: bool = False

    document_id: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    warnings: list[str] = field(
        default_factory=list
    )

    @property
    def count(self) -> int:
        return len(
            self.embeddings
        )

    def validate_dimensions(self) -> None:
        """
        Ensure every vector has the same dimension.
        """

        if not self.embeddings:
            return

        dimensions = {
            len(embedding.vector)
            for embedding in self.embeddings
        }

        if len(dimensions) != 1:
            raise ValueError(
                "Embedding vectors have inconsistent dimensions."
            )

        dimension = dimensions.pop()

        if (
            self.dimension is not None
            and self.dimension != dimension
        ):
            raise ValueError(
                "EmbeddingResult dimension does not match "
                "vector dimensions."
            )

        self.dimension = dimension

    def to_dict(
        self,
        *,
        include_vectors: bool = True,
    ) -> dict[str, Any]:
        self.validate_dimensions()

        return {
            "embeddings": [
                embedding.to_dict(
                    include_vector=include_vectors
                )
                for embedding in self.embeddings
            ],
            "model": self.model,
            "provider": self.provider,
            "dimension": self.dimension,
            "normalized": self.normalized,
            "document_id": self.document_id,
            "metadata": dict(self.metadata),
            "warnings": list(self.warnings),
            "count": self.count,
        }


class BaseEmbeddingProvider(
    BaseProcessingProvider
):
    """
    Base contract for embedding providers.
    """

    PROVIDER_TYPE = "embedding"

    PROCESSING_STAGE = "embedding"

    def capabilities(self) -> set[str]:
        return {
            ProviderCapability.EMBEDDING.value,
            ProviderCapability.BATCH_EMBEDDING.value,
        }

    @abstractmethod
    async def embed(
        self,
        request: EmbeddingRequest,
    ) -> EmbeddingResult:
        """
        Generate embeddings for the supplied texts.
        """

        raise NotImplementedError

    async def process(
        self,
        request: EmbeddingRequest,
    ) -> ProviderResult:
        request.validate()

        result = await self.embed(
            request
        )

        result.validate_dimensions()

        return ProviderResult.ok(
            provider=self.name,
            operation="embed",
            data=result.to_dict(
                include_vectors=True
            ),
            metadata={
                "document_id": result.document_id,
                "model": result.model,
                "dimension": result.dimension,
                "count": result.count,
                "normalized": result.normalized,
            },
            warnings=result.warnings,
        )

    @property
    def model_name(self) -> str | None:
        value = self.get_config(
            "model"
        )

        if value is None:
            value = self.get_config(
                "local_model"
            )

        return (
            str(value)
            if value is not None
            else None
        )

    @property
    def device(self) -> str:
        return str(
            self.get_config(
                "device",
                self.get_config(
                    "local_device",
                    "cpu",
                ),
            )
        )

    @property
    def batch_size(self) -> int:
        return int(
            self.get_config(
                "batch_size",
                self.get_config(
                    "local_batch_size",
                    32,
                ),
            )
        )

    @property
    def dimension(self) -> int | None:
        value = self.get_config(
            "dimension"
        )

        if value is None:
            return None

        return int(value)

    def supports_dimension(
        self,
        dimension: int,
    ) -> bool:
        """
        Check whether the configured provider dimension matches.
        """

        configured = self.dimension

        if configured is None:
            return True

        return configured == dimension

