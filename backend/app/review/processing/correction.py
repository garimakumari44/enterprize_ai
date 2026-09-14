from __future__ import annotations

from datetime import datetime
from typing import Dict, Any, Optional


class DocumentCorrection:
    """
    Represents manual corrections performed by a reviewer.
    """

    def __init__(
        self,
        document_id: str,
        reviewer: str,
    ) -> None:
        self.document_id = document_id
        self.reviewer = reviewer
        self.created_at = datetime.utcnow()
        self._changes: Dict[str, Dict[str, Any]] = {}

    @property
    def changes(self) -> Dict[str, Dict[str, Any]]:
        return self._changes

    def add_correction(
        self,
        field: str,
        old_value: Any,
        new_value: Any,
        confidence: Optional[float] = None,
    ) -> None:
        """
        Record a corrected field.
        """
        self._changes[field] = {
            "old_value": old_value,
            "new_value": new_value,
            "confidence": confidence,
        }

    def has_changes(self) -> bool:
        return bool(self._changes)

    def apply(self, extracted_fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply corrections to extracted fields.
        """
        updated = dict(extracted_fields)

        for field, values in self._changes.items():
            updated[field] = values["new_value"]

        return updated

    def summary(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "reviewer": self.reviewer,
            "created_at": self.created_at.isoformat(),
            "changes": self._changes,
        }