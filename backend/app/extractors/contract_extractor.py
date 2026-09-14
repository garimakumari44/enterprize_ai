from __future__ import annotations

import re
from typing import Any

from app.db.models.processing.extracted_field import ExtractedField
from app.db.models.processing.extraction_result import ExtractionResult

from .base import BaseExtractor


class ContractExtractor(BaseExtractor):
    """
    Extract structured information from contracts.
    """

    supported_document_type = "contract"

    async def extract(
        self,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> ExtractionResult:

        fields: list[ExtractedField] = []

        patterns = {
            "effective_date": r"Effective Date[:\s]+([^\n]+)",
            "termination_date": r"(?:Termination|End)\sDate[:\s]+([^\n]+)",
            "contract_number": r"Contract\s*(?:No|Number)?[:#]?\s*([A-Za-z0-9\-]+)",
            "governing_law": r"Governing Law[:\s]+([^\n]+)",
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