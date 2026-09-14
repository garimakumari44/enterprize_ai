
"""
app.processing.providers.implementations.semantic_chunker

Lightweight semantic-aware chunker.

The implementation uses:
    - paragraph boundaries
    - sentence boundaries
    - configurable chunk size
    - configurable overlap
    - optional section/heading information

It does not require an embedding model.

The name "semantic" refers to preserving natural text boundaries,
not to neural semantic similarity.
"""

from __future__ import annotations

import re
from typing import Any, Mapping

from ..chunking import (
    BaseChunkingProvider,
    ChunkingRequest,
    ChunkingResult,
    DocumentChunk,
)


class SemanticChunker(
    BaseChunkingProvider
):
    """
    Deterministic semantic-aware document chunker.
    """

    PROVIDER_NAME = "semantic_chunker"

    PROVIDER_TYPE = "chunking"

    VERSION = "1.0"

    DEFAULT_CHUNK_SIZE = 1000

    DEFAULT_OVERLAP = 150

    MIN_CHUNK_SIZE = 100

    def __init__(
        self,
        *,
        config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            config=config
        )

    async def health_check(self) -> bool:
        return True

    def validate_config(self) -> None:
        size = int(
            self.get_config(
                "chunk_size",
                self.DEFAULT_CHUNK_SIZE,
            )
        )

        overlap = int(
            self.get_config(
                "chunk_overlap",
                self.DEFAULT_OVERLAP,
            )
        )

        if size < self.MIN_CHUNK_SIZE:
            raise ValueError(
                f"chunk_size must be >= {self.MIN_CHUNK_SIZE}."
            )

        if overlap < 0:
            raise ValueError(
                "chunk_overlap cannot be negative."
            )

        if overlap >= size:
            raise ValueError(
                "chunk_overlap must be smaller than chunk_size."
            )

    def chunk_size(self) -> int:
        return int(
            self.get_config(
                "chunk_size",
                self.DEFAULT_CHUNK_SIZE,
            )
        )

    def chunk_overlap(self) -> int:
        return int(
            self.get_config(
                "chunk_overlap",
                self.DEFAULT_OVERLAP,
            )
        )

    @staticmethod
    def _normalize_text(
        text: str,
    ) -> str:
        text = text.replace(
            "\r\n",
            "\n",
        )

        text = text.replace(
            "\r",
            "\n",
        )

        return text.strip()

    @staticmethod
    def _split_paragraphs(
        text: str,
    ) -> list[str]:
        paragraphs = re.split(
            r"\n\s*\n+",
            text,
        )

        return [
            paragraph.strip()
            for paragraph in paragraphs
            if paragraph.strip()
        ]

    @staticmethod
    def _split_sentences(
        text: str,
    ) -> list[str]:
        """
        Lightweight sentence splitter.

        It intentionally avoids external NLP dependencies.
        """

        sentences = re.split(
            r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])",
            text,
        )

        return [
            sentence.strip()
            for sentence in sentences
            if sentence.strip()
        ]

    def _units(
        self,
        text: str,
    ) -> list[str]:
        paragraphs = self._split_paragraphs(
            text
        )

        units: list[str] = []

        for paragraph in paragraphs:
            if len(paragraph) <= self.chunk_size():
                units.append(
                    paragraph
                )
                continue

            units.extend(
                self._split_sentences(
                    paragraph
                )
            )

        return units

    def _split_large_unit(
        self,
        text: str,
    ) -> list[str]:
        size = self.chunk_size()

        if len(text) <= size:
            return [
                text
            ]

        words = text.split()

        chunks: list[str] = []

        current: list[str] = []
        current_length = 0

        for word in words:
            additional = (
                len(word)
                + (
                    1
                    if current
                    else 0
                )
            )

            if (
                current
                and current_length
                + additional
                > size
            ):
                chunks.append(
                    " ".join(
                        current
                    )
                )

                current = []
                current_length = 0

            current.append(
                word
            )

            current_length += (
                len(word)
                + (
                    1
                    if len(current) > 1
                    else 0
                )
            )

        if current:
            chunks.append(
                " ".join(
                    current
                )
            )

        return chunks

    def _prepare_units(
        self,
        text: str,
    ) -> list[str]:
        units = self._units(
            text
        )

        result: list[str] = []

        for unit in units:
            if len(unit) <= self.chunk_size():
                result.append(
                    unit
                )
            else:
                result.extend(
                    self._split_large_unit(
                        unit
                    )
                )

        return result

    def _build_chunks(
        self,
        units: list[str],
    ) -> list[str]:
        size = self.chunk_size()

        chunks: list[str] = []

        current: list[str] = []
        current_length = 0

        for unit in units:
            additional = (
                len(unit)
                + (
                    2
                    if current
                    else 0
                )
            )

            if (
                current
                and current_length
                + additional
                > size
            ):
                chunks.append(
                    "\n\n".join(
                        current
                    )
                )

                overlap = self.chunk_overlap()

                if overlap > 0:
                    overlap_text = (
                        chunks[-1][
                            -overlap:
                        ]
                    )

                    current = [
                        overlap_text
                    ]

                    current_length = (
                        len(
                            overlap_text
                        )
                    )
                else:
                    current = []
                    current_length = 0

            current.append(
                unit
            )

            current_length += (
                len(unit)
                + (
                    2
                    if len(current) > 1
                    else 0
                )
            )

        if current:
            chunks.append(
                "\n\n".join(
                    current
                )
            )

        return [
            chunk.strip()
            for chunk in chunks
            if chunk.strip()
        ]

    def _extract_structure_context(
        self,
        structure: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        if not structure:
            return {}

        nodes = structure.get(
            "nodes",
            [],
        )

        if not isinstance(
            nodes,
            list,
        ):
            return {}

        headings: list[str] = []

        for node in nodes:
            if not isinstance(
                node,
                Mapping,
            ):
                continue

            node_type = str(
                node.get(
                    "node_type",
                    "",
                )
            ).lower()

            if node_type in {
                "heading",
                "section",
            }:
                title = node.get(
                    "title"
                )

                if title:
                    headings.append(
                        str(title)
                    )

        return {
            "headings": headings,
        }

    def _page_for_chunk(
        self,
        chunk_text: str,
        pages: list[Mapping[str, Any]],
    ) -> tuple[int | None, int | None]:
        """
        Best-effort page mapping.

        Exact character offsets are not available in the canonical
        request, so page association is intentionally conservative.
        """

        if not pages:
            return None, None

        for page in pages:
            page_text = str(
                page.get(
                    "text",
                    "",
                )
                or ""
            )

            if (
                chunk_text[:80]
                and chunk_text[:80]
                in page_text
            ):
                page_number = page.get(
                    "page_number"
                )

                try:
                    page_number = int(
                        page_number
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    return None, None

                return (
                    page_number,
                    page_number,
                )

        return None, None

    async def chunk(
        self,
        request: ChunkingRequest,
    ) -> ChunkingResult:
        request.validate()

        self.validate_config()

        text = self._normalize_text(
            request.text
        )

        units = self._prepare_units(
            text
        )

        raw_chunks = self._build_chunks(
            units
        )

        structure_context = (
            self._extract_structure_context(
                request.structure
            )
        )

        chunks: list[
            DocumentChunk
        ] = []

        for index, chunk_text in enumerate(
            raw_chunks
        ):
            page_start, page_end = (
                self._page_for_chunk(
                    chunk_text,
                    [
                        page
                        for page in request.pages
                        if isinstance(
                            page,
                            Mapping,
                        )
                    ],
                )
            )

            heading = None

            headings = structure_context.get(
                "headings",
                [],
            )

            if headings:
                # Best-effort heading association.
                preceding = [
                    heading_item
                    for heading_item in headings
                    if heading_item
                    in chunk_text
                ]

                if preceding:
                    heading = (
                        preceding[-1]
                    )

            chunk = DocumentChunk(
                chunk_id=(
                    f"{request.document_id or 'document'}"
                    f"-chunk-{index}"
                ),
                text=chunk_text,
                document_id=request.document_id,
                page_start=page_start,
                page_end=page_end,
                section=heading,
                heading=heading,
                chunk_index=index,
                token_count=len(
                    chunk_text.split()
                ),
                character_count=len(
                    chunk_text
                ),
                metadata={
                    "strategy": "semantic",
                    "provider": self.name,
                },
            )

            chunks.append(
                chunk
            )

        warnings: list[str] = []

        if not chunks:
            warnings.append(
                "No chunks were generated."
            )

        return ChunkingResult(
            document_id=request.document_id,
            chunks=chunks,
            strategy="semantic",
            metadata={
                "chunk_size": self.chunk_size(),
                "chunk_overlap": self.chunk_overlap(),
                "unit_count": len(units),
            },
            warnings=warnings,
        )

