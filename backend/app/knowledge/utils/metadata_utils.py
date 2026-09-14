from __future__ import annotations

from datetime import datetime
from typing import Any, Dict


class MetadataUtils:
    """
    Metadata helper utilities.
    """

    @staticmethod
    def add_timestamp(metadata: Dict[str, Any]) -> Dict[str, Any]:
        metadata["timestamp"] = datetime.utcnow().isoformat()
        return metadata

    @staticmethod
    def merge(
        base: Dict[str, Any],
        extra: Dict[str, Any],
    ) -> Dict[str, Any]:

        merged = base.copy()
        merged.update(extra)
        return merged

    @staticmethod
    def ensure_defaults(
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:

        defaults = {
            "source": "unknown",
            "language": "en",
            "tags": [],
        }

        merged = defaults.copy()
        merged.update(metadata)

        return merged

    @staticmethod
    def filter_none(
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:

        return {
            k: v
            for k, v in metadata.items()
            if v is not None
        }