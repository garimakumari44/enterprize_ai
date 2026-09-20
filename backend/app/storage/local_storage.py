from __future__ import annotations

import shutil
from pathlib import Path
from typing import BinaryIO

from app.storage.storage_provider import StorageProvider


class LocalStorage(StorageProvider):
    """
    Local filesystem storage implementation.
    """

    def __init__(self, base_directory: str = "uploads") -> None:
        self.base_directory = Path(base_directory)
        self.base_directory.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        file: BinaryIO,
        destination: str,
    ) -> str:
        """
        Save file into local storage.

        Returns relative path.
        """

        relative_path = Path(destination)
        full_path = self.base_directory / relative_path

        full_path.parent.mkdir(parents=True, exist_ok=True)

        with open(full_path, "wb") as buffer:
            shutil.copyfileobj(file, buffer)

        return str(relative_path)

    def delete(
        self,
        path: str,
    ) -> bool:
        """
        Delete stored file.
        """

        file_path = self.base_directory / path

        if not file_path.exists():
            return False

        file_path.unlink()

        return True

    def exists(
        self,
        path: str,
    ) -> bool:
        """
        Check file existence.
        """

        return (self.base_directory / path).exists()

    def open(
        self,
        path: str,
    ) -> BinaryIO:
        """
        Open file for reading.
        """

        file_path = self.base_directory / path

        return open(file_path, "rb")

    def get_path(
        self,
        path: str,
    ) -> Path:
        """
        Return absolute file path.
        """

        return self.base_directory / path