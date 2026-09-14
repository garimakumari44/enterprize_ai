from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.schemas.documents.tag_schema import (
    TagCreate,
    TagUpdate,
    TagResponse,
)
from app.services.documents.document_service import DocumentService
from app.core.dependencies import get_document_service

router = APIRouter(
    prefix="/tags",
    tags=["Tags"],
)


@router.post(
    "",
    response_model=TagResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_tag(
    payload: TagCreate,
    service: DocumentService = Depends(get_document_service),
):
    return await service.create_tag(payload)


@router.get(
    "",
    response_model=list[TagResponse],
)
async def list_tags(
    service: DocumentService = Depends(get_document_service),
):
    return await service.list_tags()


@router.get(
    "/{tag_id}",
    response_model=TagResponse,
)
async def get_tag(
    tag_id: UUID,
    service: DocumentService = Depends(get_document_service),
):
    return await service.get_tag(tag_id)


@router.put(
    "/{tag_id}",
    response_model=TagResponse,
)
async def update_tag(
    tag_id: UUID,
    payload: TagUpdate,
    service: DocumentService = Depends(get_document_service),
):
    return await service.update_tag(tag_id, payload)


@router.delete(
    "/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_tag(
    tag_id: UUID,
    service: DocumentService = Depends(get_document_service),
):
    await service.delete_tag(tag_id)