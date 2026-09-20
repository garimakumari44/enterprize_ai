from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO


class StorageProvider(ABC):
    """
    Abstract storage provider.

    Every storage backend (Local, S3, Azure, GCS, MinIO, etc.)
    should implement this interface.
    """

    @abstractmethod
    def save(
        self,
        file: BinaryIO,
        destination: str,
    ) -> str:
        """
        Save a file.

        Returns:
            Relative storage path.
        """
        raise NotImplementedError

    @abstractmethod
    def delete(
        self,
        path: str,
    ) -> bool:
        """
        Delete a stored file.

        Returns:
            True if deleted.
        """
        raise NotImplementedError

    @abstractmethod
    def exists(
        self,
        path: str,
    ) -> bool:
        """
        Check if file exists.
        """
        raise NotImplementedError

    @abstractmethod
    def open(
        self,
        path: str,
    ) -> BinaryIO:
        """
        Open file for reading.
        """
        raise NotImplementedError

    @abstractmethod
    def get_path(
        self,
        path: str,
    ) -> Path:
        """
        Return filesystem path if applicable.
        """
        raise NotImplementedErrors