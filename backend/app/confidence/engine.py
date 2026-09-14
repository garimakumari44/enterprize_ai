from __future__ import annotations

from .document_confidence import (
    DocumentConfidence,
    DocumentConfidenceCalculator,
)
from .field_confidence import (
    FieldConfidence,
    FieldConfidenceCalculator,
)
from .page_confidence import (
    PageConfidence,
    PageConfidenceCalculator,
)


class ConfidenceEngine:
    """
    Central orchestration engine for confidence computation.

    The engine coordinates the three confidence levels:

        Field confidence
            ↓
        Page confidence
            ↓
        Document confidence

    Field confidence combines:
        - OCR confidence
        - Extraction confidence
        - Validation confidence

    Page confidence aggregates field confidence.

    Document confidence aggregates page confidence.

    The engine itself contains no confidence formulas. Those
    responsibilities remain inside the dedicated calculators.
    """

    def __init__(self) -> None:
        """
        Initialize all confidence calculators.
        """

        self.field_calculator = FieldConfidenceCalculator()
        self.page_calculator = PageConfidenceCalculator()
        self.document_calculator = DocumentConfidenceCalculator()

    def calculate_field(
        self,
        field_name: str,
        ocr_score: float,
        extraction_score: float,
        validation_score: float,
    ) -> FieldConfidence:
        """
        Calculate confidence for a single extracted field.

        Parameters
        ----------
        field_name:
            Name of the extracted field.

        ocr_score:
            Confidence returned by the OCR stage.

        extraction_score:
            Confidence that the extraction logic identified the
            correct value.

        validation_score:
            Confidence returned by validation/business-rule checks.

        Returns
        -------
        FieldConfidence
            Confidence result for the field.
        """

        score = self.field_calculator.calculate(
            ocr_score=ocr_score,
            extraction_score=extraction_score,
            validation_score=validation_score,
        )

        return FieldConfidence(
            field_name=field_name,
            score=score,
        )

    def calculate_page(
        self,
        page_number: int,
        fields: list[FieldConfidence],
    ) -> PageConfidence:
        """
        Calculate confidence for a document page.

        Parameters
        ----------
        page_number:
            One-based page number.

        fields:
            Field confidence results belonging to the page.

        Returns
        -------
        PageConfidence
            Aggregated confidence for the page.
        """

        return self.page_calculator.calculate(
            page_number=page_number,
            fields=fields,
        )

    def calculate_document(
        self,
        pages: list[PageConfidence],
    ) -> DocumentConfidence:
        """
        Calculate confidence for the entire document.

        Parameters
        ----------
        pages:
            Page confidence results for the document.

        Returns
        -------
        DocumentConfidence
            Aggregated document confidence.
        """

        return self.document_calculator.calculate(
            pages=pages,
        )