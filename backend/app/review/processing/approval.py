from __future__ import annotations

from enum import Enum
from datetime import datetime
from typing import Optional


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ReviewApproval:
    """
    Tracks review approval status.
    """

    def __init__(self, document_id: str):
        self.document_id = document_id
        self.status = ApprovalStatus.PENDING
        self.reviewer: Optional[str] = None
        self.comment: Optional[str] = None
        self.reviewed_at: Optional[datetime] = None

    def approve(
        self,
        reviewer: str,
        comment: Optional[str] = None,
    ) -> None:
        self.status = ApprovalStatus.APPROVED
        self.reviewer = reviewer
        self.comment = comment
        self.reviewed_at = datetime.utcnow()

    def reject(
        self,
        reviewer: str,
        comment: Optional[str] = None,
    ) -> None:
        self.status = ApprovalStatus.REJECTED
        self.reviewer = reviewer
        self.comment = comment
        self.reviewed_at = datetime.utcnow()

    @property
    def is_approved(self) -> bool:
        return self.status == ApprovalStatus.APPROVED

    @property
    def is_rejected(self) -> bool:
        return self.status == ApprovalStatus.REJECTED

    @property
    def is_pending(self) -> bool:
        return self.status == ApprovalStatus.PENDING