"""
app/storage/service.py

Application-facing storage service.

The service hides the concrete storage provider from higher-level
application services.

Architecture:

    DocumentService
          |
          v
    StorageService
          |
          v
    StorageProvider
          |
          v
    MinIOProvider
"""

from __future__ import annotations

from typing import BinaryIO, Mapping

from app.storage.base import StorageProvider
from app.storage.models import (
    ObjectMetadata,
    UploadResult,
)


class StorageService:
    """
    Application-level object storage service.

    The bucket is configured once when the service is created.

    Application-level callers only need to provide the object key.
    """

    def __init__(
        self,
        *,
        provider: StorageProvider,
        bucket: str,
    ) -> None:

        if provider is None:
            raise ValueError(
                "Storage provider cannot be None."
            )

        if not isinstance(bucket, str):
            raise TypeError(
                "Storage bucket must be a string."
            )

        bucket = bucket.strip()

        if not bucket:
            raise ValueError(
                "Storage bucket cannot be empty."
            )

        self.provider = provider
        self.bucket = bucket

    # ==================================================================
    # UPLOAD
    # ==================================================================

    def upload(
        self,
        *,
        key: str,
        file: BinaryIO,
        content_type: str | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> UploadResult:

        self._validate_key(key)

        if file is None:
            raise ValueError(
                "Upload file cannot be None."
            )

        self.ensure_bucket()

        return self.provider.upload(
            bucket=self.bucket,
            key=key,
            file=file,
            content_type=content_type,
            metadata=metadata,
        )

    # ==================================================================
    # DOWNLOAD
    # ==================================================================

    def download(
        self,
        *,
        key: str,
    ) -> bytes:

        self._validate_key(key)

        content = self.provider.download(
            bucket=self.bucket,
            key=key,
        )

        if not isinstance(content, bytes):
            raise TypeError(
                "StorageProvider.download() must return bytes."
            )

        return content

    # ==================================================================
    # DOWNLOAD STREAM
    # ==================================================================

    def download_stream(
        self,
        *,
        key: str,
    ) -> BinaryIO:

        self._validate_key(key)

        stream = self.provider.download_stream(
            bucket=self.bucket,
            key=key,
        )

        if stream is None:
            raise RuntimeError(
                "Storage provider returned no download stream."
            )

        return stream

    # ==================================================================
    # DELETE
    # ==================================================================

    def delete(
        self,
        *,
        key: str,
    ) -> None:

        self._validate_key(key)

        self.provider.delete(
            bucket=self.bucket,
            key=key,
        )

    # ==================================================================
    # EXISTS
    # ==================================================================

    def exists(
        self,
        *,
        key: str,
    ) -> bool:

        self._validate_key(key)

        return bool(
            self.provider.exists(
                bucket=self.bucket,
                key=key,
            )
        )

    # ==================================================================
    # METADATA
    # ==================================================================

    def get_metadata(
        self,
        *,
        key: str,
    ) -> ObjectMetadata:

        self._validate_key(key)

        return self.provider.get_metadata(
            bucket=self.bucket,
            key=key,
        )

    # ==================================================================
    # PRESIGNED URL
    # ==================================================================

    def generate_download_url(
        self,
        *,
        key: str,
        expires_in: int = 3600,
    ) -> str:

        self._validate_key(key)

        if not isinstance(expires_in, int):
            raise TypeError(
                "expires_in must be an integer."
            )

        if expires_in <= 0:
            raise ValueError(
                "expires_in must be greater than zero."
            )

        return self.provider.generate_presigned_url(
            bucket=self.bucket,
            key=key,
            expires_in=expires_in,
        )

    # ==================================================================
    # BUCKET
    # ==================================================================

    def ensure_bucket(self) -> None:

        self.provider.ensure_bucket(
            bucket=self.bucket,
        )

    # ==================================================================
    # HEALTH
    # ==================================================================

    def health_check(self) -> bool:

        return bool(
            self.provider.health_check()
        )

    # ==================================================================
    # VALIDATION
    # ==================================================================

    @staticmethod
    def _validate_key(
        key: str,
    ) -> None:

        if not isinstance(key, str):
            raise TypeError(
                "Storage key must be a string."
            )

        key = key.strip()

        if not key:
            raise ValueError(
                "Storage key cannot be empty."
            )

        if key.startswith("/"):
            raise ValueError(
                "Storage key must not start with '/'."
            )

        if "\x00" in key:
            raise ValueError(
                "Storage key cannot contain null bytes."
            )


__all__ = [
    "StorageService",
]