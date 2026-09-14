
"""
app.processing.providers.chunking

Canonical provider contract for document chunking.

Chunking converts a structured document into retrieval-friendly units.

Typical flow:

    Extracted text
         |
         v
    Structure
         |
         v
    ChunkingProvider
         |
         v
    DocumentChunk[]
         |
         v
    Embedding
         |
         v
    Indexing

The contract supports both simple rule-based chunking and future
semantic/token-aware chunking implementations.
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
class DocumentChunk:
    """
    Canonical representation of one retrieval chunk.
    """

    chunk_id: str

    text: str

    document_id: str | None = None

    page_start: int | None = None

    page_end: int | None = None

    section: str | None = None

    heading: str | None = None

    chunk_index: int = 0

    parent_chunk_id: str | None = None

    token_count: int | None = None

    character_count: int | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        self.chunk_id = str(
            self.chunk_id
        ).strip()

        if not self.chunk_id:
            raise ValueError(
                "chunk_id cannot be empty."
            )

        if not isinstance(
            self.text,
            str,
        ):
            raise TypeError(
                "chunk text must be a string."
            )

        self.text = self.text.strip()

        if not self.text:
            raise ValueError(
                "chunk text cannot be empty."
            )

        if self.chunk_index < 0:
            raise ValueError(
                "chunk_index cannot be negative."
            )

        if self.page_start is not None:
            if self.page_start < 1:
                raise ValueError(
                    "page_start must be >= 1."
                )

        if self.page_end is not None:
            if self.page_end < 1:
                raise ValueError(
                    "page_end must be >= 1."
                )

        if (
            self.page_start is not None
            and self.page_end is not None
            and self.page_end < self.page_start
        ):
            raise ValueError(
                "page_end cannot be smaller than page_start."
            )

        if self.token_count is None:
            self.token_count = len(
                self.text.split()
            )

        if self.character_count is None:
            self.character_count = len(
                self.text
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "document_id": self.document_id,
            "page_start": self.page_start,
            "page_end": self.page_end,
            "section": self.section,
            "heading": self.heading,
            "chunk_index": self.chunk_index,
            "parent_chunk_id": self.parent_chunk_id,
            "token_count": self.token_count,
            "character_count": self.character_count,
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True)
class ChunkingRequest:
    """
    Input contract for chunking providers.
    """

    text: str = ""

    document_id: str | None = None

    pages: Sequence[Mapping[str, Any]] = field(
        default_factory=list
    )

    structure: Mapping[str, Any] | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    options: dict[str, Any] = field(
        default_factory=dict
    )

    def validate(self) -> None:
        if not isinstance(
            self.text,
            str,
        ):
            raise TypeError(
                "text must be a string."
            )

        if not self.text.strip():
            raise ValueError(
                "ChunkingRequest text cannot be empty."
            )

        if not isinstance(
            self.pages,
            Sequence,
        ):
            raise TypeError(
                "pages must be a sequence."
            )

        if self.structure is not None:
            if not isinstance(
                self.structure,
                Mapping,
            ):
                raise TypeError(
                    "structure must be a mapping or None."
                )


@dataclass(slots=True)
class ChunkingResult:
    """
    Canonical output from a chunking provider.
    """

    document_id: str | None = None

    chunks: list[DocumentChunk] = field(
        default_factory=list
    )

    strategy: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    warnings: list[str] = field(
        default_factory=list
    )

    @property
    def chunk_count(self) -> int:
        return len(self.chunks)

    @property
    def total_characters(self) -> int:
        return sum(
            chunk.character_count or 0
            for chunk in self.chunks
        )

    @property
    def total_tokens(self) -> int:
        return sum(
            chunk.token_count or 0
            for chunk in self.chunks
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "chunks": [
                chunk.to_dict()
                for chunk in self.chunks
            ],
            "strategy": self.strategy,
            "metadata": dict(self.metadata),
            "warnings": list(self.warnings),
            "chunk_count": self.chunk_count,
            "total_characters": self.total_characters,
            "total_tokens": self.total_tokens,
        }


class BaseChunkingProvider(
    BaseProcessingProvider
):
    """
    Base contract for chunking providers.
    """

    PROVIDER_TYPE = "chunking"

    PROCESSING_STAGE = "chunking"

    def capabilities(self) -> set[str]:
        return {
            ProviderCapability.CHUNKING.value,
        }

    @abstractmethod
    async def chunk(
        self,
        request: ChunkingRequest,
    ) -> ChunkingResult:
        """
        Split a document into retrieval chunks.
        """

        raise NotImplementedError

    async def process(
        self,
        request: ChunkingRequest,
    ) -> ProviderResult:
        request.validate()

        result = await self.chunk(
            request
        )

        return ProviderResult.ok(
            provider=self.name,
            operation="chunk",
            data=result.to_dict(),
            metadata={
                "document_id": result.document_id,
                "strategy": result.strategy,
                "chunk_count": result.chunk_count,
                "total_characters": (
                    result.total_characters
                ),
                "total_tokens": result.total_tokens,
            },
            warnings=result.warnings,
        )

    def chunk_size(self) -> int | None:
        value = self.get_config(
            "chunk_size"
        )

        return (
            int(value)
            if value is not None
            else None
        )

    def chunk_overlap(self) -> int:
        return int(
            self.get_config(
                "chunk_overlap",
                0,
            )
        )

