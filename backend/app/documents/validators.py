"""
Document validation.

Validation here is concerned with the uploaded object itself.

Business rules and persistence belong to DocumentService/Repository.
"""

from __future__ import annotations

import mimetypes
from pathlib import Path

from fastapi import UploadFile


# 50 MB default application limit.
DEFAULT_MAX_FILE_SIZE = 50 * 1024 * 1024


# Supported document types.
ALLOWED_CONTENT_TYPES: set[str] = {
    "application/pdf",
    "text/plain",
    "text/csv",
    "application/json",

    # Microsoft Office
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",

    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",

    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",

    # Common image formats for OCR/document intelligence.
    "image/jpeg",
    "image/png",
    "image/tiff",
    "image/webp",
}


class DocumentValidationError(ValueError):
    """Raised when a document fails validation."""


def validate_filename(filename: str) -> str:
    """
    Validate and normalize a filename.
    """

    if not filename:
        raise DocumentValidationError(
            "Filename is required."
        )

    filename = Path(filename).name.strip()

    if not filename:
        raise DocumentValidationError(
            "Filename is invalid."
        )

    if len(filename) > 512:
        raise DocumentValidationError(
            "Filename is too long."
        )

    return filename


def validate_content_type(
    content_type: str | None,
) -> str:
    """
    Validate MIME type.
    """

    if not content_type:
        raise DocumentValidationError(
            "Content type is required."
        )

    content_type = content_type.lower().strip()

    if content_type not in ALLOWED_CONTENT_TYPES:
        raise DocumentValidationError(
            f"Unsupported document type: {content_type}"
        )

    return content_type


def validate_size(
    size_bytes: int,
    max_size: int = DEFAULT_MAX_FILE_SIZE,
) -> None:
    """
    Validate document size.
    """

    if size_bytes < 0:
        raise DocumentValidationError(
            "Document size cannot be negative."
        )

    if size_bytes > max_size:
        raise DocumentValidationError(
            f"Document exceeds maximum allowed size "
            f"of {max_size} bytes."
        )


async def get_upload_size(
    file: UploadFile,
) -> int:
    """
    Determine the size of an uploaded file.

    The current stream position is restored afterwards.
    """

    current_position = file.file.tell()

    try:
        file.file.seek(0, 2)
        size = file.file.tell()
    finally:
        file.file.seek(current_position)

    return size


async def validate_upload(
    file: UploadFile,
    max_size: int = DEFAULT_MAX_FILE_SIZE,
) -> tuple[str, str, int]:
    """
    Validate an uploaded document.

    Returns:

        (
            normalized_filename,
            validated_content_type,
            size_bytes,
        )
    """

    filename = validate_filename(
        file.filename or ""
    )

    content_type = validate_content_type(
        file.content_type
    )

    size_bytes = await get_upload_size(file)

    validate_size(
        size_bytes,
        max_size=max_size,
    )

    return (
        filename,
        content_type,
        size_bytes,
    )


def guess_content_type(
    filename: str,
) -> str | None:
    """
    Guess MIME type from filename.

    This should not replace actual content inspection for
    security-sensitive deployments.
    """

    content_type, _ = mimetypes.guess_type(filename)

    return content_type