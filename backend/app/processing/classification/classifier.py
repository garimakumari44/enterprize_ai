
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ProcessingStage
from app.processing.pipeline.context import ProcessingContext
from app.processing.pipeline.pipeline import DocumentProcessingStage


class ClassificationStage(DocumentProcessingStage):
    """
    Classify a document into a high-level document type.

    The current implementation uses deterministic, lightweight
    heuristic classification based on:

    - filename
    - MIME type
    - extracted/raw text

    The stage is intentionally persistence-independent. An optional
    job-scoped AsyncSession is accepted to satisfy the common
    DocumentProcessingStage contract and to allow future database-backed
    classification without changing the pipeline interface.
    """

    @property
    def name(self) -> str:
        """Return the canonical processing-stage name."""
        return ProcessingStage.CLASSIFICATION.value

    async def process(
        self,
        data: ProcessingContext,
        *,
        session: AsyncSession | None = None,
    ) -> ProcessingContext:
        """
        Classify the current document and update the processing context.

        Args:
            data: Current document-processing context.
            session: Optional job-scoped database session. Currently unused.

        Returns:
            The updated ProcessingContext.
        """
        # Accepted for compatibility with the common stage contract.
        _ = session

        filename = (data.file_name or "").strip()
        mime_type = (data.mime_type or "").strip().lower()
        text = (data.raw_text or "").strip()

        document_type, confidence = self._classify(
            filename=filename,
            mime_type=mime_type,
            text=text,
        )

        data.document_type = document_type
        data.classification_confidence = confidence

        data.set_metadata(
            "classification",
            {
                "document_type": document_type,
                "confidence": confidence,
            },
        )

        return data

    @staticmethod
    def _classify(
        *,
        filename: str,
        mime_type: str,
        text: str,
    ) -> tuple[str, float]:
        """
        Determine the document type using deterministic heuristics.

        Classification priority is intentional. More specific document
        indicators are evaluated before generic MIME-type fallbacks.

        Returns:
            A tuple of (document_type, confidence).
        """
        normalized_filename = filename.lower()
        normalized_text = text[:5000].lower()

        searchable_value = (
            f"{normalized_filename} "
            f"{mime_type} "
            f"{normalized_text}"
        )

        # Financial / business documents
        if "invoice" in searchable_value:
            return "invoice", 0.90

        if (
            "balance sheet" in searchable_value
            or "income statement" in searchable_value
        ):
            return "financial_report", 0.85

        if (
            "annual report" in searchable_value
            or "annual_report" in normalized_filename
        ):
            return "annual_report", 0.85

        # Legal documents
        if (
            "contract" in searchable_value
            or "agreement" in searchable_value
        ):
            return "contract", 0.85

        # Professional documents
        if (
            "resume" in searchable_value
            or "curriculum vitae" in searchable_value
            or " cv " in f" {searchable_value} "
        ):
            return "resume", 0.90

        # Academic / research documents
        if (
            "research paper" in searchable_value
            or "abstract" in searchable_value
        ):
            return "research_paper", 0.80

        # MIME-based fallbacks
        if mime_type.startswith("image/"):
            return "image_document", 0.70

        if mime_type == "application/pdf":
            return "pdf_document", 0.60

        return "unknown", 0.25


__all__ = [
    "ClassificationStage",
]
