
"""
app/assistant/query_router.py

Deterministic query routing for the AI Assistant.

Responsibilities
----------------
- Classify assistant queries before context retrieval.
- Decide which application data sources are relevant.
- Keep routing deterministic and explainable.
- Avoid using the LLM merely to decide where application data lives.

The router does NOT:
- access the database
- perform retrieval
- call the LLM
- construct prompts
- generate answers

It only returns a normalized routing decision.

Supported routes
----------------
operational_processing
    Processing jobs, processing status, recently processed documents,
    failed processing, processing history, pipeline execution.

operational_documents
    Document metadata, uploaded documents, filenames, document versions.

review
    Human review, review queue, documents awaiting review, reviewer decisions.

intelligence
    Risk, classification, intelligence results, high-risk documents,
    extracted intelligence.

knowledge
    Questions about the actual content of documents and RAG/search.

hybrid
    Queries that require more than one application source.

general
    Normal conversational/general questions where application context
    is not required.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping


# ---------------------------------------------------------------------------
# Route names
# ---------------------------------------------------------------------------

ROUTE_OPERATIONAL_PROCESSING = "operational_processing"
ROUTE_OPERATIONAL_DOCUMENTS = "operational_documents"
ROUTE_REVIEW = "review"
ROUTE_INTELLIGENCE = "intelligence"
ROUTE_KNOWLEDGE = "knowledge"
ROUTE_HYBRID = "hybrid"
ROUTE_GENERAL = "general"


@dataclass(frozen=True)
class QueryRoute:
    """
    Normalized assistant query routing decision.
    """

    route: str
    confidence: float
    sources: tuple[str, ...]
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "route": self.route,
            "confidence": self.confidence,
            "sources": list(self.sources),
            "reason": self.reason,
        }


class QueryRouter:
    """
    Deterministic assistant query router.

    The implementation intentionally uses transparent keyword/pattern
    matching as the first routing layer. This is preferable for
    operational enterprise queries because:

    - behavior is predictable
    - routing can be audited
    - no additional LLM call is required
    - routing failures are easier to debug
    - sensitive application data is not sent to an LLM merely for routing

    A learned/LLM router can be added later behind the same interface.
    """

    # ------------------------------------------------------------------
    # Keyword groups
    # ------------------------------------------------------------------

    PROCESSING_TERMS = (
        "processed",
        "processing",
        "process",
        "processing job",
        "processing jobs",
        "processing status",
        "processing history",
        "processing failed",
        "failed processing",
        "processing error",
        "processing errors",
        "pipeline",
        "pipeline execution",
        "ocr",
        "extraction",
        "chunking",
        "embedding",
        "indexing",
        "stage",
        "stages",
        "job status",
        "job",
        "jobs",
        "completed processing",
        "recently processed",
        "processed recently",
    )

    DOCUMENT_TERMS = (
        "document",
        "documents",
        "file",
        "files",
        "filename",
        "file name",
        "uploaded",
        "upload",
        "uploads",
        "version",
        "versions",
        "document version",
        "document versions",
        "mime type",
        "file size",
        "page count",
        "document metadata",
    )

    REVIEW_TERMS = (
        "review",
        "reviewer",
        "human review",
        "human reviewer",
        "review queue",
        "needs review",
        "need review",
        "awaiting review",
        "pending review",
        "review decision",
        "review decisions",
        "approve",
        "approved",
        "reject",
        "rejected",
    )

    INTELLIGENCE_TERMS = (
        "risk",
        "risky",
        "high risk",
        "low risk",
        "intelligence",
        "intelligence result",
        "classification",
        "classified",
        "entity",
        "entities",
        "finding",
        "findings",
        "insight",
        "insights",
        "anomaly",
        "anomalies",
        "alert",
        "alerts",
    )

    KNOWLEDGE_TERMS = (
        "what does",
        "what do",
        "according to",
        "according to the document",
        "according to the documents",
        "according to this document",
        "explain",
        "summarize",
        "summary",
        "summarise",
        "summarize the document",
        "summarise the document",
        "content",
        "clause",
        "clauses",
        "contract says",
        "document says",
        "documents say",
        "mentions",
        "mentioned",
        "states",
        "stated",
        "section",
        "sections",
        "provision",
        "provisions",
        "termination",
        "obligation",
        "obligations",
        "what is stated",
        "what are the requirements",
        "find in the document",
        "search the document",
        "search documents",
    )

    # ------------------------------------------------------------------
    # Time / operational indicators
    # ------------------------------------------------------------------

    RECENCY_TERMS = (
        "recent",
        "recently",
        "latest",
        "last",
        "today",
        "yesterday",
        "this week",
        "this month",
        "past hour",
        "past day",
        "past week",
        "past month",
        "newest",
    )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def route(
        self,
        query: str,
        *,
        context: Mapping[str, Any] | None = None,
    ) -> QueryRoute:
        """
        Route an assistant query.

        Parameters
        ----------
        query:
            User's natural-language question.

        context:
            Optional caller-provided context. Currently used only for
            future extensibility and not trusted for routing decisions.

        Returns
        -------
        QueryRoute
            Normalized routing decision.
        """

        del context  # Reserved for future routing hints.

        normalized = self._normalize(query)

        if not normalized:
            return QueryRoute(
                route=ROUTE_GENERAL,
                confidence=1.0,
                sources=(),
                reason="Empty query.",
            )

        scores = {
            ROUTE_OPERATIONAL_PROCESSING: self._score(
                normalized,
                self.PROCESSING_TERMS,
            ),
            ROUTE_OPERATIONAL_DOCUMENTS: self._score(
                normalized,
                self.DOCUMENT_TERMS,
            ),
            ROUTE_REVIEW: self._score(
                normalized,
                self.REVIEW_TERMS,
            ),
            ROUTE_INTELLIGENCE: self._score(
                normalized,
                self.INTELLIGENCE_TERMS,
            ),
            ROUTE_KNOWLEDGE: self._score(
                normalized,
                self.KNOWLEDGE_TERMS,
            ),
        }

        # --------------------------------------------------------------
        # Strong operational processing signal
        # --------------------------------------------------------------

        if self._contains_any(normalized, self.RECENCY_TERMS):
            if scores[ROUTE_OPERATIONAL_PROCESSING] > 0:
                scores[ROUTE_OPERATIONAL_PROCESSING] += 3.0

        # --------------------------------------------------------------
        # Explicit hybrid patterns
        # --------------------------------------------------------------

        hybrid_processing_knowledge = (
            scores[ROUTE_OPERATIONAL_PROCESSING] > 0
            and scores[ROUTE_KNOWLEDGE] > 0
        )

        hybrid_processing_risk = (
            scores[ROUTE_OPERATIONAL_PROCESSING] > 0
            and scores[ROUTE_INTELLIGENCE] > 0
        )

        hybrid_document_risk = (
            scores[ROUTE_OPERATIONAL_DOCUMENTS] > 0
            and scores[ROUTE_INTELLIGENCE] > 0
        )

        hybrid_document_review = (
            scores[ROUTE_OPERATIONAL_DOCUMENTS] > 0
            and scores[ROUTE_REVIEW] > 0
        )

        hybrid_knowledge_risk = (
            scores[ROUTE_KNOWLEDGE] > 0
            and scores[ROUTE_INTELLIGENCE] > 0
        )

        if (
            hybrid_processing_knowledge
            or hybrid_processing_risk
            or hybrid_document_risk
            or hybrid_document_review
            or hybrid_knowledge_risk
        ):
            sources = self._sources_for_hybrid(scores)

            return QueryRoute(
                route=ROUTE_HYBRID,
                confidence=0.90,
                sources=tuple(sources),
                reason="Query contains signals requiring multiple application data sources.",
            )

        # --------------------------------------------------------------
        # Select highest scoring route
        # --------------------------------------------------------------

        best_route, best_score = max(
            scores.items(),
            key=lambda item: item[1],
        )

        if best_score <= 0:
            return QueryRoute(
                route=ROUTE_GENERAL,
                confidence=0.75,
                sources=(),
                reason="No application-specific routing signal detected.",
            )

        confidence = self._confidence(scores, best_route)

        sources = self._sources_for_route(best_route)

        return QueryRoute(
            route=best_route,
            confidence=confidence,
            sources=tuple(sources),
            reason=self._reason_for_route(best_route),
        )

    # ------------------------------------------------------------------
    # Compatibility aliases
    # ------------------------------------------------------------------

    def classify(
        self,
        query: str,
        *,
        context: Mapping[str, Any] | None = None,
    ) -> QueryRoute:
        """
        Compatibility alias for callers using ``classify``.
        """

        return self.route(query, context=context)

    def resolve(
        self,
        query: str,
        *,
        context: Mapping[str, Any] | None = None,
    ) -> QueryRoute:
        """
        Compatibility alias for callers using ``resolve``.
        """

        return self.route(query, context=context)

    def route_query(
        self,
        query: str,
        *,
        context: Mapping[str, Any] | None = None,
    ) -> QueryRoute:
        """
        Compatibility alias for callers using ``route_query``.
        """

        return self.route(query, context=context)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize(query: str) -> str:
        return re.sub(
            r"\s+",
            " ",
            str(query or "").strip().lower(),
        )

    @staticmethod
    def _contains_any(
        query: str,
        terms: tuple[str, ...],
    ) -> bool:
        return any(term in query for term in terms)

    @staticmethod
    def _score(
        query: str,
        terms: tuple[str, ...],
    ) -> float:
        score = 0.0

        for term in terms:
            if term in query:
                # Multi-word phrases are stronger signals than
                # single words.
                score += 2.0 if " " in term else 1.0

        return score

    @staticmethod
    def _confidence(
        scores: dict[str, float],
        best_route: str,
    ) -> float:
        best = scores[best_route]

        if best >= 6:
            return 0.97

        if best >= 4:
            return 0.93

        if best >= 2:
            return 0.88

        return 0.80

    @staticmethod
    def _sources_for_route(route: str) -> list[str]:
        mapping = {
            ROUTE_OPERATIONAL_PROCESSING: [
                "processing",
                "documents",
            ],
            ROUTE_OPERATIONAL_DOCUMENTS: [
                "documents",
            ],
            ROUTE_REVIEW: [
                "review",
            ],
            ROUTE_INTELLIGENCE: [
                "intelligence",
            ],
            ROUTE_KNOWLEDGE: [
                "knowledge",
            ],
            ROUTE_GENERAL: [],
        }

        return mapping.get(route, [])

    @staticmethod
    def _sources_for_hybrid(
        scores: dict[str, float],
    ) -> list[str]:
        sources: list[str] = []

        if scores[ROUTE_OPERATIONAL_PROCESSING] > 0:
            sources.append("processing")

        if scores[ROUTE_OPERATIONAL_DOCUMENTS] > 0:
            sources.append("documents")

        if scores[ROUTE_REVIEW] > 0:
            sources.append("review")

        if scores[ROUTE_INTELLIGENCE] > 0:
            sources.append("intelligence")

        if scores[ROUTE_KNOWLEDGE] > 0:
            sources.append("knowledge")

        return sources

    @staticmethod
    def _reason_for_route(route: str) -> str:
        reasons = {
            ROUTE_OPERATIONAL_PROCESSING: (
                "Query refers to document processing, processing jobs, "
                "pipeline execution, or processing status."
            ),
            ROUTE_OPERATIONAL_DOCUMENTS: (
                "Query refers to document or uploaded-file metadata."
            ),
            ROUTE_REVIEW: (
                "Query refers to human review or review decisions."
            ),
            ROUTE_INTELLIGENCE: (
                "Query refers to risk, classification, findings, "
                "or intelligence results."
            ),
            ROUTE_KNOWLEDGE: (
                "Query asks about document content and should use "
                "knowledge retrieval."
            ),
            ROUTE_GENERAL: (
                "No application-specific source is required."
            ),
        }

        return reasons.get(
            route,
            "Application-specific routing decision.",
        )


__all__ = [
    "QueryRoute",
    "QueryRouter",
    "ROUTE_OPERATIONAL_PROCESSING",
    "ROUTE_OPERATIONAL_DOCUMENTS",
    "ROUTE_REVIEW",
    "ROUTE_INTELLIGENCE",
    "ROUTE_KNOWLEDGE",
    "ROUTE_HYBRID",
    "ROUTE_GENERAL",
]

