"""
app/knowledge/query/query_filters.py

Structured filters extracted from natural-language knowledge queries.

These filters are converted into a retrieval-layer representation
that supports both equality and comparison operators.

Examples
--------

"invoice"
    -> {"document_type": "invoice"}

"above $100,000"
    -> {"amount": {"gte": "100000"}}

"between $50,000 and $100,000"
    -> {
        "amount": {
            "gte": "50000",
            "lte": "100000",
        }
    }
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any


@dataclass
class QueryFilters:
    """
    Structured filters extracted from a natural-language query.
    """

    document_type: str | None = None

    company_id: str | None = None

    created_after: date | None = None
    created_before: date | None = None

    amount_min: Decimal | None = None
    amount_max: Decimal | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    # ======================================================================
    # EMPTY
    # ======================================================================

    def is_empty(self) -> bool:
        """
        Return True when no structured filters are present.
        """

        return not any(
            [
                self.document_type,
                self.company_id,
                self.created_after,
                self.created_before,
                self.amount_min is not None,
                self.amount_max is not None,
                self.metadata,
            ]
        )

    # ======================================================================
    # RETRIEVAL REPRESENTATION
    # ======================================================================

    def to_dict(self) -> dict[str, Any]:
        """
        Convert filters into a retrieval-layer representation.

        Equality filters:

            {
                "document_type": "invoice",
                "company_id": "123"
            }

        Numeric comparison:

            {
                "amount": {
                    "gte": "100000"
                }
            }

        Date comparison:

            {
                "created_at": {
                    "gte": "2026-01-01",
                    "lte": "2026-08-31"
                }
            }
        """

        filters: dict[str, Any] = {}

        # ------------------------------------------------------------------
        # Document type
        # ------------------------------------------------------------------

        if self.document_type:
            filters["document_type"] = (
                self.document_type
            )

        # ------------------------------------------------------------------
        # Company
        # ------------------------------------------------------------------

        if self.company_id:
            filters["company_id"] = (
                self.company_id
            )

        # ------------------------------------------------------------------
        # Amount
        # ------------------------------------------------------------------

        amount_filter: dict[str, str] = {}

        if self.amount_min is not None:
            amount_filter["gte"] = str(
                self.amount_min
            )

        if self.amount_max is not None:
            amount_filter["lte"] = str(
                self.amount_max
            )

        if amount_filter:
            filters["amount"] = amount_filter

        # ------------------------------------------------------------------
        # Created date
        # ------------------------------------------------------------------

        created_filter: dict[str, str] = {}

        if self.created_after is not None:
            created_filter["gte"] = (
                self.created_after.isoformat()
            )

        if self.created_before is not None:
            created_filter["lte"] = (
                self.created_before.isoformat()
            )

        if created_filter:
            filters["created_at"] = created_filter

        # ------------------------------------------------------------------
        # Additional metadata
        # ------------------------------------------------------------------

        if self.metadata:
            filters["metadata"] = dict(
                self.metadata
            )

        return filters


__all__ = [
    "QueryFilters",
]