from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Citation:
    """
    Citation pointing back to a retrieved document/chunk.
    """

    citation_id: str
    document_id: str
    chunk_id: str
    title: str | None = None
    page_number: int | None = None


class CitationBuilder:
    """
    Build citation metadata for generated knowledge answers.
    """

    def build(
        self,
        citations: Iterable[Citation],
    ) -> list[Citation]:
        unique: dict[str, Citation] = {}

        for citation in citations:
            unique[citation.citation_id] = citation

        return list(unique.values())

    def format_inline(
        self,
        citation: Citation,
    ) -> str:
        return f"[{citation.citation_id}]"

    def format_reference(
        self,
        citation: Citation,
    ) -> str:
        parts = [citation.citation_id]

        if citation.title:
            parts.append(citation.title)

        if citation.page_number is not None:
            parts.append(f"page {citation.page_number}")

        parts.append(
            f"document={citation.document_id}"
        )

        return " — ".join(parts)