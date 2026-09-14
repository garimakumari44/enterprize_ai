from __future__ import annotations

import re
from typing import Any

from app.models.processing.extracted_field import ExtractedField
from app.models.processing.extraction_result import ExtractionResult

from .base import BaseExtractor


class BankStatementExtractor(BaseExtractor):
    """
    Extract structured data from bank statements.
    """

    supported_document_type = "bank_statement"

    async def extract(
        self,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> ExtractionResult:

        fields: list[ExtractedField] = []

        patterns = {
            "account_number": r"Account\s*(?:No|Number)?[:#]?\s*([A-Za-z0-9\-*]+)",
            "statement_period": r"Statement\s*Period[:\s]+([^\n]+)",
            "opening_balance": r"Opening\s*Balance[:$]?\s*([\d,]+\.\d{2}|\d+)",
            "closing_balance": r"Closing\s*Balance[:$]?\s*([\d,]+\.\d{2}|\d+)",
        }

        for field_name, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                fields.append(
                    ExtractedField(
                        field_name=field_name,
                        value=match.group(1).strip(),
                        confidence=0.96,
                    )
                )

        return ExtractionResult(
            document_type=self.supported_document_type,
            fields=fields,
            raw_text=text,
        )