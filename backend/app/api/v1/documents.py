"""
app/api/v1/documents.py

Document API.

Responsibilities:
- Accept document uploads
- Validate request parameters
- Return document metadata
- Delegate storage and persistence to services

The API layer does NOT contain:
- Storage implementation
- OCR logic
- Parsing logic
- Chunking logic
- Embedding generation
- Database business logic
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.dependencies import get_document_service
from app.services.documents.document_service import (
    DocumentNotFoundError,
    DocumentService,
    DuplicateDocumentError,
)


# ============================================================================
# ROUTER
# ============================================================================

router = APIRouter()

logger = logging.getLogger(__name__)

settings = get_settings()


# ============================================================================
# SCHEMAS
# ============================================================================


class DocumentResponse(BaseModel):
    """Public representation of a document."""

    id: str
    name: str
    filename: str | None = None
    content_type: str | None = None
    size: int | None = None
    status: str = "uploaded"
    created_at: str | None = None
    updated_at: str | None = None


class DocumentUploadResponse(BaseModel):
    """Response returned after document upload."""

    document_id: str
    job_id: str | None = None
    status: str = "uploaded"
    message: str = "Document uploaded successfully"


class DocumentListResponse(BaseModel):
    """Paginated document response."""

    items: list[DocumentResponse]
    total: int
    page: int
    page_size: int


# ============================================================================
# HELPERS
# ============================================================================


def _to_document_response(
    document: Any,
) -> DocumentResponse:
    """
    Convert a database document model into the public API response.
    """

    metadata = getattr(
        document,
        "metadata_",
        None,
    )

    if not isinstance(metadata, dict):
        metadata = {}

    return DocumentResponse(
        id=str(document.id),
        name=getattr(
            document,
            "name",
            getattr(
                document,
                "filename",
                "",
            ),
        ),
        filename=metadata.get(
            "filename",
            getattr(
                document,
                "filename",
                None,
            ),
        ),
        content_type=metadata.get(
            "content_type",
            getattr(
                document,
                "content_type",
                None,
            ),
        ),
        size=metadata.get(
            "size_bytes",
            getattr(
                document,
                "size",
                getattr(
                    document,
                    "size_bytes",
                    None,
                ),
            ),
        ),
        status=getattr(
            document,
            "status",
            "unknown",
        ),
        created_at=(
            str(document.created_at)
            if getattr(
                document,
                "created_at",
                None,
            )
            else None
        ),
        updated_at=(
            str(document.updated_at)
            if getattr(
                document,
                "updated_at",
                None,
            )
            else None
        ),
    )


# ============================================================================
# UPLOAD DOCUMENT
# ============================================================================


@router.post(
    "",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    service: DocumentService = Depends(
        get_document_service,
    ),
) -> DocumentUploadResponse:
    """
    Upload a document.

    DocumentService handles:
    - validation
    - checksum generation
    - duplicate detection
    - object storage
    - database persistence
    """

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required.",
        )

    logger.info(
        "Document upload started: filename=%s content_type=%s",
        file.filename,
        file.content_type,
    )

    try:
        document = await service.upload(
            file=file,
        )

    except DuplicateDocumentError as exc:
        logger.warning(
            "Duplicate document upload: filename=%s error=%s",
            file.filename,
            exc,
        )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        logger.warning(
            "Document validation/value error: filename=%s error=%s",
            file.filename,
            exc,
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception(
            "Document upload failed: filename=%s",
            file.filename,
        )

        if settings.DEBUG:
            detail = (
                f"{type(exc).__name__}: {exc}"
            )
        else:
            detail = "Failed to upload document."

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        ) from exc

    logger.info(
        "Document upload completed: document_id=%s filename=%s",
        document.id,
        file.filename,
    )

    return DocumentUploadResponse(
        document_id=str(document.id),
        status=getattr(
            document,
            "status",
            "uploaded",
        ),
        message="Document uploaded successfully",
    )


# ============================================================================
# LIST DOCUMENTS
# ============================================================================


@router.get(
    "",
    response_model=DocumentListResponse,
)
async def list_documents(
    page: int = 1,
    page_size: int = 20,
    service: DocumentService = Depends(
        get_document_service,
    ),
) -> DocumentListResponse:
    """
    List documents with pagination.
    """

    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page must be greater than or equal to 1.",
        )

    if page_size < 1 or page_size > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page size must be between 1 and 100.",
        )

    offset = (page - 1) * page_size

    try:
        documents = await service.list(
            limit=page_size,
            offset=offset,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception(
            "Failed to retrieve documents.",
        )

        if settings.DEBUG:
            detail = (
                f"{type(exc).__name__}: {exc}"
            )
        else:
            detail = "Failed to retrieve documents."

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        ) from exc

    raw_documents = getattr(
        documents,
        "items",
        documents,
    )

    if raw_documents is None:
        raw_documents = []

    raw_documents = list(raw_documents)

    return DocumentListResponse(
        items=[
            _to_document_response(document)
            for document in raw_documents
        ],
        total=getattr(
            documents,
            "total",
            len(raw_documents),
        ),
        page=page,
        page_size=page_size,
    )


# ============================================================================
# GET SINGLE DOCUMENT
# ============================================================================


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
)
async def get_document(
    document_id: UUID,
    service: DocumentService = Depends(
        get_document_service,
    ),
) -> DocumentResponse:
    """
    Get a single document by ID.
    """

    try:
        document = await service.get(
            document_id,
        )

    except DocumentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception(
            "Failed to retrieve document: document_id=%s",
            document_id,
        )

        if settings.DEBUG:
            detail = (
                f"{type(exc).__name__}: {exc}"
            )
        else:
            detail = "Failed to retrieve document."

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        ) from exc

    return _to_document_response(document)


# ============================================================================
# DELETE DOCUMENT
# ============================================================================


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_document(
    document_id: UUID,
    service: DocumentService = Depends(
        get_document_service,
    ),
) -> None:
    """
    Delete a document.

    DocumentService handles:
    - object storage deletion
    - database deletion
    - transaction commit
    """

    try:
        await service.delete(
            document_id,
        )

    except DocumentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception(
            "Failed to delete document: document_id=%s",
            document_id,
        )

        if settings.DEBUG:
            detail = (
                f"{type(exc).__name__}: {exc}"
            )
        else:
            detail = "Failed to delete document."

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        ) from exc

    return None