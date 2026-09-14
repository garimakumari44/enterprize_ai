from __future__ import annotations

import re
from typing import Any

from app.db.models.extracted_field import ExtractedField
from app.db.models.extraction_result import ExtractionResult

from .base import BaseExtractor


class InvoiceExtractor(BaseExtractor):

    supported_document_type = "invoice"

    async def extract(
        self,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> ExtractionResult:

        fields: list[ExtractedField] = []

        invoice_number = re.search(
            r"Invoice\s*(?:No|Number)?[:#]?\s*([A-Za-z0-9\-]+)",
            text,
            re.IGNORECASE,
        )

        total = re.search(
            r"Total\s*[:$]?\s*([\d,.]+)",
            text,
            re.IGNORECASE,
        )

        if invoice_number:
            fields.append(
                ExtractedField(
                    field_name="invoice_number",
                    value=invoice_number.group(1),
                    confidence=0.97,
                )
            )

        if total:
            fields.append(
                ExtractedField(
                    field_name="total_amount",
                    value=total.group(1),
                    confidence=0.95,
                )
            )

        return ExtractionResult(
            document_type=self.supported_document_type,
            fields=fields,
            raw_text=text,
        )