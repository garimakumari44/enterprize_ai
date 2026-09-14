from __future__ import annotations

import hashlib
import mimetypes
import os
import re
import uuid
from pathlib import Path
from typing import BinaryIO


# ---------------------------------------------------------------------
# Allowed File Types
# ---------------------------------------------------------------------

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".txt",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".csv",
    ".ppt",
    ".pptx",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".webp",
}

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


# ---------------------------------------------------------------------
# Filename Helpers
# ---------------------------------------------------------------------


def sanitize_filename(filename: str) -> str:
    """
    Remove unsafe characters from filenames.
    """
    filename = Path(filename).name
    filename = re.sub(r"[^\w.\- ]", "_", filename)
    return filename.strip()


def generate_storage_filename(filename: str) -> str:
    """
    Generates a unique filename for storage.
    """
    ext = Path(filename).suffix.lower()
    return f"{uuid.uuid4().hex}{ext}"


def get_extension(filename: str) -> str:
    return Path(filename).suffix.lower()


# ---------------------------------------------------------------------
# MIME Type
# ---------------------------------------------------------------------


def get_mime_type(filename: str) -> str:
    mime, _ = mimetypes.guess_type(filename)
    return mime or "application/octet-stream"


# ---------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------


def is_allowed_file(filename: str) -> bool:
    return get_extension(filename) in ALLOWED_EXTENSIONS


def validate_file_size(size: int) -> None:
    if size > MAX_FILE_SIZE:
        raise ValueError(
            f"File exceeds maximum size ({MAX_FILE_SIZE / (1024 * 1024):.0f} MB)"
        )


# ---------------------------------------------------------------------
# Checksums
# ---------------------------------------------------------------------


def calculate_sha256(file: BinaryIO) -> str:
    """
    Calculate SHA256 hash.

    File pointer is restored after reading.
    """
    file.seek(0)

    digest = hashlib.sha256()

    while chunk := file.read(8192):
        digest.update(chunk)

    file.seek(0)

    return digest.hexdigest()


def calculate_md5(file: BinaryIO) -> str:
    """
    Calculate MD5 hash.
    """
    file.seek(0)

    digest = hashlib.md5()

    while chunk := file.read(8192):
        digest.update(chunk)

    file.seek(0)

    return digest.hexdigest()


# ---------------------------------------------------------------------
# Human Readable File Size
# ---------------------------------------------------------------------


def human_file_size(size: int) -> str:
    """
    Convert bytes into readable string.
    """
    units = ["B", "KB", "MB", "GB", "TB"]

    value = float(size)

    for unit in units:
        if value < 1024:
            return f"{value:.2f} {unit}"
        value /= 1024

    return f"{value:.2f} PB"


# ---------------------------------------------------------------------
# Slugs
# ---------------------------------------------------------------------


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


# ---------------------------------------------------------------------
# File Metadata
# ---------------------------------------------------------------------


def extract_basic_metadata(filepath: str) -> dict:
    """
    Extract filesystem metadata.
    """
    stat = os.stat(filepath)

    return {
        "size": stat.st_size,
        "created": stat.st_ctime,
        "modified": stat.st_mtime,
    }


# ---------------------------------------------------------------------
# Duplicate Detection
# ---------------------------------------------------------------------


def is_same_checksum(hash1: str, hash2: str) -> bool:
    return hash1.lower() == hash2.lower()


# ---------------------------------------------------------------------
# File Type Helpers
# ---------------------------------------------------------------------


def is_pdf(filename: str) -> bool:
    return get_extension(filename) == ".pdf"


def is_image(filename: str) -> bool:
    return get_extension(filename) in {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".bmp",
        ".webp",
    }


def is_word(filename: str) -> bool:
    return get_extension(filename) in {
        ".doc",
        ".docx",
    }


def is_excel(filename: str) -> bool:
    return get_extension(filename) in {
        ".xls",
        ".xlsx",
        ".csv",
    }


def is_powerpoint(filename: str) -> bool:
    return get_extension(filename) in {
        ".ppt",
        ".pptx",
    }


def is_text(filename: str) -> bool:
    return get_extension(filename) == ".txt"