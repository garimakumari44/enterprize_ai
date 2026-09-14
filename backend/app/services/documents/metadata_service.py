from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Any


class MetadataService:
    """
    Extract metadata from uploaded files.

    Future:
    - PDF metadata
    - Office metadata
    - Image EXIF
    - OCR information
    """

    def extract(self, file_path: str) -> dict[str, Any]:
        path = Path(file_path)

        mime_type, _ = mimetypes.guess_type(path.name)

        return {
            "filename": path.name,
            "extension": path.suffix.lower(),
            "mime_type": mime_type,
            "size": path.stat().st_size,
        }