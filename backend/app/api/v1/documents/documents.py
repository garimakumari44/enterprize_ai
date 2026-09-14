from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile, Query, status

from app.schemas.documents.document_schema import (
    DocumentCreate,
    DocumentResponse,
    DocumentUpdate,
    DocumentListResponse,
)
from app.services.documents.document_service import DocumentService
from app.core.dependencies import get_document_service

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    folder_id: UUID | None = Form(default=None),
    description: str | None = Form(default=None),
    service: DocumentService = Depends(get_document_service),
):
    return await service.upload_document(
        file=file,
        folder_id=folder_id,
        description=description,
    )


@router.get(
    "",
    response_model=DocumentListResponse,
)
async def list_documents(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
    folder_id: UUID | None = None,
    service: DocumentService = Depends(get_document_service),
):
    return await service.list_documents(
        skip=skip,
        limit=limit,
        search=search,
        folder_id=folder_id,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
)
async def get_document(
    document_id: UUID,
    service: DocumentService = Depends(get_document_service),
):
    return await service.get_document(document_id)


@router.put(
    "/{document_id}",
    response_model=DocumentResponse,
)
async def update_document(
    document_id: UUID,
    payload: DocumentUpdate,
    service: DocumentService = Depends(get_document_service),
):
    return await service.update_document(document_id, payload)


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_document(
    document_id: UUID,
    service: DocumentService = Depends(get_document_service),
):
    await service.delete_document(document_id)