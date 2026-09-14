from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.schemas.documents.folder_schema import (
    FolderCreate,
    FolderUpdate,
    FolderResponse,
)
from app.services.documents.document_service import DocumentService
from app.core.dependencies import get_document_service

router = APIRouter(
    prefix="/folders",
    tags=["Folders"],
)


@router.post(
    "",
    response_model=FolderResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_folder(
    payload: FolderCreate,
    service: DocumentService = Depends(get_document_service),
):
    return await service.create_folder(payload)


@router.get(
    "",
    response_model=list[FolderResponse],
)
async def list_folders(
    service: DocumentService = Depends(get_document_service),
):
    return await service.list_folders()


@router.get(
    "/{folder_id}",
    response_model=FolderResponse,
)
async def get_folder(
    folder_id: UUID,
    service: DocumentService = Depends(get_document_service),
):
    return await service.get_folder(folder_id)


@router.put(
    "/{folder_id}",
    response_model=FolderResponse,
)
async def update_folder(
    folder_id: UUID,
    payload: FolderUpdate,
    service: DocumentService = Depends(get_document_service),
):
    return await service.update_folder(folder_id, payload)


@router.delete(
    "/{folder_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_folder(
    folder_id: UUID,
    service: DocumentService = Depends(get_document_service),
):
    await service.delete_folder(folder_id)