"""
app/knowledge/query/query_parser.py

Natural-language knowledge query parser.

The parser converts a user query into:

    ParsedQuery
        |
        +-- original_query
        +-- normalized_query
        +-- intent
        +-- exhaustive
        +-- structured filters

The parser does not execute retrieval.

Important behavior
------------------
Normal document-type words remain searchable text.

Examples:

    invoice
    unpaid invoice
    invoice total
    resumes with Kubernetes experience

remain normal search queries.

However, explicit document lookup language is recognized:

    find invoices
    find all invoices
    show all contracts
    list resumes
    retrieve reports

For exhaustive lookup queries, the document type is extracted as a
filter so retrieval can reliably find all matching documents rather
than depending only on semantic similarity.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from app.knowledge.query.query_filters import QueryFilters
from app.knowledge.query.query_intent import QueryIntent


@dataclass
class ParsedQuery:
    """
    Normalized representation of a user's knowledge-search query.
    """

    original_query: str
    normalized_query: str
    intent: QueryIntent
    filters: QueryFilters
    exhaustive: bool = False


class QueryParser:
    """
    Parse natural-language knowledge queries into structured queries.

    This is intentionally rule-based for now.

    A future LLM/model-based parser can return the same
    ParsedQuery contract without changing SearchService.
    """

    # ======================================================================
    # DOCUMENT TYPES
    # ======================================================================

    DOCUMENT_TYPES = {
        "invoice": "invoice",
        "invoices": "invoice",
        "contract": "contract",
        "contracts": "contract",
        "resume": "resume",
        "resumes": "resume",
        "cv": "resume",
        "cvs": "resume",
        "report": "report",
        "reports": "report",
    }

    # ======================================================================
    # LOOKUP WORDS
    # ======================================================================

    LOOKUP_WORDS = (
        "find",
        "show",
        "get",
        "locate",
        "retrieve",
        "search",
        "list",
    )

    EXHAUSTIVE_WORDS = (
        "all",
        "every",
        "each",
        "list all",
        "show all",
        "find all",
        "get all",
        "retrieve all",
        "locate all",
    )

    # ======================================================================
    # PUBLIC
    # ======================================================================

    def parse(
        self,
        query: str,
    ) -> ParsedQuery:

        if not isinstance(query, str):
            raise TypeError(
                "query must be a string"
            )

        normalized = " ".join(
            query.strip().split()
        )

        if not normalized:
            raise ValueError(
                "query cannot be empty"
            )

        intent = self._detect_intent(
            normalized
        )

        exhaustive = self._detect_exhaustive(
            normalized
        )

        filters = self._extract_filters(
            normalized,
            exhaustive=exhaustive,
        )

        if not filters.is_empty():
            intent = QueryIntent.FILTERED_SEARCH

        normalized_query = self._normalize_search_query(
            normalized,
            exhaustive=exhaustive,
        )

        return ParsedQuery(
            original_query=query,
            normalized_query=normalized_query,
            intent=intent,
            filters=filters,
            exhaustive=exhaustive,
        )

    # ======================================================================
    # INTENT
    # ======================================================================

    def _detect_intent(
        self,
        query: str,
    ) -> QueryIntent:

        lowered = query.lower()

        question_patterns = [
            r"^what\b",
            r"^who\b",
            r"^when\b",
            r"^where\b",
            r"^why\b",
            r"^how\b",
            r"\?$",
        ]

        lookup_patterns = [
            r"\bfind\b",
            r"\bshow\b",
            r"\bget\b",
            r"\blocate\b",
            r"\bretrieve\b",
            r"\bsearch\b",
            r"\blist\b",
        ]

        if any(
            re.search(
                pattern,
                lowered,
            )
            for pattern in question_patterns
        ):
            return QueryIntent.QUESTION_ANSWERING

        if any(
            re.search(
                pattern,
                lowered,
            )
            for pattern in lookup_patterns
        ):
            return QueryIntent.DOCUMENT_LOOKUP

        return QueryIntent.SEARCH

    # ======================================================================
    # EXHAUSTIVE SEARCH
    # ======================================================================

    @staticmethod
    def _detect_exhaustive(
        query: str,
    ) -> bool:
        """
        Detect whether the user is asking for all matching documents.

        Examples:

            find all invoices
            show all contracts
            list all resumes
            retrieve every report
            get every invoice
        """

        lowered = query.lower()

        exhaustive_patterns = [
            r"\ball\b",
            r"\bevery\b",
            r"\beach\b",
        ]

        return any(
            re.search(
                pattern,
                lowered,
            )
            for pattern in exhaustive_patterns
        )

    # ======================================================================
    # NORMALIZE SEARCH QUERY
    # ======================================================================

    def _normalize_search_query(
        self,
        query: str,
        exhaustive: bool = False,
    ) -> str:
        """
        Remove command-like words from the retrieval query.

        Examples:

            find all invoices
                -> invoice

            show all contracts
                -> contract

            find invoices above 100000
                -> invoices above 100000

            resumes with Kubernetes experience
                -> resumes with Kubernetes experience

        The goal is to send useful search text to the retrieval engine
        rather than commands such as "find all".
        """

        normalized = query.strip()

        # Remove common lookup commands from the beginning.
        normalized = re.sub(
            r"^\s*(?:find|show|get|locate|retrieve|search|list)\b\s*",
            "",
            normalized,
            flags=re.IGNORECASE,
        )

        # Remove "all/every/each" when used as lookup modifiers.
        normalized = re.sub(
            r"^\s*(?:all|every|each)\b\s*",
            "",
            normalized,
            flags=re.IGNORECASE,
        )

        normalized = " ".join(
            normalized.split()
        )

        # If the query became empty, fall back to the original query.
        if not normalized:
            normalized = query.strip()

        return normalized

    # ======================================================================
    # FILTER EXTRACTION
    # ======================================================================

    def _extract_filters(
        self,
        query: str,
        exhaustive: bool = False,
    ) -> QueryFilters:

        lowered = query.lower()

        amount_min, amount_max = (
            self._extract_amount_range(
                lowered
            )
        )

        created_after, created_before = (
            self._extract_date_range(
                lowered
            )
        )

        document_type = (
            self._extract_document_type(
                lowered,
                exhaustive=exhaustive,
            )
        )

        return QueryFilters(
            document_type=document_type,
            company_id=(
                self._extract_company_id(
                    lowered
                )
            ),
            created_after=created_after,
            created_before=created_before,
            amount_min=amount_min,
            amount_max=amount_max,
        )

    # ======================================================================
    # DOCUMENT TYPE
    # ======================================================================

    @classmethod
    def _extract_document_type(
        cls,
        query: str,
        exhaustive: bool = False,
    ) -> str | None:
        """
        Extract document type.

        Explicit syntax always produces a filter:

            document type: invoice
            document_type=invoice
            type: invoice
            file type: invoice

        For exhaustive lookup queries, ordinary document type words are
        also promoted to metadata filters:

            find all invoices
            show all contracts
            list all resumes

        Ordinary non-exhaustive searches remain unchanged:

            invoice
            invoice total
            unpaid invoice
            resumes with Kubernetes
        """

        # ------------------------------------------------------------------
        # Explicit document type syntax
        # ------------------------------------------------------------------

        explicit_patterns = [
            r"\bdocument\s+type\s*[:=]\s*([a-zA-Z_-]+)",
            r"\bdocument_type\s*[:=]\s*([a-zA-Z_-]+)",
            r"\bfile\s+type\s*[:=]?\s*([a-zA-Z_-]+)",
            r"\btype\s*[:=]\s*([a-zA-Z_-]+)",
        ]

        for pattern in explicit_patterns:

            match = re.search(
                pattern,
                query,
            )

            if not match:
                continue

            value = match.group(1).lower()

            return cls.DOCUMENT_TYPES.get(
                value
            )

        # ------------------------------------------------------------------
        # Exhaustive natural-language lookup
        # ------------------------------------------------------------------

        if exhaustive:

            # Prefer plural/singular document type matching.
            document_pattern = (
                r"\b("
                + "|".join(
                    re.escape(value)
                    for value in cls.DOCUMENT_TYPES
                )
                + r")\b"
            )

            match = re.search(
                document_pattern,
                query,
            )

            if match:
                value = match.group(1).lower()

                return cls.DOCUMENT_TYPES.get(
                    value
                )

        # ------------------------------------------------------------------
        # Ordinary search text does not become metadata filter.
        # ------------------------------------------------------------------

        return None

    # ======================================================================
    # COMPANY
    # ======================================================================

    @staticmethod
    def _extract_company_id(
        query: str,
    ) -> str | None:

        patterns = [
            r"\bcompany(?:\s+id)?\s*[:=]\s*([A-Za-z0-9_-]+)",
            r"\bcompany\s+([A-Za-z0-9_-]+)",
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                query,
            )

            if match:
                return match.group(1)

        return None

    # ======================================================================
    # AMOUNTS
    # ======================================================================

    @classmethod
    def _extract_amount_range(
        cls,
        query: str,
    ) -> tuple[
        Decimal | None,
        Decimal | None,
    ]:
        """
        Extract minimum/maximum monetary constraints.

        Examples:

            above 10000
            over $10,000
            greater than 10000
            more than $10,000
            at least $10,000

            below 10000
            under $10,000
            less than 10000
            at most $10,000

            between $10,000 and $50,000
        """

        # ------------------------------------------------------------------
        # Between X and Y
        # ------------------------------------------------------------------

        between_pattern = (
            r"\bbetween\s+"
            r"\$?\s*([\d,]+(?:\.\d+)?)"
            r"\s+and\s+"
            r"\$?\s*([\d,]+(?:\.\d+)?)"
        )

        match = re.search(
            between_pattern,
            query,
        )

        if match:

            minimum = cls._decimal(
                match.group(1)
            )

            maximum = cls._decimal(
                match.group(2)
            )

            return minimum, maximum

        # ------------------------------------------------------------------
        # Minimum
        # ------------------------------------------------------------------

        minimum_patterns = [
            (
                r"(?:above|over|greater than|"
                r"more than|at least)\s+"
                r"\$?\s*([\d,]+(?:\.\d+)?)"
            ),
            (
                r"\$?\s*([\d,]+(?:\.\d+)?)"
                r"\s*(?:and above|or more)"
            ),
        ]

        for pattern in minimum_patterns:

            match = re.search(
                pattern,
                query,
            )

            if match:

                return (
                    cls._decimal(
                        match.group(1)
                    ),
                    None,
                )

        # ------------------------------------------------------------------
        # Maximum
        # ------------------------------------------------------------------

        maximum_patterns = [
            (
                r"(?:below|under|less than|"
                r"at most)\s+"
                r"\$?\s*([\d,]+(?:\.\d+)?)"
            ),
            (
                r"\$?\s*([\d,]+(?:\.\d+)?)"
                r"\s*(?:and below|or less)"
            ),
        ]

        for pattern in maximum_patterns:

            match = re.search(
                pattern,
                query,
            )

            if match:

                return (
                    None,
                    cls._decimal(
                        match.group(1)
                    ),
                )

        return None, None

    # ======================================================================
    # DECIMAL
    # ======================================================================

    @staticmethod
    def _decimal(
        value: str,
    ) -> Decimal | None:

        try:
            return Decimal(
                value.replace(",", "")
            )
        except (
            ValueError,
            ArithmeticError,
        ):
            return None

    # ======================================================================
    # DATES
    # ======================================================================

    @staticmethod
    def _extract_date_range(
        query: str,
    ) -> tuple[
        date | None,
        date | None,
    ]:
        """
        Extract common relative date ranges.

        Examples:

            today
            this week
            this month
        """

        today = date.today()

        # ------------------------------------------------------------------
        # Today
        # ------------------------------------------------------------------

        if re.search(
            r"\btoday\b",
            query,
        ):
            return today, today

        # ------------------------------------------------------------------
        # This week
        # ------------------------------------------------------------------

        if re.search(
            r"\bthis week\b",
            query,
        ):
            start = today - timedelta(
                days=today.weekday()
            )

            return start, today

        # ------------------------------------------------------------------
        # This month
        # ------------------------------------------------------------------

        if re.search(
            r"\bthis month\b",
            query,
        ):
            start = today.replace(
                day=1
            )

            return start, today

        return None, None


__all__ = [
    "ParsedQuery",
    "QueryParser",
]