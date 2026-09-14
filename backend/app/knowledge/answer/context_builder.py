from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass
class ContextItem:
    """
    A single piece of retrieved knowledge used to generate an answer.
    """

    chunk_id: str
    document_id: str
    content: str
    score: float | None = None
    metadata: dict[str, Any] | None = None


class ContextBuilder:
    """
    Build deterministic LLM context from retrieved search results.
    """

    def __init__(
        self,
        max_chunks: int = 10,
        max_characters: int = 30_000,
    ) -> None:
        if max_chunks <= 0:
            raise ValueError("max_chunks must be greater than zero")

        if max_characters <= 0:
            raise ValueError("max_characters must be greater than zero")

        self.max_chunks = max_chunks
        self.max_characters = max_characters

    def build(
        self,
        chunks: Iterable[ContextItem],
    ) -> str:
        selected = list(chunks)[: self.max_chunks]

        if not selected:
            return ""

        sections: list[str] = []
        total_characters = 0

        for index, chunk in enumerate(selected, start=1):
            content = chunk.content.strip()

            if not content:
                continue

            section = (
                f"[Source {index}]\n"
                f"Document ID: {chunk.document_id}\n"
                f"Chunk ID: {chunk.chunk_id}\n"
                f"{content}"
            )

            if (
                total_characters + len(section)
                > self.max_characters
            ):
                remaining = self.max_characters - total_characters

                if remaining > 0:
                    sections.append(section[:remaining])

                break

            sections.append(section)
            total_characters += len(section)

        return "\n\n".join(sections)