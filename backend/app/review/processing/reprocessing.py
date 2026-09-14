from __future__ import annotations

from typing import Callable, Dict, Any, Optional


class ReprocessingManager:
    """
    Handles document reprocessing after review.
    """

    def __init__(self, processor: Callable[[str], Dict[str, Any]]):
        """
        processor:
            Callable that accepts document_id
            and returns processing result.
        """
        self.processor = processor

    def should_reprocess(
        self,
        approval_status: str,
        corrections_exist: bool,
    ) -> bool:
        """
        Decide whether document should be reprocessed.
        """
        return (
            approval_status.lower() == "approved"
            and corrections_exist
        )

    def reprocess(
        self,
        document_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Trigger processing pipeline again.
        """
        return self.processor(document_id)

    def process_after_review(
        self,
        document_id: str,
        approval_status: str,
        corrections_exist: bool,
    ) -> Optional[Dict[str, Any]]:
        """
        Reprocess only if required.
        """
        if self.should_reprocess(
            approval_status,
            corrections_exist,
        ):
            return self.reprocess(document_id)

        return None