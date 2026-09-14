"""
Advanced document template classifier.

Maps a classified document to the most appropriate extraction template.

Responsibilities
----------------
- Resolve document types to extraction templates.
- Validate supported document types.
- Provide template metadata.
- Expose required and optional extraction fields.
- Support template versions.
- Return candidate templates for ambiguous classifications.
- Incorporate upstream document-classification confidence.
- Provide an extensible foundation for future:
    - Embedding similarity
    - Vector search
    - Layout embeddings
    - Template retrieval
    - ML-based template matching

This module intentionally does NOT perform field extraction.
The extraction engine is responsible for that.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional


@dataclass(frozen=True)
class TemplateDefinition:
    """
    Definition of an extraction template.
    """

    template: str
    document_type: str
    version: str
    description: str
    required_fields: tuple[str, ...]
    optional_fields: tuple[str, ...]
    aliases: tuple[str, ...] = ()
    priority: float = 1.0


class TemplateClassifier:
    """
    Advanced extraction-template resolver.

    The classifier receives the document type produced by the document
    classification stage and resolves it to an extraction template.

    Example
    -------
    Input:

        {
            "document_type": "invoice",
            "confidence": 0.94
        }

    Output:

        {
            "template": "invoice_template",
            "document_type": "invoice",
            "confidence": 0.94,
            "template_version": "1.0",
            ...
        }

    The class is deliberately provider-independent so that template
    matching can later be upgraded to vector/embedding/layout matching.
    """

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    DEFAULT_TEMPLATE = "generic_template"
    DEFAULT_VERSION = "1.0"

    # Minimum upstream document classification confidence before we
    # consider a specialized template reliable.
    MIN_CLASSIFICATION_CONFIDENCE = 0.45

    # Confidence assigned to the generic fallback.
    GENERIC_TEMPLATE_CONFIDENCE = 0.50

    # Maximum number of alternative templates returned.
    MAX_CANDIDATES = 3

    # ------------------------------------------------------------------
    # Template definitions
    # ------------------------------------------------------------------

    TEMPLATES: Dict[str, TemplateDefinition] = {
        "invoice": TemplateDefinition(
            template="invoice_template",
            document_type="invoice",
            version="1.0",
            description="Structured extraction template for invoices.",
            required_fields=(
                "invoice_number",
                "invoice_date",
                "vendor_name",
                "total_amount",
            ),
            optional_fields=(
                "due_date",
                "purchase_order_number",
                "customer_name",
                "customer_address",
                "vendor_address",
                "subtotal",
                "tax",
                "discount",
                "currency",
                "payment_terms",
                "line_items",
            ),
            aliases=(
                "bill",
                "billing",
                "sales_invoice",
            ),
            priority=1.0,
        ),
        "receipt": TemplateDefinition(
            template="receipt_template",
            document_type="receipt",
            version="1.0",
            description="Structured extraction template for receipts.",
            required_fields=(
                "merchant_name",
                "transaction_date",
                "total_amount",
            ),
            optional_fields=(
                "receipt_number",
                "transaction_id",
                "subtotal",
                "tax",
                "discount",
                "currency",
                "payment_method",
                "amount_tendered",
                "change",
                "line_items",
            ),
            aliases=(
                "purchase_receipt",
                "sales_receipt",
            ),
            priority=1.0,
        ),
        "passport": TemplateDefinition(
            template="passport_template",
            document_type="passport",
            version="1.0",
            description="Structured extraction template for passports.",
            required_fields=(
                "passport_number",
                "full_name",
                "nationality",
                "date_of_birth",
            ),
            optional_fields=(
                "sex",
                "place_of_birth",
                "date_of_issue",
                "date_of_expiry",
                "issuing_country",
                "mrz",
            ),
            aliases=(
                "travel_document",
            ),
            priority=1.0,
        ),
        "resume": TemplateDefinition(
            template="resume_template",
            document_type="resume",
            version="1.0",
            description="Structured extraction template for resumes/CVs.",
            required_fields=(
                "full_name",
            ),
            optional_fields=(
                "email",
                "phone",
                "address",
                "summary",
                "skills",
                "education",
                "experience",
                "projects",
                "certifications",
                "achievements",
                "languages",
                "linkedin",
                "github",
                "portfolio",
            ),
            aliases=(
                "cv",
                "curriculum_vitae",
                "curriculum vitae",
            ),
            priority=1.0,
        ),
        "driving_license": TemplateDefinition(
            template="driving_license_template",
            document_type="driving_license",
            version="1.0",
            description="Structured extraction template for driving licenses.",
            required_fields=(
                "license_number",
                "full_name",
                "date_of_birth",
            ),
            optional_fields=(
                "date_of_issue",
                "date_of_expiry",
                "address",
                "vehicle_class",
                "issuing_authority",
                "nationality",
                "photo",
            ),
            aliases=(
                "drivers_license",
                "driver_license",
                "driving licence",
                "driver licence",
            ),
            priority=1.0,
        ),
        "bank_statement": TemplateDefinition(
            template="bank_statement_template",
            document_type="bank_statement",
            version="1.0",
            description="Structured extraction template for bank statements.",
            required_fields=(
                "account_number",
                "statement_period",
            ),
            optional_fields=(
                "account_holder",
                "bank_name",
                "opening_balance",
                "closing_balance",
                "available_balance",
                "currency",
                "transactions",
                "debit",
                "credit",
                "ifsc",
                "swift",
                "iban",
                "routing_number",
            ),
            aliases=(
                "bank statement",
                "account statement",
                "financial statement",
            ),
            priority=1.0,
        ),
    }

    # ------------------------------------------------------------------
    # Backward-compatible template map
    # ------------------------------------------------------------------

    TEMPLATE_MAP: Dict[str, str] = {
        document_type: definition.template
        for document_type, definition in TEMPLATES.items()
    }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def classify(
        self,
        document_type: str,
        *,
        document_confidence: Optional[float] = None,
        alternatives: Optional[List[Mapping[str, Any]]] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Resolve the best extraction template.

        Parameters
        ----------
        document_type:
            Document type produced by DocumentClassifier.

        document_confidence:
            Optional confidence from DocumentClassifier.

        alternatives:
            Optional alternative document classifications produced by
            DocumentClassifier.

        metadata:
            Optional document metadata reserved for future layout/template
            matching.

        Returns
        -------
        dict
            Template selection result.

        Notes
        -----
        Existing callers can continue doing:

            await classifier.classify("invoice")

        while advanced callers can provide upstream classification
        confidence and alternatives.
        """

        del metadata  # Reserved for future layout-aware matching.

        normalized_type = self._normalize_document_type(document_type)

        # --------------------------------------------------------------
        # Unknown input
        # --------------------------------------------------------------

        if not normalized_type:
            return self._generic_result(
                reason="No document type was provided."
            )

        # --------------------------------------------------------------
        # Generic/unknown classification
        # --------------------------------------------------------------

        if normalized_type in {
            "unknown",
            "generic",
            "other",
            "unclassified",
        }:
            return self._generic_result(
                reason="Document classifier returned an unknown type."
            )

        # --------------------------------------------------------------
        # Resolve aliases
        # --------------------------------------------------------------

        resolved_type = self._resolve_document_type(
            normalized_type
        )

        definition = self.TEMPLATES.get(resolved_type)

        if definition is None:
            return self._generic_result(
                reason=(
                    f"No specialized template is registered for "
                    f"document type '{document_type}'."
                )
            )

        # --------------------------------------------------------------
        # Determine template confidence
        # --------------------------------------------------------------

        confidence = self._calculate_template_confidence(
            definition=definition,
            document_confidence=document_confidence,
        )

        # If the upstream classifier is very uncertain, we should not
        # report the template as highly reliable.
        if (
            document_confidence is not None
            and document_confidence < self.MIN_CLASSIFICATION_CONFIDENCE
        ):
            confidence = min(
                confidence,
                max(document_confidence, 0.0),
            )

        candidates = self._build_candidates(
            resolved_type=resolved_type,
            document_confidence=document_confidence,
            alternatives=alternatives,
        )

        return {
            "template": definition.template,
            "document_type": definition.document_type,
            "confidence": round(confidence, 2),
            "template_version": definition.version,
            "description": definition.description,
            "required_fields": list(
                definition.required_fields
            ),
            "optional_fields": list(
                definition.optional_fields
            ),
            "candidates": candidates,
            "matched_alias": (
                normalized_type != resolved_type
            ),
            "classifier": "template_classifier_v2",
            "fallback": False,
        }

    # ------------------------------------------------------------------
    # Document type normalization
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_document_type(
        document_type: Any,
    ) -> str:
        """
        Normalize document-type input.

        Examples
        --------
        "Bank Statement"
            → "bank_statement"

        "Driver's License"
            → "drivers_license"

        "CV"
            → "cv"
        """

        if document_type is None:
            return ""

        if not isinstance(document_type, str):
            document_type = str(document_type)

        value = document_type.strip().lower()

        if not value:
            return ""

        # Normalize apostrophes and separators.
        value = value.replace("'", "")
        value = value.replace("’", "")

        value = re.sub(
            r"[\s\-]+",
            "_",
            value,
        )

        value = re.sub(
            r"_+",
            "_",
            value,
        )

        return value.strip("_")

    # ------------------------------------------------------------------
    # Alias resolution
    # ------------------------------------------------------------------

    def _resolve_document_type(
        self,
        normalized_type: str,
    ) -> str:
        """
        Resolve canonical document type from aliases.
        """

        if normalized_type in self.TEMPLATES:
            return normalized_type

        for document_type, definition in self.TEMPLATES.items():
            aliases = {
                self._normalize_document_type(alias)
                for alias in definition.aliases
            }

            if normalized_type in aliases:
                return document_type

        return normalized_type

    # ------------------------------------------------------------------
    # Confidence
    # ------------------------------------------------------------------

    @staticmethod
    def _calculate_template_confidence(
        *,
        definition: TemplateDefinition,
        document_confidence: Optional[float],
    ) -> float:
        """
        Calculate confidence that the selected template is appropriate.

        If upstream document classification confidence is available,
        template confidence is derived from it rather than inventing
        an independent confidence value.

        If upstream confidence is unavailable, the value is based on
        deterministic template resolution.
        """

        if document_confidence is None:
            return min(
                0.95 * definition.priority,
                1.0,
            )

        try:
            upstream = float(document_confidence)
        except (TypeError, ValueError):
            upstream = 0.0

        upstream = max(
            0.0,
            min(upstream, 1.0),
        )

        # Template resolution itself is deterministic, so the upstream
        # document confidence is the strongest signal.
        confidence = (
            upstream * 0.90
            + min(definition.priority, 1.0) * 0.10
        )

        return max(
            0.0,
            min(confidence, 1.0),
        )

    # ------------------------------------------------------------------
    # Candidate templates
    # ------------------------------------------------------------------

    def _build_candidates(
        self,
        *,
        resolved_type: str,
        document_confidence: Optional[float],
        alternatives: Optional[List[Mapping[str, Any]]],
    ) -> List[Dict[str, Any]]:
        """
        Build alternative template candidates.

        The upstream DocumentClassifier can provide alternatives such as:

            [
                {
                    "document_type": "receipt",
                    "confidence": 0.21
                }
            ]

        Those are translated into template candidates.
        """

        candidates: List[Dict[str, Any]] = []

        # Primary candidate
        primary_definition = self.TEMPLATES.get(
            resolved_type
        )

        if primary_definition is not None:
            primary_confidence = (
                self._calculate_template_confidence(
                    definition=primary_definition,
                    document_confidence=document_confidence,
                )
            )

            candidates.append(
                {
                    "template": primary_definition.template,
                    "document_type": primary_definition.document_type,
                    "confidence": round(
                        primary_confidence,
                        2,
                    ),
                    "template_version": primary_definition.version,
                }
            )

        # Alternative candidates
        for alternative in alternatives or []:
            alternative_type = alternative.get(
                "document_type"
            )

            if not alternative_type:
                continue

            normalized = self._normalize_document_type(
                alternative_type
            )

            resolved = self._resolve_document_type(
                normalized
            )

            definition = self.TEMPLATES.get(resolved)

            if definition is None:
                continue

            if resolved == resolved_type:
                continue

            raw_confidence = alternative.get(
                "confidence",
                0.0,
            )

            try:
                confidence = float(raw_confidence)
            except (TypeError, ValueError):
                confidence = 0.0

            confidence = max(
                0.0,
                min(confidence, 1.0),
            )

            candidates.append(
                {
                    "template": definition.template,
                    "document_type": definition.document_type,
                    "confidence": round(
                        confidence,
                        2,
                    ),
                    "template_version": definition.version,
                }
            )

            if len(candidates) >= self.MAX_CANDIDATES:
                break

        return candidates[: self.MAX_CANDIDATES]

    # ------------------------------------------------------------------
    # Generic fallback
    # ------------------------------------------------------------------

    def _generic_result(
        self,
        *,
        reason: str,
    ) -> Dict[str, Any]:
        """
        Return a safe generic extraction-template result.
        """

        return {
            "template": self.DEFAULT_TEMPLATE,
            "document_type": "unknown",
            "confidence": self.GENERIC_TEMPLATE_CONFIDENCE,
            "template_version": self.DEFAULT_VERSION,
            "description": (
                "Generic extraction template for unsupported "
                "or uncertain documents."
            ),
            "required_fields": [],
            "optional_fields": [],
            "candidates": [
                {
                    "template": self.DEFAULT_TEMPLATE,
                    "document_type": "unknown",
                    "confidence": self.GENERIC_TEMPLATE_CONFIDENCE,
                    "template_version": self.DEFAULT_VERSION,
                }
            ],
            "matched_alias": False,
            "classifier": "template_classifier_v2",
            "fallback": True,
            "reason": reason,
        }

    # ------------------------------------------------------------------
    # Utility methods
    # ------------------------------------------------------------------

    @classmethod
    def supported_document_types(
        cls,
    ) -> List[str]:
        """
        Return all supported canonical document types.
        """

        return sorted(cls.TEMPLATES.keys())

    @classmethod
    def get_template_definition(
        cls,
        document_type: str,
    ) -> Optional[TemplateDefinition]:
        """
        Return the template definition for a document type.
        """

        normalized = cls._normalize_document_type(
            document_type
        )

        resolved = cls()._resolve_document_type(
            normalized
        )

        return cls.TEMPLATES.get(resolved)


__all__ = [
    "TemplateClassifier",
    "TemplateDefinition",
]