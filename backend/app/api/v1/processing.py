"""
app/api/v1/processing/api.py

Canonical Document Processing API.

This module is the single public API boundary for document processing.

Public API
----------

    /api/v1/processing
        POST   /jobs
        GET    /jobs/{processing_id}
        POST   /jobs/{processing_id}/cancel
        GET    /jobs/{processing_id}/result
        POST   /jobs/{processing_id}/review
        POST   /jobs/{processing_id}/review/approve
        POST   /jobs/{processing_id}/review/reject

The API intentionally aggregates:

    - processing job state
    - pipeline stages
    - extraction
    - validation
    - document intelligence
    - human review

Business logic remains in services.

The API layer is responsible only for:
    - HTTP
    - request validation
    - response schemas
    - aggregation
    - error translation
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_storage_service
from app.db.models.document_intelligence_result import (
    DocumentIntelligenceResult,
)
from app.db.models.extracted_field import ExtractedField
from app.db.models.extraction_result import ExtractionResult
from app.db.models.processing_job import ProcessingJob
from app.db.session import get_async_db
from app.execution.queue.broker import Broker
from app.services.processing.processing_service import ProcessingService
from app.services.processing.review_service import ReviewService
from app.services.processing.validation_service import ValidationService
from app.storage.service import StorageService


logger = logging.getLogger(__name__)


# ============================================================================
# ROUTER
# ============================================================================

router = APIRouter(
    prefix="/processing",
    tags=["Document Processing"],
)


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================


class ProcessingRequest(BaseModel):
    """Start a document processing job."""

    document_id: UUID

    force: bool = Field(
        default=False,
        description="Force creation of a new processing job.",
    )


class ReviewCorrection(BaseModel):
    """One human correction."""

    field: str = Field(
        ...,
        min_length=1,
    )

    value: Any = None

    reason: str | None = None


class ReviewSubmission(BaseModel):
    """Human review submission."""

    decision: str = Field(
        ...,
        description="approve, reject, or needs_changes.",
    )

    comments: str | None = None

    corrections: list[ReviewCorrection] = Field(
        default_factory=list,
    )


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================


class ProcessingStepResponse(BaseModel):
    """One processing pipeline stage."""

    name: str

    step_order: int

    status: str

    provider: str | None = None

    provider_operation: str | None = None

    attempt_count: int = 0

    duration_ms: int | None = None

    error_code: str | None = None

    error_message: str | None = None

    created_at: datetime | None = None

    started_at: datetime | None = None

    completed_at: datetime | None = None


class ExtractedFieldResponse(BaseModel):
    """One extracted field."""

    id: UUID

    field_name: str

    value: Any = None

    normalized_value: Any = None

    confidence: float | None = Field(
        default=None,
        ge=0,
        le=1,
    )

    source: str | None = None

    page_number: int | None = None

    bounding_box: dict[str, Any] | None = None

    created_at: datetime | None = None

    updated_at: datetime | None = None


class ExtractionResponse(BaseModel):
    """Aggregated extraction result."""

    id: UUID

    processing_id: UUID

    document_id: UUID

    document_version_id: UUID

    document_type: str

    overall_confidence: float

    status: str

    raw_text: str | None = None

    structured_data: dict[str, Any] = Field(
        default_factory=dict,
    )

    validation_status: str

    extraction_method: str | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

    fields: list[ExtractedFieldResponse] = Field(
        default_factory=list,
    )

    created_at: datetime | None = None

    updated_at: datetime | None = None


class ValidationIssueResponse(BaseModel):
    """One validation issue."""

    rule: str | None = None

    code: str | None = None

    message: str

    severity: str = "error"

    field: str | None = None

    value: Any = None


class ValidationResponse(BaseModel):
    """Aggregated validation result."""

    processing_id: UUID

    status: str

    passed: bool

    score: float | None = Field(
        default=None,
        ge=0,
        le=1,
    )

    issues: list[ValidationIssueResponse] = Field(
        default_factory=list,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

    created_at: datetime | None = None

    completed_at: datetime | None = None


class IntelligenceResponse(BaseModel):
    """Aggregated document intelligence result."""

    processing_id: UUID

    document_id: UUID

    document_version_id: UUID

    document_type: str | None = None

    status: str

    confidence: float | None = Field(
        default=None,
        ge=0,
        le=1,
    )

    structured_data: dict[str, Any] = Field(
        default_factory=dict,
    )

    validation_results: dict[str, Any] = Field(
        default_factory=dict,
    )

    artifacts: list[dict[str, Any]] = Field(
        default_factory=list,
    )

    knowledge: dict[str, Any] = Field(
        default_factory=dict,
    )

    raw_text: str | None = None

    validation_status: str | None = None

    created_at: datetime | None = None

    updated_at: datetime | None = None

    completed_at: datetime | None = None


class ReviewResponse(BaseModel):
    """Aggregated human review state."""

    processing_id: UUID

    status: str

    decision: str | None = None

    reviewer_id: UUID | None = None

    comments: str | None = None

    corrections: list[ReviewCorrection] = Field(
        default_factory=list,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

    created_at: datetime | None = None

    updated_at: datetime | None = None


class ProcessingResponse(BaseModel):
    """Response after creating a processing job."""

    processing_id: UUID

    document_id: UUID

    document_version_id: UUID

    status: str

    message: str


class ProcessingAggregateResponse(BaseModel):
    """
    Canonical processing response.

    This is the main response consumed by the frontend.

    It contains the complete state of a processing execution.
    """

    processing_id: UUID

    document_id: UUID

    document_version_id: UUID

    status: str

    current_stage: str | None = None

    progress: int = Field(
        default=0,
        ge=0,
        le=100,
    )

    error: str | None = None

    steps: list[ProcessingStepResponse] = Field(
        default_factory=list,
    )

    extraction: ExtractionResponse | None = None

    validation: ValidationResponse | None = None

    intelligence: IntelligenceResponse | None = None

    review: ReviewResponse | None = None

    completed_at: datetime | None = None


# ============================================================================
# DEPENDENCIES
# ============================================================================


def get_processing_service(
    db: AsyncSession = Depends(get_async_db),
    storage_service: StorageService = Depends(get_storage_service),
) -> ProcessingService:
    """Build a lightweight ProcessingService for job creation."""

    return ProcessingService(
        db=db,
        storage_service=storage_service,
    )


def get_validation_service(
    db: AsyncSession = Depends(get_async_db),
) -> ValidationService:
    """Build ValidationService."""

    return ValidationService(
        db=db,
    )


def get_review_service(
    db: AsyncSession = Depends(get_async_db),
) -> ReviewService:
    """Build ReviewService."""

    return ReviewService(
        db=db,
    )


# ============================================================================
# NORMALIZATION
# ============================================================================


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)

    return {}


def _as_list_of_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []

    return [
        dict(item)
        for item in value
        if isinstance(item, dict)
    ]


def _normalize_status(
    value: Any,
    default: str = "unknown",
) -> str:

    if value is None:
        return default

    value = getattr(
        value,
        "value",
        value,
    )

    normalized = (
        str(value)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )

    return normalized or default


def _normalize_confidence(
    value: Any,
) -> float | None:

    if value is None:
        return None

    try:
        value = float(value)
    except (TypeError, ValueError):
        return None

    return max(
        0.0,
        min(
            value,
            1.0,
        ),
    )


def _build_step_response(
    step: Any,
) -> ProcessingStepResponse:

    return ProcessingStepResponse(
        name=step.name,
        step_order=step.step_order,
        status=_normalize_status(step.status),
        provider=getattr(
            step,
            "provider",
            None,
        ),
        provider_operation=getattr(
            step,
            "provider_operation",
            None,
        ),
        attempt_count=getattr(
            step,
            "attempt_count",
            0,
        ),
        duration_ms=getattr(
            step,
            "duration_ms",
            None,
        ),
        error_code=getattr(
            step,
            "error_code",
            None,
        ),
        error_message=getattr(
            step,
            "error_message",
            None,
        ),
        created_at=getattr(
            step,
            "created_at",
            None,
        ),
        started_at=getattr(
            step,
            "started_at",
            None,
        ),
        completed_at=getattr(
            step,
            "completed_at",
            None,
        ),
    )


def _build_field_response(
    field: ExtractedField,
) -> ExtractedFieldResponse:

    return ExtractedFieldResponse(
        id=field.id,
        field_name=field.field_name,
        value=getattr(
            field,
            "value",
            None,
        ),
        normalized_value=getattr(
            field,
            "normalized_value",
            None,
        ),
        confidence=_normalize_confidence(
            getattr(
                field,
                "confidence",
                None,
            )
        ),
        source=getattr(
            field,
            "source",
            None,
        ),
        page_number=getattr(
            field,
            "page_number",
            None,
        ),
        bounding_box=getattr(
            field,
            "bounding_box",
            None,
        ),
        created_at=getattr(
            field,
            "created_at",
            None,
        ),
        updated_at=getattr(
            field,
            "updated_at",
            None,
        ),
    )


# ============================================================================
# EXTRACTION
# ============================================================================


async def _load_extraction(
    db: AsyncSession,
    processing_id: UUID,
) -> ExtractionResponse | None:

    result = await db.execute(
        select(ExtractionResult)
        .where(
            ExtractionResult.processing_id
            == processing_id,
        )
        .order_by(
            ExtractionResult.created_at.desc(),
        )
        .limit(1)
    )

    extraction = result.scalar_one_or_none()

    if extraction is None:
        return None

    fields_result = await db.execute(
        select(ExtractedField)
        .where(
            ExtractedField.extraction_result_id
            == extraction.id,
        )
        .order_by(
            ExtractedField.created_at.asc(),
        )
    )

    fields = list(
        fields_result.scalars().all()
    )

    document_type = getattr(
        extraction,
        "document_type",
        None,
    )

    document_type = (
        str(document_type).strip()
        if document_type is not None
        else "unknown"
    )

    return ExtractionResponse(
        id=extraction.id,
        processing_id=extraction.processing_id,
        document_id=extraction.document_id,
        document_version_id=extraction.document_version_id,
        document_type=document_type or "unknown",
        overall_confidence=(
            _normalize_confidence(
                getattr(
                    extraction,
                    "overall_confidence",
                    0.0,
                )
            )
            or 0.0
        ),
        status=_normalize_status(
            getattr(
                extraction,
                "status",
                None,
            ),
            default="completed",
        ),
        raw_text=getattr(
            extraction,
            "raw_text",
            None,
        ),
        structured_data=_as_dict(
            getattr(
                extraction,
                "structured_data",
                None,
            )
        ),
        validation_status=_normalize_status(
            getattr(
                extraction,
                "validation_status",
                None,
            ),
            default="pending",
        ),
        extraction_method=getattr(
            extraction,
            "extraction_method",
            None,
        ),
        metadata=_as_dict(
            getattr(
                extraction,
                "metadata",
                None,
            )
        ),
        fields=[
            _build_field_response(field)
            for field in fields
        ],
        created_at=getattr(
            extraction,
            "created_at",
            None,
        ),
        updated_at=getattr(
            extraction,
            "updated_at",
            None,
        ),
    )


# ============================================================================
# INTELLIGENCE
# ============================================================================


async def _load_intelligence(
    db: AsyncSession,
    job: ProcessingJob,
) -> IntelligenceResponse | None:

    result = await db.execute(
        select(DocumentIntelligenceResult)
        .where(
            DocumentIntelligenceResult.processing_id
            == job.id,
        )
    )

    entity = result.scalar_one_or_none()

    if entity is None:
        return None

    document_version = getattr(
        job,
        "document_version",
        None,
    )

    if document_version is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Processing job document version "
                "could not be loaded."
            ),
        )

    document_id = getattr(
        entity,
        "document_id",
        None,
    )

    if document_id is None:
        document_id = getattr(
            document_version,
            "document_id",
            None,
        )

    document_version_id = getattr(
        entity,
        "document_version_id",
        None,
    )

    if document_version_id is None:
        document_version_id = getattr(
            document_version,
            "id",
            None,
        )

    return IntelligenceResponse(
        processing_id=job.id,
        document_id=document_id,
        document_version_id=document_version_id,
        document_type=getattr(
            entity,
            "document_type",
            None,
        ),
        status=_normalize_status(
            job.status,
        ),
        confidence=_normalize_confidence(
            getattr(
                entity,
                "classification_confidence",
                None,
            )
        ),
        structured_data=_as_dict(
            getattr(
                entity,
                "structured_data",
                None,
            )
        ),
        validation_results=_as_dict(
            getattr(
                entity,
                "validation_results",
                None,
            )
        ),
        artifacts=_as_list_of_dicts(
            getattr(
                entity,
                "artifacts",
                None,
            )
        ),
        knowledge=_as_dict(
            getattr(
                entity,
                "knowledge",
                None,
            )
        ),
        raw_text=getattr(
            entity,
            "raw_text",
            None,
        ),
        validation_status=_extract_validation_status(
            getattr(
                entity,
                "validation_results",
                None,
            )
        ),
        created_at=getattr(
            entity,
            "created_at",
            None,
        ),
        updated_at=getattr(
            entity,
            "updated_at",
            None,
        ),
        completed_at=getattr(
            job,
            "completed_at",
            None,
        ),
    )


def _extract_validation_status(
    value: Any,
) -> str | None:

    if not isinstance(value, dict):
        return None

    result = value.get("status")

    if result is None:
        result = value.get(
            "overall_status"
        )

    if result is None:
        nested = value.get(
            "validation"
        )

        if isinstance(
            nested,
            dict,
        ):
            result = nested.get(
                "status"
            )

    if result is None:
        return None

    return str(result).strip() or None


# ============================================================================
# VALIDATION
# ============================================================================


async def _load_validation(
    processing_id: UUID,
    service: ValidationService,
) -> ValidationResponse | None:

    method = getattr(
        service,
        "get_validation_result",
        None,
    )

    if method is None:
        method = getattr(
            service,
            "get_result",
            None,
        )

    if method is None:
        logger.warning(
            "ValidationService has no result retrieval method"
        )
        return None

    result = await method(
        processing_id=processing_id,
    )

    if result is None:
        return None

    if isinstance(
        result,
        dict,
    ):

        issues = result.get(
            "issues",
            result.get(
                "violations",
                [],
            ),
        )

        status_value = str(
            result.get(
                "status",
                "unknown",
            )
        )

        passed = result.get(
            "passed",
            status_value.lower()
            in {
                "passed",
                "pass",
                "valid",
            },
        )

        metadata = result.get(
            "metadata",
            {},
        )

        return ValidationResponse(
            processing_id=processing_id,
            status=status_value,
            passed=bool(passed),
            score=_normalize_confidence(
                result.get(
                    "score",
                    result.get(
                        "confidence",
                    ),
                )
            ),
            issues=[
                ValidationIssueResponse(
                    rule=item.get("rule"),
                    code=item.get("code"),
                    message=str(
                        item.get(
                            "message",
                            "Validation issue",
                        )
                    ),
                    severity=str(
                        item.get(
                            "severity",
                            "error",
                        )
                    ),
                    field=item.get("field"),
                    value=item.get("value"),
                )
                for item in issues
                if isinstance(
                    item,
                    dict,
                )
            ],
            metadata=(
                metadata
                if isinstance(
                    metadata,
                    dict,
                )
                else {}
            ),
            created_at=result.get(
                "created_at",
            ),
            completed_at=result.get(
                "completed_at",
            ),
        )

    status_value = str(
        getattr(
            result,
            "status",
            "unknown",
        )
    )

    issues = getattr(
        result,
        "issues",
        getattr(
            result,
            "violations",
            [],
        ),
    ) or []

    passed = getattr(
        result,
        "passed",
        status_value.lower()
        in {
            "passed",
            "pass",
            "valid",
        },
    )

    metadata = getattr(
        result,
        "metadata",
        {},
    )

    return ValidationResponse(
        processing_id=processing_id,
        status=status_value,
        passed=bool(passed),
        score=_normalize_confidence(
            getattr(
                result,
                "score",
                getattr(
                    result,
                    "confidence",
                    None,
                ),
            )
        ),
        issues=[
            ValidationIssueResponse(
                rule=getattr(
                    item,
                    "rule",
                    None,
                ),
                code=getattr(
                    item,
                    "code",
                    None,
                ),
                message=str(
                    getattr(
                        item,
                        "message",
                        "Validation issue",
                    )
                ),
                severity=str(
                    getattr(
                        item,
                        "severity",
                        "error",
                    )
                ),
                field=getattr(
                    item,
                    "field",
                    None,
                ),
                value=getattr(
                    item,
                    "value",
                    None,
                ),
            )
            for item in issues
        ],
        metadata=(
            metadata
            if isinstance(
                metadata,
                dict,
            )
            else {}
        ),
        created_at=getattr(
            result,
            "created_at",
            None,
        ),
        completed_at=getattr(
            result,
            "completed_at",
            None,
        ),
    )


# ============================================================================
# REVIEW
# ============================================================================



async def _load_review(
    processing_id,
    service: ReviewService,
):
    """
    Load the latest review associated with a processing job.

    ReviewRecord is linked to DocumentIntelligenceResult,
    not directly to ProcessingJob.
    """

    return await service.get_review_by_processing_id(
        processing_id=processing_id
    )


# ============================================================================
# START PROCESSING
# ============================================================================


@router.post(
    "/jobs",
    response_model=ProcessingResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_processing(
    request: ProcessingRequest,
    service: ProcessingService = Depends(
        get_processing_service,
    ),
) -> ProcessingResponse:

    try:

        job = await service.start_processing(
            document_id=request.document_id,
            force=request.force,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception as exc:

        logger.exception(
            "Failed to create processing job",
            extra={
                "document_id": str(
                    request.document_id
                ),
            },
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start document processing.",
        ) from exc

    job_status = _normalize_status(
        getattr(
            job,
            "status",
            "queued",
        ),
        default="queued",
    )

    if job_status == "queued":

        broker = Broker()
        broker.publish(
            "document_processing",
            str(job.id),
        )

        message = (
            "Document processing job created "
            "and queued for execution."
        )

    elif job_status == "running":

        message = (
            "A processing job is already running "
            "for this document version."
        )

    elif job_status == "completed":

        message = (
            "A completed processing job already exists "
            "for this document version."
        )

    else:

        message = (
            f"Processing job is currently "
            f"{job_status}."
        )

    return ProcessingResponse(
        processing_id=job.id,
        document_id=request.document_id,
        document_version_id=job.document_version_id,
        status=job_status,
        message=message,
    )


# ============================================================================
# GET COMPLETE PROCESSING RESULT
# ============================================================================


@router.get(
    "/jobs/{processing_id}",
    response_model=ProcessingAggregateResponse,
)
async def get_processing(
    processing_id: UUID,
    db: AsyncSession = Depends(
        get_async_db,
    ),
    validation_service: ValidationService = Depends(
        get_validation_service,
    ),
    review_service: ReviewService = Depends(
        get_review_service,
    ),
) -> ProcessingAggregateResponse:

    # ------------------------------------------------------------------
    # Load job
    # ------------------------------------------------------------------

    result = await db.execute(
        select(ProcessingJob)
        .where(
            ProcessingJob.id == processing_id,
        )
        .options(
            selectinload(
                ProcessingJob.document_version,
            ),
            selectinload(
                ProcessingJob.steps,
            ),
        )
    )

    job = result.scalar_one_or_none()

    if job is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Processing job not found.",
        )

    document_version = getattr(
        job,
        "document_version",
        None,
    )

    if document_version is None:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Processing job document version "
                "could not be loaded."
            ),
        )

    # ------------------------------------------------------------------
    # Basic processing state
    # ------------------------------------------------------------------

    steps = getattr(
        job,
        "steps",
        None,
    ) or []

    progress = getattr(
        job,
        "progress",
        0,
    ) or 0

    progress = max(
        0,
        min(
            100,
            int(progress),
        ),
    )

    # ------------------------------------------------------------------
    # Aggregate child results
    # ------------------------------------------------------------------

    extraction = await _load_extraction(
        db=db,
        processing_id=processing_id,
    )

    validation = await _load_validation(
        processing_id=processing_id,
        service=validation_service,
    )

    intelligence = await _load_intelligence(
        db=db,
        job=job,
    )

    review = await _load_review(
        processing_id=processing_id,
        service=review_service,
    )

    # ------------------------------------------------------------------
    # Final aggregate response
    # ------------------------------------------------------------------

    return ProcessingAggregateResponse(
        processing_id=job.id,
        document_id=document_version.document_id,
        document_version_id=job.document_version_id,
        status=_normalize_status(
            job.status,
        ),
        current_stage=getattr(
            job,
            "current_step",
            None,
        ),
        progress=progress,
        error=getattr(
            job,
            "error_message",
            None,
        ),
        steps=[
            _build_step_response(step)
            for step in sorted(
                steps,
                key=lambda item: item.step_order,
            )
        ],
        extraction=extraction,
        validation=validation,
        intelligence=intelligence,
        review=review,
        completed_at=getattr(
            job,
            "completed_at",
            None,
        ),
    )


# ============================================================================
# CANCEL
# ============================================================================


@router.post(
    "/jobs/{processing_id}/cancel",
    response_model=ProcessingAggregateResponse,
)
async def cancel_processing(
    processing_id: UUID,
    service: ProcessingService = Depends(
        get_processing_service,
    ),
    db: AsyncSession = Depends(
        get_async_db,
    ),
    validation_service: ValidationService = Depends(
        get_validation_service,
    ),
    review_service: ReviewService = Depends(
        get_review_service,
    ),
) -> ProcessingAggregateResponse:

    try:

        job = await service.cancel_processing(
            processing_id=processing_id,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if job is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Processing job not found.",
        )

    # Return the same canonical representation.
    return await get_processing(
        processing_id=processing_id,
        db=db,
        validation_service=validation_service,
        review_service=review_service,
    )


# ============================================================================
# REVIEW
# ============================================================================


@router.post(
    "/jobs/{processing_id}/review",
    response_model=ReviewResponse,
)
async def submit_review(
    processing_id: UUID,
    request: ReviewSubmission,
    service: ReviewService = Depends(
        get_review_service,
    ),
) -> ReviewResponse:

    method = getattr(
        service,
        "submit_review",
        None,
    )

    if method is None:
        method = getattr(
            service,
            "review",
            None,
        )

    if method is None:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "ReviewService does not expose "
                "a review submission method."
            ),
        )

    try:

        result = await method(
            processing_id=processing_id,
            decision=request.decision,
            comments=request.comments,
            corrections=[
                correction.model_dump()
                for correction
                in request.corrections
            ],
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if result is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Processing job not found.",
        )

    return await _load_review(
        processing_id=processing_id,
        service=service,
    )


# ============================================================================
# APPROVE
# ============================================================================


@router.post(
    "/jobs/{processing_id}/review/approve",
    response_model=ReviewResponse,
)
async def approve_review(
    processing_id: UUID,
    comments: str | None = None,
    service: ReviewService = Depends(
        get_review_service,
    ),
) -> ReviewResponse:

    method = getattr(
        service,
        "approve",
        None,
    )

    if method is None:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "ReviewService does not expose "
                "an approve method."
            ),
        )

    try:

        await method(
            processing_id=processing_id,
            comments=comments,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    result = await _load_review(
        processing_id=processing_id,
        service=service,
    )

    if result is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review record not found.",
        )

    return result


# ============================================================================
# REJECT
# ============================================================================


@router.post(
    "/jobs/{processing_id}/review/reject",
    response_model=ReviewResponse,
)
async def reject_review(
    processing_id: UUID,
    comments: str | None = None,
    service: ReviewService = Depends(
        get_review_service,
    ),
) -> ReviewResponse:

    method = getattr(
        service,
        "reject",
        None,
    )

    if method is None:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "ReviewService does not expose "
                "a reject method."
            ),
        )

    try:

        await method(
            processing_id=processing_id,
            comments=comments,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    result = await _load_review(
        processing_id=processing_id,
        service=service,
    )

    if result is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review record not found.",
        )

    return result


# ============================================================================
# PUBLIC EXPORTS
# ============================================================================


__all__ = [
    "router",
    "ProcessingRequest",
    "ProcessingResponse",
    "ProcessingAggregateResponse",
    "ProcessingStepResponse",
    "ExtractionResponse",
    "ExtractedFieldResponse",
    "ValidationResponse",
    "ValidationIssueResponse",
    "IntelligenceResponse",
    "ReviewResponse",
    "ReviewSubmission",
    "ReviewCorrection",
]