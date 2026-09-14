
"""
app.processing.providers.implementations.rule_based_classifier

Deterministic rule-based document classifier.

This provider intentionally has no ML or external dependencies.

It uses:
    - filename
    - MIME type
    - document text
    - configurable keyword rules

The implementation is designed to be a reliable fallback classifier
before introducing an ML/LLM-based classifier.
"""

from __future__ import annotations

import re
from typing import Any

from ..base import ProviderConfigurationError
from ..classification import (
    BaseClassificationProvider,
    ClassificationLabel,
    ClassificationRequest,
    ClassificationResult,
)


class RuleBasedClassifier(BaseClassificationProvider):
    """
    Deterministic document classifier.

    Supported labels:

        invoice
        receipt
        purchase_order
        contract
        resume
        bank_statement
        report
        email
        unknown
    """

    PROVIDER_NAME = "rule_based_classifier"

    PROVIDER_TYPE = "classification"

    VERSION = "1.0"

    LABELS = (
        "invoice",
        "receipt",
        "purchase_order",
        "contract",
        "resume",
        "bank_statement",
        "report",
        "email",
        "unknown",
    )

    DEFAULT_RULES: dict[str, tuple[str, ...]] = {
        "invoice": (
            "invoice",
            "invoice number",
            "invoice no",
            "invoice #",
            "subtotal",
            "amount due",
            "tax invoice",
            "bill to",
            "due date",
        ),
        "receipt": (
            "receipt",
            "transaction receipt",
            "purchase receipt",
            "cashier",
            "total paid",
            "payment received",
        ),
        "purchase_order": (
            "purchase order",
            "purchase order number",
            "po number",
            "po no",
            "order number",
            "vendor",
            "ship to",
            "buyer",
        ),
        "contract": (
            "agreement",
            "contract",
            "party hereby",
            "terms and conditions",
            "effective date",
            "whereas",
            "hereinafter",
            "signature",
        ),
        "resume": (
            "resume",
            "curriculum vitae",
            "professional experience",
            "work experience",
            "education",
            "skills",
            "employment history",
        ),
        "bank_statement": (
            "bank statement",
            "account statement",
            "account number",
            "opening balance",
            "closing balance",
            "transaction date",
            "debit",
            "credit",
            "available balance",
        ),
        "report": (
            "report",
            "executive summary",
            "findings",
            "analysis",
            "conclusion",
            "methodology",
            "recommendations",
        ),
        "email": (
            "from:",
            "to:",
            "subject:",
            "cc:",
            "sent:",
            "dear ",
            "regards,",
        ),
    }

    def __init__(
        self,
        *,
        config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            config=config
        )

        self._rules = self._build_rules()

    async def health_check(self) -> bool:
        return True

    def supported_labels(self) -> tuple[str, ...]:
        return self.LABELS

    def validate_config(self) -> None:
        threshold = self.get_config(
            "confidence_threshold",
            0.50,
        )

        try:
            threshold = float(
                threshold
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ProviderConfigurationError(
                "confidence_threshold must be numeric."
            ) from exc

        if not 0.0 <= threshold <= 1.0:
            raise ProviderConfigurationError(
                "confidence_threshold must be between 0 and 1."
            )

        max_labels = self.get_config(
            "max_labels",
            3,
        )

        try:
            max_labels = int(
                max_labels
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ProviderConfigurationError(
                "max_labels must be an integer."
            ) from exc

        if max_labels < 1:
            raise ProviderConfigurationError(
                "max_labels must be >= 1."
            )

    def _build_rules(
        self,
    ) -> dict[str, tuple[str, ...]]:
        configured = self.get_config(
            "rules"
        )

        if not configured:
            return dict(
                self.DEFAULT_RULES
            )

        if not isinstance(
            configured,
            dict,
        ):
            raise ProviderConfigurationError(
                "rules must be a mapping of label -> keywords."
            )

        rules: dict[str, tuple[str, ...]] = {}

        for label, keywords in configured.items():
            normalized_label = str(
                label
            ).strip().lower()

            if normalized_label not in self.LABELS:
                continue

            if not isinstance(
                keywords,
                (list, tuple, set),
            ):
                raise ProviderConfigurationError(
                    f"Rules for '{normalized_label}' "
                    "must be a sequence."
                )

            rules[
                normalized_label
            ] = tuple(
                str(keyword).strip().lower()
                for keyword in keywords
                if str(keyword).strip()
            )

        return rules

    @staticmethod
    def _normalize(
        text: str,
    ) -> str:
        text = text.lower()

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    def _combined_input(
        self,
        request: ClassificationRequest,
    ) -> str:
        parts: list[str] = []

        if request.filename:
            parts.append(
                request.filename
            )

        if request.mime_type:
            parts.append(
                request.mime_type
            )

        if request.text:
            parts.append(
                request.text
            )

        return self._normalize(
            " ".join(parts)
        )

    def _keyword_score(
        self,
        text: str,
        keyword: str,
    ) -> float:
        """
        Score a keyword match.

        Longer/more specific phrases receive more weight.
        """

        if not keyword:
            return 0.0

        if keyword in text:
            word_count = len(
                keyword.split()
            )

            if word_count >= 4:
                return 4.0

            if word_count == 3:
                return 3.0

            if word_count == 2:
                return 2.0

            return 1.0

        return 0.0

    def _score_labels(
        self,
        text: str,
    ) -> dict[str, float]:
        scores: dict[str, float] = {}

        for label, keywords in self._rules.items():
            score = 0.0

            for keyword in keywords:
                score += self._keyword_score(
                    text,
                    keyword,
                )

            if score > 0:
                scores[label] = score

        return scores

    def _confidence(
        self,
        score: float,
        second_score: float,
    ) -> float:
        """
        Convert rule score into bounded confidence.

        This is a heuristic confidence score, not a calibrated
        statistical probability.
        """

        if score <= 0:
            return 0.0

        base = min(
            0.95,
            0.45 + (
                score / 20.0
            ),
        )

        margin = max(
            0.0,
            score - second_score,
        )

        confidence = base + min(
            0.20,
            margin / 20.0,
        )

        return min(
            0.99,
            max(
                0.0,
                confidence,
            ),
        )

    async def classify(
        self,
        request: ClassificationRequest,
    ) -> ClassificationResult:
        request.validate()

        text = self._combined_input(
            request
        )

        scores = self._score_labels(
            text
        )

        if not scores:
            return ClassificationResult(
                document_id=request.document_id,
                primary_label="unknown",
                confidence=0.0,
                labels=[
                    ClassificationLabel(
                        label="unknown",
                        confidence=0.0,
                        rank=1,
                    )
                ],
                model="rule-based",
                version=self.VERSION,
                metadata={
                    "matched_rules": 0,
                },
                warnings=[
                    "No classification rules matched the document."
                ],
            )

        ranked = sorted(
            scores.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        primary_label, primary_score = (
            ranked[0]
        )

        second_score = (
            ranked[1][1]
            if len(ranked) > 1
            else 0.0
        )

        confidence = self._confidence(
            primary_score,
            second_score,
        )

        threshold = float(
            self.get_config(
                "confidence_threshold",
                0.50,
            )
        )

        if confidence < threshold:
            primary_label = "unknown"

        max_labels = int(
            self.get_config(
                "max_labels",
                3,
            )
        )

        labels: list[
            ClassificationLabel
        ] = []

        for rank, (
            label,
            score,
        ) in enumerate(
            ranked[:max_labels],
            start=1,
        ):
            next_score = (
                ranked[rank][1]
                if rank < len(ranked)
                else 0.0
            )

            label_confidence = (
                self._confidence(
                    score,
                    next_score,
                )
            )

            labels.append(
                ClassificationLabel(
                    label=label,
                    confidence=label_confidence,
                    rank=rank,
                    metadata={
                        "rule_score": score,
                    },
                )
            )

        warnings: list[str] = []

        if primary_label == "unknown":
            warnings.append(
                "Classification confidence was below the configured threshold."
            )

        return ClassificationResult(
            document_id=request.document_id,
            primary_label=primary_label,
            confidence=confidence,
            labels=labels,
            model="rule-based",
            version=self.VERSION,
            metadata={
                "matched_rules": len(scores),
                "rule_scores": scores,
            },
            warnings=warnings,
        )

