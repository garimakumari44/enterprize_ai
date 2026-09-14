"""
app/services/processing/document_intelligence_service.py

Persists business-level Document Intelligence results.

ProcessingJob:
    Tracks execution state.

DocumentIntelligenceResult:
    Stores the actual intelligence extracted from the document.
"""

from __future__ import annotations

import uuid
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.document_intelligence_result import (
    DocumentIntelligenceResult,
)


class DocumentIntelligenceService:
    """
    Converts processing pipeline output into a persisted
    DocumentIntelligenceResult.
    """

    def __init__(
        self,
        db: AsyncSession,
    ) -> None:
        self.db = db

    # ==================================================================
    # CREATE / UPDATE
    # ==================================================================

    async def create_result(
        self,
        processing_id: uuid.UUID,
        document_id: uuid.UUID,
        document_version_id: uuid.UUID,
        processing_output: dict[str, Any] | None = None,
    ) -> DocumentIntelligenceResult:
        """
        Create or update the intelligence result for a processing job.
        """

        processing_output = processing_output or {}

        existing_result = await self._get_existing_result(
            processing_id=processing_id,
        )

        document_type = self._resolve_document_type(
            processing_output,
        )

        confidence = self._resolve_confidence(
            processing_output,
        )

        structured_data = self._build_structured_data(
            processing_output,
        )

        validation_results = self._build_validation_results(
            structured_data,
        )

        artifacts = self._build_artifacts(
            processing_output,
        )

        knowledge = self._build_knowledge(
            processing_output,
        )

        raw_text = self._resolve_raw_text(
            processing_output,
        )

        # --------------------------------------------------------------
        # Update existing result
        # --------------------------------------------------------------

        if existing_result is not None:

            existing_result.document_id = document_id
            existing_result.document_version_id = (
                document_version_id
            )
            existing_result.document_type = document_type
            existing_result.confidence = confidence
            existing_result.structured_data = structured_data
            existing_result.validation_results = (
                validation_results
            )
            existing_result.artifacts = artifacts
            existing_result.knowledge = knowledge
            existing_result.raw_text = raw_text

            await self.db.flush()

            return existing_result

        # --------------------------------------------------------------
        # Create new result
        # --------------------------------------------------------------

        result = DocumentIntelligenceResult(
            processing_id=processing_id,
            document_id=document_id,
            document_version_id=document_version_id,
            document_type=document_type,
            confidence=confidence,
            structured_data=structured_data,
            validation_results=validation_results,
            artifacts=artifacts,
            knowledge=knowledge,
            raw_text=raw_text,
        )

        self.db.add(result)

        await self.db.flush()

        return result

    # ==================================================================
    # GET
    # ==================================================================

    async def get_result(
        self,
        processing_id: uuid.UUID,
    ) -> DocumentIntelligenceResult | None:
        """
        Retrieve the persisted intelligence result.
        """

        return await self._get_existing_result(
            processing_id=processing_id,
        )

    async def _get_existing_result(
        self,
        processing_id: uuid.UUID,
    ) -> DocumentIntelligenceResult | None:

        result = await self.db.execute(
            select(DocumentIntelligenceResult)
            .where(
                DocumentIntelligenceResult.processing_id
                == processing_id
            )
        )

        return result.scalar_one_or_none()

    # ==================================================================
    # DOCUMENT TYPE
    # ==================================================================

    def _resolve_document_type(
        self,
        output: dict[str, Any],
    ) -> str | None:

        classification = output.get("classification")

        if isinstance(classification, dict):

            document_type = classification.get(
                "document_type",
            )

            if document_type:
                return str(document_type)

            label = classification.get("label")

            if label:
                return str(label)

            document_type = classification.get(
                "type",
            )

            if document_type:
                return str(document_type)

        document_type = output.get(
            "document_type",
        )

        if document_type:
            return str(document_type)

        return None

    # ==================================================================
    # CONFIDENCE
    # ==================================================================

    def _resolve_confidence(
        self,
        output: dict[str, Any],
    ) -> float | None:

        classification = output.get(
            "classification",
        )

        if isinstance(classification, dict):

            confidence = classification.get(
                "confidence",
            )

            if confidence is not None:

                try:
                    return float(confidence)

                except (
                    TypeError,
                    ValueError,
                ):
                    pass

        confidence = output.get(
            "confidence",
        )

        if confidence is not None:

            try:
                return float(confidence)

            except (
                TypeError,
                ValueError,
            ):
                pass

        return None

    # ==================================================================
    # STRUCTURED DATA
    # ==================================================================

    def _build_structured_data(
        self,
        output: dict[str, Any],
    ) -> dict[str, Any]:

        structured_data = output.get(
            "structured_data",
        )

        if isinstance(
            structured_data,
            dict,
        ):
            return structured_data

        invoice = output.get(
            "invoice",
        )

        if isinstance(
            invoice,
            dict,
        ):
            return {
                "invoice": invoice,
            }

        extraction = output.get(
            "extraction",
        )

        if isinstance(
            extraction,
            dict,
        ):
            return extraction

        metadata = output.get(
            "metadata",
        )

        if isinstance(
            metadata,
            dict,
        ):
            return {
                "metadata": metadata,
            }

        structure = output.get(
            "structure",
        )

        if isinstance(
            structure,
            dict,
        ):
            return {
                "structure": structure,
            }

        return {}

    # ==================================================================
    # VALIDATION
    # ==================================================================

    def _build_validation_results(
        self,
        structured_data: dict[str, Any],
    ) -> dict[str, Any]:

        invoice = structured_data.get(
            "invoice",
        )

        if not isinstance(
            invoice,
            dict,
        ):
            return {
                "valid": True,
                "checks": {},
                "errors": [],
                "warnings": [],
            }

        financials = invoice.get(
            "financials",
        )

        if not isinstance(
            financials,
            dict,
        ):
            return {
                "valid": True,
                "checks": {},
                "errors": [],
                "warnings": [],
            }

        subtotal = self._decimal(
            financials.get("subtotal"),
        )

        tax_amount = self._decimal(
            financials.get("tax_amount")
            or financials.get("tax"),
        )

        total = self._decimal(
            financials.get("total"),
        )

        tax_rate = self._decimal(
            financials.get("tax_rate"),
        )

        checks: dict[str, Any] = {}

        errors: list[str] = []

        warnings: list[str] = []

        # --------------------------------------------------------------
        # Tax calculation
        # --------------------------------------------------------------

        if (
            subtotal is not None
            and tax_amount is not None
            and tax_rate is not None
        ):

            expected_tax = (
                subtotal
                * tax_rate
                / Decimal("100")
            )

            tax_valid = (
                abs(
                    expected_tax
                    - tax_amount
                )
                <= Decimal("0.01")
            )

            checks["tax_calculation"] = (
                tax_valid
            )

            if not tax_valid:

                errors.append(
                    "Tax amount does not match "
                    "the stated tax rate."
                )

        # --------------------------------------------------------------
        # Total calculation
        # --------------------------------------------------------------

        if (
            subtotal is not None
            and tax_amount is not None
            and total is not None
        ):

            expected_total = (
                subtotal
                + tax_amount
            )

            total_valid = (
                abs(
                    expected_total
                    - total
                )
                <= Decimal("0.01")
            )

            checks["total_calculation"] = (
                total_valid
            )

            if not total_valid:

                errors.append(
                    "Invoice total does not match "
                    "subtotal plus tax."
                )

        return {
            "valid": len(errors) == 0,
            "checks": checks,
            "errors": errors,
            "warnings": warnings,
        }

    # ==================================================================
    # ARTIFACTS
    # ==================================================================

    def _build_artifacts(
        self,
        output: dict[str, Any],
    ) -> list[dict[str, Any]]:

        artifacts = output.get(
            "artifacts",
        )

        if isinstance(
            artifacts,
            list,
        ):
            return artifacts

        generated: list[dict[str, Any]] = []

        if output.get(
            "raw_text",
        ):

            generated.append(
                {
                    "id": "raw-text",
                    "type": "extracted_text",
                    "status": "available",
                    "metadata": {},
                }
            )

        if output.get(
            "chunks",
        ):

            generated.append(
                {
                    "id": "chunks",
                    "type": "chunks",
                    "status": "available",
                    "metadata": {},
                }
            )

        if output.get(
            "embeddings",
        ):

            generated.append(
                {
                    "id": "embeddings",
                    "type": "embeddings",
                    "status": "available",
                    "metadata": {},
                }
            )

        return generated

    # ==================================================================
    # KNOWLEDGE
    # ==================================================================

    def _build_knowledge(
        self,
        output: dict[str, Any],
    ) -> dict[str, Any]:

        knowledge = output.get(
            "knowledge",
        )

        if isinstance(
            knowledge,
            dict,
        ):
            return knowledge

        indexing = output.get(
            "indexing",
        )

        if isinstance(
            indexing,
            dict,
        ):

            return {
                "indexed": bool(
                    indexing.get(
                        "indexed",
                        False,
                    )
                    or indexing.get(
                        "status",
                    )
                    == "completed"
                ),
                "index_id": indexing.get(
                    "index_id",
                ),
                "chunk_count": output.get(
                    "chunk_count",
                ),
                "embedding_count": output.get(
                    "embedding_count",
                ),
            }

        return {
            "indexed": False,
            "index_id": None,
            "chunk_count": None,
            "embedding_count": None,
        }

    # ==================================================================
    # RAW TEXT
    # ==================================================================

    def _resolve_raw_text(
        self,
        output: dict[str, Any],
    ) -> str | None:

        raw_text = output.get(
            "raw_text",
        )

        if isinstance(
            raw_text,
            str,
        ):
            return raw_text

        text = output.get(
            "text",
        )

        if isinstance(
            text,
            str,
        ):
            return text

        extraction = output.get(
            "text_extraction",
        )

        if isinstance(
            extraction,
            dict,
        ):

            extracted_text = extraction.get(
                "text",
            )

            if isinstance(
                extracted_text,
                str,
            ):
                return extracted_text

        return None

    # ==================================================================
    # DECIMAL
    # ==================================================================

    @staticmethod
    def _decimal(
        value: Any,
    ) -> Decimal | None:

        if value is None:
            return None

        try:
            return Decimal(
                str(value),
            )

        except (
            InvalidOperation,
            ValueError,
        ):
            return None


__all__ = [
    "DocumentIntelligenceService",
]