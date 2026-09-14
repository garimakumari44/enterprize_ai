from __future__ import annotations

import re
from typing import Any

from app.models.processing.extracted_field import ExtractedField
from app.models.processing.extraction_result import ExtractionResult

from .base import BaseExtractor


class ReceiptExtractor(BaseExtractor):

    supported_document_type = "receipt"

    async def extract(
        self,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> ExtractionResult:

        fields: list[ExtractedField] = []

        total = re.search(
            r"Total\s*[:$]?\s*([\d,.]+)",
            text,
            re.IGNORECASE,
        )

        tax = re.search(
            r"Tax\s*[:$]?\s*([\d,.]+)",
            text,
            re.IGNORECASE,
        )

        if total:
            fields.append(
                ExtractedField(
                    field_name="total_amount",
                    value=total.group(1),
                    confidence=0.95,
                )
            )

        if tax:
            fields.append(
                ExtractedField(
                    field_name="tax_amount",
                    value=tax.group(1),
                    confidence=0.92,
                )
            )

        return ExtractionResult(
            document_type=self.supported_document_type,
            fields=fields,
            raw_text=text,
        )