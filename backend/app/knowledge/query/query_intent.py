from __future__ import annotations

from enum import Enum


class QueryIntent(str, Enum):
    """Supported knowledge-search query intents."""

    SEARCH = "search"
    QUESTION_ANSWERING = "question_answering"
    DOCUMENT_LOOKUP = "document_lookup"
    FILTERED_SEARCH = "filtered_search"
    UNKNOWN = "unknown"