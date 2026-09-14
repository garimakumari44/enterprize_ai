"""
app/services/documents/document_service.py

Document application service.

Responsibilities:

    - Validate uploaded documents
    - Calculate document checksums
    - Detect duplicate documents
    - Generate object-storage keys
    - Upload objects through StorageService
    - Persist logical Document metadata
    - Persist immutable DocumentVersion records
    - Delete documents from storage and PostgreSQL
    - Manage document metadata and processing status

Architecture:

    Document API
         |
         v
    DocumentService
         |
         +----------------------+----------------------+
         |                      |                      |
         v                      v                      v
    DocumentRepository    DocumentVersion       StorageService
                                |                      |
                                v                      v
                           PostgreSQL                MinIO

Important:

    Document represents the logical document.

    DocumentVersion represents the exact uploaded artifact.

    Processing always operates on a DocumentVersion.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.document_version import DocumentVersion
from app.documents.checksum import calculate_checksum
from app.documents.validators import validate_upload
from app.repositories.documents.document_repository import DocumentRepository
from app.storage.service import StorageService


class DocumentNotFoundError(Exception):
    """Raised when a requested document does not exist."""


class DuplicateDocumentError(Exception):
    """Raised when an identical document already exists."""


class DocumentService:
    """
    Application service for document lifecycle management.
    """

    def __init__(
        self,
        session: AsyncSession,
        storage: StorageService,
    ) -> None:
        self.session = session
        self.storage = storage
        self.repository = DocumentRepository(session)

    # ==================================================================
    # UPLOAD
    # ==================================================================

    async def upload(
        self,
        *,
        file: UploadFile,
        project_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """
        Validate, upload, and persist a document.

        The important invariant is:

            Document
                |
                +--> current_version_id
                           |
                           v
                    DocumentVersion
                           |
                           +--> object_storage_key
                           |
                           v
                         MinIO
        """

        # --------------------------------------------------------------
        # 1. Validate upload
        # --------------------------------------------------------------

        (
            filename,
            content_type,
            size_bytes,
        ) = await validate_upload(file)

        # --------------------------------------------------------------
        # 2. Reset stream
        # --------------------------------------------------------------

        file.file.seek(0)

        # --------------------------------------------------------------
        # 3. Calculate checksum
        # --------------------------------------------------------------

        checksum = calculate_checksum(
            file.file
        )

        # --------------------------------------------------------------
        # 4. Duplicate detection
        # --------------------------------------------------------------

        existing_document = (
            await self.repository.get_by_checksum(
                checksum=checksum,
                project_id=project_id,
            )
        )

        if existing_document is not None:
            raise DuplicateDocumentError(
                "A document with the same content already exists."
            )

        # --------------------------------------------------------------
        # 5. Generate document ID
        # --------------------------------------------------------------

        document_id = uuid4()

        # --------------------------------------------------------------
        # 6. Generate MinIO object key
        # --------------------------------------------------------------

        storage_key = self._build_storage_key(
            document_id=document_id,
            filename=filename,
        )

        # --------------------------------------------------------------
        # 7. Upload to MinIO
        # --------------------------------------------------------------

        file.file.seek(0)

        try:
            self.storage.upload(
                key=storage_key,
                file=file.file,
                content_type=content_type,
                metadata={
                    "document_id": str(document_id),
                    "original_filename": filename,
                    "checksum": checksum,
                },
            )

        except Exception:
            raise

        # --------------------------------------------------------------
        # 8. Build document metadata
        # --------------------------------------------------------------

        document_metadata: dict[str, Any] = dict(
            metadata or {}
        )

        document_metadata.update(
            {
                "filename": filename,
                "content_type": content_type,
                "size_bytes": size_bytes,
                "checksum": checksum,
                "storage_key": storage_key,
            }
        )

        if project_id is not None:
            document_metadata["project_id"] = str(
                project_id
            )

        # --------------------------------------------------------------
        # 9. Persist database records
        # --------------------------------------------------------------

        try:
            document = await self.repository.create(
                name=filename,
                document_type=self._infer_document_type(
                    content_type=content_type,
                    filename=filename,
                ),
                status="processing",
                metadata=document_metadata,
            )

            await self.session.flush()

            # ----------------------------------------------------------
            # First uploaded artifact = version 1
            # ----------------------------------------------------------

            document_version = DocumentVersion(
                document_id=document.id,
                version_number=1,

                original_filename=filename,
                mime_type=content_type,
                file_size=size_bytes,
                checksum=checksum,

                storage_provider="minio",
                object_storage_bucket=self.storage.bucket,
                object_storage_key=storage_key,

                status="uploaded",

                page_count=None,
                detected_language=None,

                metadata_=dict(
                    metadata or {}
                ),
            )

            self.session.add(
                document_version
            )

            await self.session.flush()

            # ----------------------------------------------------------
            # CRITICAL:
            # connect logical document to uploaded version
            # ----------------------------------------------------------

            document.current_version_id = (
                document_version.id
            )

            document.status = "processing"

            await self.session.flush()

            # ----------------------------------------------------------
            # Commit
            # ----------------------------------------------------------

            await self.session.commit()

            await self.session.refresh(
                document
            )

            return document

        except Exception:
            await self._cleanup_storage_object(
                storage_key
            )

            await self.session.rollback()

            raise

    # ==================================================================
    # GET
    # ==================================================================

    async def get(
        self,
        document_id: UUID,
    ):
        document = await self.repository.get_by_id(
            document_id
        )

        if document is None:
            raise DocumentNotFoundError(
                f"Document {document_id} not found."
            )

        return document

    # ==================================================================
    # LIST
    # ==================================================================

    async def list(
        self,
        *,
        project_id: UUID | None = None,
        limit: int = 100,
        offset: int = 0,
    ):
        if limit <= 0:
            raise ValueError(
                "limit must be greater than zero."
            )

        if offset < 0:
            raise ValueError(
                "offset cannot be negative."
            )

        return await self.repository.list(
            project_id=project_id,
            limit=limit,
            offset=offset,
        )

    # ==================================================================
    # DELETE
    # ==================================================================

    async def delete(
        self,
        document_id: UUID,
    ) -> None:

        document = await self.get(
            document_id
        )

        storage_keys = (
            await self._get_storage_keys(
                document
            )
        )

        try:

            for storage_key in storage_keys:
                self.storage.delete(
                    key=storage_key
                )

            await self.repository.delete(
                document
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

    # ==================================================================
    # UPDATE METADATA
    # ==================================================================

    async def update_metadata(
        self,
        document_id: UUID,
        metadata: dict[str, Any],
    ):

        document = await self.get(
            document_id
        )

        updated_document = (
            await self.repository.update(
                document,
                metadata_=metadata,
            )
        )

        await self.session.commit()

        await self.session.refresh(
            updated_document
        )

        return updated_document

    # ==================================================================
    # PROCESSING STATUS
    # ==================================================================

    async def mark_processing(
        self,
        document_id: UUID,
    ):

        return await self._update_status(
            document_id=document_id,
            status="processing",
        )

    async def mark_completed(
        self,
        document_id: UUID,
    ):

        return await self._update_status(
            document_id=document_id,
            status="completed",
        )

    async def mark_failed(
        self,
        document_id: UUID,
    ):

        return await self._update_status(
            document_id=document_id,
            status="failed",
        )

    # ==================================================================
    # STATUS UPDATE
    # ==================================================================

    async def _update_status(
        self,
        *,
        document_id: UUID,
        status: str,
    ):

        document = await self.get(
            document_id
        )

        try:

            updated_document = (
                await self.repository.update(
                    document,
                    status=status,
                )
            )

            await self.session.commit()

            await self.session.refresh(
                updated_document
            )

            return updated_document

        except Exception:
            await self.session.rollback()
            raise

    # ==================================================================
    # STORAGE KEY
    # ==================================================================

    @staticmethod
    def _build_storage_key(
        *,
        document_id: UUID,
        filename: str,
    ) -> str:

        safe_filename = (
            filename
            .replace("\\", "/")
            .split("/")[-1]
        )

        return (
            f"documents/"
            f"{document_id}/"
            f"{safe_filename}"
        )

    # ==================================================================
    # DOCUMENT TYPE
    # ==================================================================

    @staticmethod
    def _infer_document_type(
        *,
        content_type: str | None,
        filename: str,
    ) -> str:

        if content_type:
            normalized = (
                content_type.lower().strip()
            )

            mapping = {
                "application/pdf": "pdf",
                "text/plain": "text",
                "text/markdown": "markdown",
                "text/csv": "csv",
                "application/json": "json",
                "application/xml": "xml",
                "text/xml": "xml",
                "application/msword": "word",

                (
                    "application/"
                    "vnd.openxmlformats-officedocument."
                    "wordprocessingml.document"
                ): "word",

                (
                    "application/"
                    "vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ): "spreadsheet",

                (
                    "application/"
                    "vnd.openxmlformats-officedocument."
                    "presentationml.presentation"
                ): "presentation",
            }

            mapped = mapping.get(
                normalized
            )

            if mapped:
                return mapped

        normalized_filename = filename.lower()

        if normalized_filename.endswith(".pdf"):
            return "pdf"

        if normalized_filename.endswith(
            (".doc", ".docx")
        ):
            return "word"

        if normalized_filename.endswith(
            (".xls", ".xlsx")
        ):
            return "spreadsheet"

        if normalized_filename.endswith(
            (".ppt", ".pptx")
        ):
            return "presentation"

        if normalized_filename.endswith(".csv"):
            return "csv"

        if normalized_filename.endswith(".json"):
            return "json"

        if normalized_filename.endswith(
            (".md", ".markdown")
        ):
            return "markdown"

        if normalized_filename.endswith(
            (".txt", ".log")
        ):
            return "text"

        return "file"

    # ==================================================================
    # STORAGE KEY EXTRACTION
    # ==================================================================

    async def _get_storage_keys(
        self,
        document: Any,
    ) -> list[str]:

        result = await self.session.execute(
            select(DocumentVersion)
            .where(
                DocumentVersion.document_id
                == document.id
            )
            .order_by(
                DocumentVersion.version_number
            )
        )

        versions = result.scalars().all()

        keys: list[str] = []

        for version in versions:
            key = getattr(
                version,
                "object_storage_key",
                None,
            )

            if key:
                keys.append(
                    str(key)
                )

        # Backward compatibility
        if not keys:

            metadata = getattr(
                document,
                "metadata_",
                None,
            )

            if isinstance(
                metadata,
                dict,
            ):
                storage_key = metadata.get(
                    "storage_key"
                )

                if storage_key:
                    keys.append(
                        str(storage_key)
                    )

        return list(
            dict.fromkeys(keys)
        )

    # ==================================================================
    # STORAGE CLEANUP
    # ==================================================================

    async def _cleanup_storage_object(
        self,
        storage_key: str,
    ) -> None:

        try:

            self.storage.delete(
                key=storage_key
            )

        except Exception:
            # Do not hide the original DB exception.
            pass


__all__ = [
    "DocumentService",
    "DocumentNotFoundError",
    "DuplicateDocumentError",
]