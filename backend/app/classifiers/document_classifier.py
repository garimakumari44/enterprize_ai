"""
Advanced document type classifier.

Supported document types
------------------------
- Invoice
- Receipt
- Passport
- Resume / CV
- Driving License
- Bank Statement

The classifier is intentionally provider-independent. It uses OCR/text
signals today and can later be combined with ML/layout classifiers such as:

- LayoutLM
- LayoutLMv3
- Donut
- DocFormer
- Azure Document Intelligence
- AWS Textract
- Google Document AI
- Gemini / multimodal models

Design goals
------------
- Deterministic
- Explainable
- Backward compatible
- Robust against noisy OCR
- Weighted evidence instead of simple keyword counting
- Supports ambiguous/unknown documents
- Easy to extend
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class PatternRule:
    """
    A classification rule.

    pattern:
        Regular expression searched against normalized OCR text.

    weight:
        Importance of the matched signal.

    evidence:
        Human-readable explanation returned to the caller.

    strong:
        Marks the rule as a high-value identifying signal.
    """

    pattern: str
    weight: float
    evidence: str
    strong: bool = False


class DocumentClassifier:
    """
    Explainable rule-based document classifier.

    The classifier is designed as the first layer of a larger document
    intelligence system.

    Classification flow
    -------------------
        OCR text
             ↓
        normalization
             ↓
        document-specific rules
             ↓
        positive evidence
             ↓
        negative/conflicting evidence
             ↓
        confidence calculation
             ↓
        primary + alternatives
    """

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    MIN_SCORE = 1.5

    # Minimum confidence before we call the classification reliable.
    MIN_CONFIDENCE = 0.45

    # If the difference between the best and second-best classification
    # is too small, the result is considered ambiguous.
    AMBIGUITY_MARGIN = 0.10

    # Maximum evidence items returned per document type.
    MAX_EVIDENCE = 12

    # ------------------------------------------------------------------
    # Document classification rules
    # ------------------------------------------------------------------

    DOCUMENT_RULES: Dict[str, List[PatternRule]] = {
        "invoice": [
            PatternRule(
                r"\binvoice\b",
                3.0,
                "invoice",
                strong=True,
            ),
            PatternRule(
                r"\binvoice\s*(number|no\.?|#)\b",
                4.0,
                "invoice number",
                strong=True,
            ),
            PatternRule(
                r"\b(bill|billing)\s*(to|address)\b",
                2.5,
                "bill-to information",
                strong=True,
            ),
            PatternRule(
                r"\b(ship|shipping)\s*(to|address)\b",
                1.5,
                "ship-to information",
            ),
            PatternRule(
                r"\b(due\s*date|payment\s*due)\b",
                3.0,
                "payment due date",
                strong=True,
            ),
            PatternRule(
                r"\b(subtotal|sub-total)\b",
                1.5,
                "subtotal",
            ),
            PatternRule(
                r"\b(tax|vat|gst)\b",
                1.0,
                "tax information",
            ),
            PatternRule(
                r"\b(amount\s*due|balance\s*due|total\s*due)\b",
                2.5,
                "amount due",
                strong=True,
            ),
            PatternRule(
                r"\b(unit\s*price|quantity|qty)\b",
                1.0,
                "line-item pricing",
            ),
            PatternRule(
                r"\b(purchase\s*order|po\s*(number|no\.?|#))\b",
                1.5,
                "purchase order reference",
            ),
        ],
        "receipt": [
            PatternRule(
                r"\breceipt\b",
                4.0,
                "receipt",
                strong=True,
            ),
            PatternRule(
                r"\b(transaction\s*(id|number|no\.?|#))\b",
                2.5,
                "transaction identifier",
                strong=True,
            ),
            PatternRule(
                r"\b(change|change\s*due)\b",
                3.0,
                "change due",
            ),
            PatternRule(
                r"\b(cash|card|credit\s*card|debit\s*card)\b",
                1.5,
                "payment method",
            ),
            PatternRule(
                r"\b(tendered|amount\s*tendered)\b",
                2.0,
                "amount tendered",
            ),
            PatternRule(
                r"\b(merchant|store|shop)\b",
                1.0,
                "merchant information",
            ),
            PatternRule(
                r"\b(thank\s*you|thanks\s*for\s*(shopping|your\s*purchase))\b",
                1.5,
                "purchase acknowledgement",
            ),
            PatternRule(
                r"\b(receipt\s*(no|number|#))\b",
                2.5,
                "receipt number",
            ),
        ],
        "passport": [
            PatternRule(
                r"\bpassport\b",
                5.0,
                "passport",
                strong=True,
            ),
            PatternRule(
                r"\bnationality\b",
                2.5,
                "nationality",
                strong=True,
            ),
            PatternRule(
                r"\b(date\s*of\s*birth|dob)\b",
                2.0,
                "date of birth",
            ),
            PatternRule(
                r"\b(place\s*of\s*birth|pob)\b",
                2.0,
                "place of birth",
            ),
            PatternRule(
                r"\b(passport\s*(no|number|#))\b",
                4.0,
                "passport number",
                strong=True,
            ),
            PatternRule(
                r"\b(date\s*of\s*(issue|issuance))\b",
                2.0,
                "passport issue date",
            ),
            PatternRule(
                r"\b(date\s*of\s*expiry|expiry\s*date|expiration\s*date)\b",
                2.5,
                "passport expiry date",
            ),
            PatternRule(
                r"\b(sex|gender)\b",
                1.0,
                "sex/gender field",
            ),
            PatternRule(
                r"\b(mrz|machine\s*readable\s*zone)\b",
                5.0,
                "machine-readable zone",
                strong=True,
            ),
            PatternRule(
                r"\b(document\s*(type|code))\b",
                1.5,
                "document type code",
            ),
        ],
        "resume": [
            PatternRule(
                r"\b(resume|résumé|curriculum\s*vitae|cv)\b",
                4.0,
                "resume/CV",
                strong=True,
            ),
            PatternRule(
                r"\b(work\s*experience|professional\s*experience)\b",
                3.0,
                "work experience",
                strong=True,
            ),
            PatternRule(
                r"\beducation\b",
                2.0,
                "education",
            ),
            PatternRule(
                r"\b(skills|technical\s*skills|core\s*skills)\b",
                2.0,
                "skills section",
            ),
            PatternRule(
                r"\b(certifications?|certificates?)\b",
                1.5,
                "certifications",
            ),
            PatternRule(
                r"\b(employment|professional\s*summary|career\s*objective)\b",
                1.5,
                "career information",
            ),
            PatternRule(
                r"\b(projects?|academic\s*projects?)\b",
                1.0,
                "projects section",
            ),
            PatternRule(
                r"\b(achievements?|accomplishments?)\b",
                1.0,
                "achievements",
            ),
            PatternRule(
                r"\b(linkedin|github|portfolio)\b",
                1.0,
                "professional profile link",
            ),
        ],
        "driving_license": [
            PatternRule(
                r"\b(driver'?s?\s*licen[cs]e)\b",
                5.0,
                "driver's license",
                strong=True,
            ),
            PatternRule(
                r"\bdriving\s*licen[cs]e\b",
                5.0,
                "driving license",
                strong=True,
            ),
            PatternRule(
                r"\blicen[cs]e\s*(number|no\.?|#)\b",
                3.0,
                "license number",
                strong=True,
            ),
            PatternRule(
                r"\b(dob|date\s*of\s*birth)\b",
                1.5,
                "date of birth",
            ),
            PatternRule(
                r"\b(date\s*of\s*issue|issued)\b",
                2.0,
                "license issue date",
            ),
            PatternRule(
                r"\b(date\s*of\s*expiry|expiry|expires)\b",
                2.0,
                "license expiry date",
            ),
            PatternRule(
                r"\b(vehicle\s*class|class)\b",
                1.5,
                "vehicle class",
            ),
            PatternRule(
                r"\b(address|residential\s*address)\b",
                1.0,
                "address",
            ),
            PatternRule(
                r"\b(authority|issuing\s*authority)\b",
                1.0,
                "issuing authority",
            ),
        ],
        "bank_statement": [
            PatternRule(
                r"\bbank\s*statement\b",
                5.0,
                "bank statement",
                strong=True,
            ),
            PatternRule(
                r"\b(statement\s*(period|date|from|to))\b",
                3.0,
                "statement period",
                strong=True,
            ),
            PatternRule(
                r"\b(account\s*(number|no\.?|#))\b",
                3.0,
                "account number",
                strong=True,
            ),
            PatternRule(
                r"\b(available\s*balance)\b",
                3.0,
                "available balance",
            ),
            PatternRule(
                r"\b(opening\s*balance)\b",
                2.0,
                "opening balance",
            ),
            PatternRule(
                r"\b(closing\s*balance)\b",
                2.5,
                "closing balance",
            ),
            PatternRule(
                r"\b(debit|credit)\b",
                1.0,
                "debit/credit transaction",
            ),
            PatternRule(
                r"\b(transaction\s*(date|description))\b",
                1.5,
                "transaction details",
            ),
            PatternRule(
                r"\b(account\s*(holder|name))\b",
                1.5,
                "account holder",
            ),
            PatternRule(
                r"\b(ifsc|swift|iban|routing\s*number)\b",
                2.0,
                "banking identifier",
            ),
            PatternRule(
                r"\b(balance\s*(forward|brought\s*forward))\b",
                1.5,
                "balance carry-forward",
            ),
        ],
    }

    # ------------------------------------------------------------------
    # Negative/conflicting signals
    # ------------------------------------------------------------------

    NEGATIVE_RULES: Dict[str, List[PatternRule]] = {
        "invoice": [
            PatternRule(
                r"\bchange\s*due\b",
                2.0,
                "receipt-style change due",
            ),
        ],
        "receipt": [
            PatternRule(
                r"\bdue\s*date\b",
                2.0,
                "invoice-style due date",
            ),
            PatternRule(
                r"\binvoice\s*(number|no\.?|#)\b",
                2.5,
                "invoice number",
            ),
        ],
        "resume": [
            PatternRule(
                r"\baccount\s*(number|no\.?|#)\b",
                1.5,
                "banking account identifier",
            ),
        ],
        "bank_statement": [
            PatternRule(
                r"\bwork\s*experience\b",
                2.0,
                "resume-style work experience",
            ),
        ],
    }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def classify(
        self,
        text: str,
        *,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Classify a document from OCR/extracted text.

        Parameters
        ----------
        text:
            OCR or extracted document text.

        metadata:
            Optional document metadata. Reserved for future layout/model
            signals and does not affect classification unless supported
            explicitly.

        Returns
        -------
        dict
            Backward-compatible classification result with additional
            evidence and alternative predictions.
        """

        del metadata  # Reserved for future classifier signals.

        normalized = self._normalize_text(text)

        if not normalized:
            return self._unknown_result(
                reason="No usable text was available for classification."
            )

        scores: Dict[str, float] = {}
        evidence: Dict[str, List[str]] = {}
        strong_matches: Dict[str, int] = {}

        for document_type, rules in self.DOCUMENT_RULES.items():
            positive_score = 0.0
            negative_score = 0.0
            doc_evidence: List[str] = []
            strong_count = 0

            # Positive evidence
            for rule in rules:
                if self._matches(rule.pattern, normalized):
                    positive_score += rule.weight

                    if rule.evidence not in doc_evidence:
                        doc_evidence.append(rule.evidence)

                    if rule.strong:
                        strong_count += 1

            # Negative/conflicting evidence
            for rule in self.NEGATIVE_RULES.get(document_type, []):
                if self._matches(rule.pattern, normalized):
                    negative_score += rule.weight

            final_score = max(
                positive_score - negative_score,
                0.0,
            )

            scores[document_type] = final_score
            evidence[document_type] = doc_evidence[: self.MAX_EVIDENCE]
            strong_matches[document_type] = strong_count

        ranked = sorted(
            scores.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        if not ranked or ranked[0][1] < self.MIN_SCORE:
            return self._unknown_result(
                reason="Insufficient document-specific evidence.",
                scores=scores,
            )

        best_type, best_score = ranked[0]

        second_score = ranked[1][1] if len(ranked) > 1 else 0.0

        confidence = self._calculate_confidence(
            best_type=best_type,
            best_score=best_score,
            second_score=second_score,
            strong_matches=strong_matches.get(best_type, 0),
            evidence_count=len(evidence.get(best_type, [])),
        )

        ambiguous = self._is_ambiguous(
            best_score=best_score,
            second_score=second_score,
            confidence=confidence,
        )

        # If there is weak/conflicting evidence, do not pretend the
        # classification is highly reliable.
        document_type = best_type

        if ambiguous:
            document_type = "unknown"

        alternatives = self._build_alternatives(
            ranked=ranked,
            best_type=best_type,
            scores=scores,
            evidence=evidence,
        )

        return {
            # Existing API fields
            "document_type": document_type,
            "confidence": round(confidence, 2),
            "score": round(best_score, 2),

            # Advanced diagnostics
            "ambiguous": ambiguous,
            "evidence": evidence.get(best_type, []),
            "alternatives": alternatives,
            "scores": {
                key: round(value, 2)
                for key, value in scores.items()
            },
            "strong_matches": strong_matches.get(best_type, 0),
            "classifier": "rule_based_advanced",
        }

    # ------------------------------------------------------------------
    # Normalization
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_text(text: Any) -> str:
        """
        Normalize noisy OCR text.

        Handles:
        - None
        - non-string input
        - repeated whitespace
        - Unicode-ish OCR spacing
        - case normalization
        """

        if text is None:
            return ""

        if not isinstance(text, str):
            text = str(text)

        text = text.replace("\x00", " ")

        # Normalize common OCR whitespace.
        text = re.sub(r"\s+", " ", text)

        return text.strip().lower()

    # ------------------------------------------------------------------
    # Matching
    # ------------------------------------------------------------------

    @staticmethod
    def _matches(pattern: str, text: str) -> bool:
        """
        Safely evaluate a regular expression.

        Invalid patterns should never crash document processing.
        """

        try:
            return re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            ) is not None
        except re.error:
            return False

    # ------------------------------------------------------------------
    # Confidence
    # ------------------------------------------------------------------

    @staticmethod
    def _calculate_confidence(
        *,
        best_type: str,
        best_score: float,
        second_score: float,
        strong_matches: int,
        evidence_count: int,
    ) -> float:
        """
        Calculate a calibrated heuristic confidence.

        Confidence intentionally depends on more than the raw score.

        Signals:
        - absolute evidence score
        - separation from second-best class
        - strong identifying matches
        - number of independent evidence signals
        """

        # Saturating score component.
        score_component = min(best_score / 10.0, 1.0)

        # How clearly the best class beats the runner-up.
        if best_score <= 0:
            margin_component = 0.0
        else:
            margin_component = max(
                0.0,
                min(
                    (best_score - second_score) / best_score,
                    1.0,
                ),
            )

        strong_component = min(
            strong_matches / 2.0,
            1.0,
        )

        evidence_component = min(
            evidence_count / 5.0,
            1.0,
        )

        confidence = (
            score_component * 0.40
            + margin_component * 0.25
            + strong_component * 0.20
            + evidence_component * 0.15
        )

        # Strong document-specific identifiers deserve a modest boost.
        if best_type in {
            "passport",
            "driving_license",
            "bank_statement",
        } and strong_matches >= 1:
            confidence += 0.05

        return max(
            0.0,
            min(confidence, 1.0),
        )

    # ------------------------------------------------------------------
    # Ambiguity detection
    # ------------------------------------------------------------------

    def _is_ambiguous(
        self,
        *,
        best_score: float,
        second_score: float,
        confidence: float,
    ) -> bool:
        """
        Determine whether classification should be marked unknown.

        This prevents the classifier from making an overly confident
        decision when two document types have similar evidence.
        """

        if best_score < self.MIN_SCORE:
            return True

        if confidence < self.MIN_CONFIDENCE:
            return True

        if second_score <= 0:
            return False

        relative_margin = (
            best_score - second_score
        ) / max(best_score, 1.0)

        return relative_margin < self.AMBIGUITY_MARGIN

    # ------------------------------------------------------------------
    # Alternatives
    # ------------------------------------------------------------------

    def _build_alternatives(
        self,
        *,
        ranked: List[Tuple[str, float]],
        best_type: str,
        scores: Dict[str, float],
        evidence: Dict[str, List[str]],
    ) -> List[Dict[str, Any]]:
        """
        Return the strongest alternative classifications.
        """

        alternatives: List[Dict[str, Any]] = []

        total_score = sum(
            max(value, 0.0)
            for value in scores.values()
        )

        for document_type, score in ranked:
            if document_type == best_type:
                continue

            if score <= 0:
                continue

            probability = (
                score / total_score
                if total_score > 0
                else 0.0
            )

            alternatives.append(
                {
                    "document_type": document_type,
                    "confidence": round(
                        min(probability, 1.0),
                        2,
                    ),
                    "score": round(score, 2),
                    "evidence": evidence.get(
                        document_type,
                        [],
                    )[:5],
                }
            )

            if len(alternatives) >= 3:
                break

        return alternatives

    # ------------------------------------------------------------------
    # Unknown result
    # ------------------------------------------------------------------

    @staticmethod
    def _unknown_result(
        *,
        reason: str,
        scores: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Standard unknown/low-confidence result.
        """

        return {
            "document_type": "unknown",
            "confidence": 0.0,
            "score": 0.0,
            "ambiguous": True,
            "evidence": [],
            "alternatives": [],
            "scores": {
                key: round(value, 2)
                for key, value in (scores or {}).items()
            },
            "strong_matches": 0,
            "classifier": "rule_based_advanced",
            "reason": reason,
        }


__all__ = [
    "DocumentClassifier",
]