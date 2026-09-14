from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.db.models.extraction_result import ExtractionResult
from app.db.models.extracted_field import ExtractedField
from app.repositories.processing.extraction_repository import (
    ExtractionRepository,
)


class ExtractionService:
    """
    Handles extracted data produced by OCR / AI.
    """

    def __init__(self, db: Session):
        self.db = db
        self.repository = ExtractionRepository(db)

    def create_result(
        self,
        *,
        processing_job_id: uuid.UUID,
        raw_text: str,
    ) -> ExtractionResult:

        result = ExtractionResult(
            processing_job_id=processing_job_id,
            raw_text=raw_text,
        )

        return self.repository.create_result(result)

    def add_field(
        self,
        *,
        extraction_result_id: uuid.UUID,
        name: str,
        value: str,
        confidence: float | None = None,
    ) -> ExtractedField:

        field = ExtractedField(
            extraction_result_id=extraction_result_id,
            field_name=name,
            field_value=value,
            confidence=confidence,
        )

        return self.repository.create_field(field)

    def get_result(self, result_id: uuid.UUID):
        return self.repository.get_result(result_id)

    def list_fields(self, result_id: uuid.UUID):
        return self.repository.list_fields(result_id)

    def delete_result(self, result_id: uuid.UUID):
        return self.repository.delete_result(result_id)