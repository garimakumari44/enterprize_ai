
from __future__ import annotations

import re
from typing import Any

from app.db.models.extracted_field import ExtractedField
from app.db.models.extraction_result import ExtractionResult

from .base import BaseExtractor


class EntityExtractor(BaseExtractor):
    """
    Generic entity extractor.

    Extracts common entities from document text using deterministic
    regular-expression based rules.

    Supported entities
    ------------------
    - Email addresses
    - Phone numbers
    - Dates

    This extractor is intentionally provider-independent and can be
    reused by specialized document extractors.
    """

    supported_document_type = "generic"

    # ------------------------------------------------------------------
    # Entity patterns
    # ------------------------------------------------------------------

    EMAIL_PATTERN = re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    )

    PHONE_PATTERN = re.compile(
        r"(?<!\w)"
        r"\+?\d(?:[\d\s().-]{7,18}\d)"
        r"(?!\w)"
    )

    DATE_PATTERN = re.compile(
        r"\b"
        r"(?:"
        r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"
        r"|"
        r"\d{4}[/-]\d{1,2}[/-]\d{1,2}"
        r")"
        r"\b"
    )

    # ------------------------------------------------------------------
    # Extraction
    # ------------------------------------------------------------------

    async def extract(
        self,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> ExtractionResult:
        """
        Extract generic entities from document text.

        Parameters
        ----------
        text:
            Text extracted from the document.

        metadata:
            Optional document metadata. Currently not required by the
            deterministic extraction rules, but accepted for interface
            compatibility with the processing pipeline.

        Returns
        -------
        ExtractionResult
            Structured extraction result containing extracted fields
            and the original raw text.
        """

        # Always normalize None/invalid input into a safe string.
        if not isinstance(text, str):
            text = str(text or "")

        fields: list[ExtractedField] = []

        if not text.strip():
            return ExtractionResult(
                document_type=self.supported_document_type,
                fields=fields,
                raw_text=text,
            )

        # --------------------------------------------------------------
        # Email extraction
        # --------------------------------------------------------------

        emails = self._unique_matches(
            self.EMAIL_PATTERN,
            text,
            normalize=lambda value: value.strip(),
        )

        for email in emails:
            fields.append(
                ExtractedField(
                    field_name="email",
                    value=email,
                    confidence=0.98,
                )
            )

        # --------------------------------------------------------------
        # Phone extraction
        # --------------------------------------------------------------

        phones = self._unique_matches(
            self.PHONE_PATTERN,
            text,
            normalize=self._normalize_phone,
        )

        for phone in phones:
            # Avoid accepting extremely short numeric fragments.
            digits = re.sub(r"\D", "", phone)

            if len(digits) < 9:
                continue

            fields.append(
                ExtractedField(
                    field_name="phone",
                    value=phone,
                    confidence=0.95,
                )
            )

        # --------------------------------------------------------------
        # Date extraction
        # --------------------------------------------------------------

        dates = self._unique_matches(
            self.DATE_PATTERN,
            text,
            normalize=lambda value: value.strip(),
        )

        for date in dates:
            fields.append(
                ExtractedField(
                    field_name="date",
                    value=date,
                    confidence=0.90,
                )
            )

        return ExtractionResult(
            document_type=self.supported_document_type,
            fields=fields,
            raw_text=text,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _unique_matches(
        pattern: re.Pattern[str],
        text: str,
        normalize: Any,
    ) -> list[str]:
        """
        Return normalized unique regex matches while preserving order.
        """

        results: list[str] = []
        seen: set[str] = set()

        for match in pattern.finditer(text):
            value = normalize(match.group(0))

            if not value:
                continue

            # Case-insensitive deduplication is useful for emails.
            key = value.casefold()

            if key in seen:
                continue

            seen.add(key)
            results.append(value)

        return results

    @staticmethod
    def _normalize_phone(value: str) -> str:
        """
        Normalize whitespace around phone numbers without destroying
        the original human-readable formatting.
        """

        value = value.strip()

        # Collapse repeated whitespace.
        value = re.sub(r"\s+", " ", value)

        # Remove whitespace directly inside common separators.
        value = re.sub(r"\s*-\s*", "-", value)
        value = re.sub(r"\(\s+", "(", value)
        value = re.sub(r"\s+\)", ")", value)

        return value

