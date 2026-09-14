"""
Document checksum utilities.

SHA-256 is used as the canonical checksum algorithm.

The checksum serves two purposes:

1. File integrity verification.
2. Content-based deduplication.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import BinaryIO


CHUNK_SIZE = 1024 * 1024  # 1 MB


def calculate_checksum(file: BinaryIO) -> str:
    """
    Calculate SHA-256 checksum for an open binary file.

    The current file position is restored after calculation.
    """

    original_position = file.tell()

    hasher = hashlib.sha256()

    try:
        file.seek(0)

        while True:
            chunk = file.read(CHUNK_SIZE)

            if not chunk:
                break

            hasher.update(chunk)

    finally:
        file.seek(original_position)

    return hasher.hexdigest()


def calculate_bytes_checksum(data: bytes) -> str:
    """
    Calculate SHA-256 checksum for raw bytes.
    """

    return hashlib.sha256(data).hexdigest()


def calculate_file_checksum(path: str | Path) -> str:
    """
    Calculate SHA-256 checksum for a file on disk.
    """

    hasher = hashlib.sha256()

    with open(path, "rb") as file:
        while True:
            chunk = file.read(CHUNK_SIZE)

            if not chunk:
                break

            hasher.update(chunk)

    return hasher.hexdigest()


def verify_checksum(
    file: BinaryIO,
    expected_checksum: str,
) -> bool:
    """
    Verify that a file matches the expected SHA-256 checksum.
    """

    actual_checksum = calculate_checksum(file)

    return actual_checksum.lower() == expected_checksum.lower()