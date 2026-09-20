"""
app/storage/base.py

Canonical object-storage provider contract.

The rest of the application depends on StorageProvider,
not on a concrete storage implementation.

Current implementation:
    StorageProvider
          |
          └── MinIOProvider
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import BinaryIO, Mapping, Optional

from .models import (
    ObjectMetadata,
    StorageObject,
    UploadResult,
)


class StorageProvider(ABC):
    """
    Abstract interface for object storage.

    Implementations are responsible for communicating with
    the underlying object-storage system.
    """

    @abstractmethod
    def upload(
        self,
        *,
        bucket: str,
        key: str,
        file: BinaryIO,
        content_type: Optional[str] = None,
        metadata: Optional[Mapping[str, str]] = None,
    ) -> UploadResult:
        """
        Upload an object.

        Args:
            bucket:
                Storage bucket name.

            key:
                Object key/path inside the bucket.

            file:
                Binary file-like object.

            content_type:
                MIME type of the object.

            metadata:
                Optional object metadata.

        Returns:
            UploadResult
        """
        raise NotImplementedError

    @abstractmethod
    def download(
        self,
        *,
        bucket: str,
        key: str,
    ) -> bytes:
        """
        Download an object and return its contents as bytes.
        """
        raise NotImplementedError

    @abstractmethod
    def download_stream(
        self,
        *,
        bucket: str,
        key: str,
    ) -> BinaryIO:
        """
        Download an object as a readable binary stream.
        """
        raise NotImplementedError

    @abstractmethod
    def delete(
        self,
        *,
        bucket: str,
        key: str,
    ) -> None:
        """
        Delete an object.
        """
        raise NotImplementedError

    @abstractmethod
    def exists(
        self,
        *,
        bucket: str,
        key: str,
    ) -> bool:
        """
        Check whether an object exists.
        """
        raise NotImplementedError

    @abstractmethod
    def get_metadata(
        self,
        *,
        bucket: str,
        key: str,
    ) -> ObjectMetadata:
        """
        Retrieve object metadata.
        """
        raise NotImplementedError

    @abstractmethod
    def generate_presigned_url(
        self,
        *,
        bucket: str,
        key: str,
        expires_in: int = 3600,
    ) -> str:
        """
        Generate a temporary URL for accessing an object.
        """
        raise NotImplementedError

    @abstractmethod
    def ensure_bucket(
        self,
        *,
        bucket: str,
    ) -> None:
        """
        Ensure that a bucket exists.
        """
        raise NotImplementedError

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check whether the storage provider is reachable.
        """
        raise NotImplementedError