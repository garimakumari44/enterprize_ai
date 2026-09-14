from __future__ import annotations

import re
from typing import Any

from app.models.processing.extracted_field import ExtractedField
from app.models.processing.extraction_result import ExtractionResult

from .base import BaseExtractor


class PurchaseOrderExtractor(BaseExtractor):
    """
    Extract Purchase Order fields.
    """

    supported_document_type = "purchase_order"

    async def extract(
        self,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> ExtractionResult:

        fields: list[ExtractedField] = []

        patterns = {
            "purchase_order_number": r"(?:PO|Purchase Order)\s*(?:No|Number)?[:#]?\s*([A-Za-z0-9\-]+)",
            "vendor": r"Vendor[:\s]+([^\n]+)",
            "total_amount": r"Total[:$]?\s*([\d,]+\.\d{2}|\d+)",
        }

        for field_name, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                fields.append(
                    ExtractedField(
                        field_name=field_name,
                        value=match.group(1).strip(),
                        confidence=0.95,
                    )
                )

        return ExtractionResult(
            document_type=self.supported_document_type,
            fields=fields,
            raw_text=text,
        )