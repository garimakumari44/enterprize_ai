from datetime import datetime, timedelta
from typing import Optional


class WorkflowTimeout:
    """
    Represents timeout configuration and checks
    for an entire workflow execution.
    """

    def __init__(
        self,
        timeout_seconds: int = 3600
    ):
        self.timeout_seconds = timeout_seconds

    @property
    def timeout_delta(self) -> timedelta:
        return timedelta(seconds=self.timeout_seconds)

    def has_timed_out(
        self,
        started_at: datetime,
        now: Optional[datetime] = None,
    ) -> bool:
        """
        Returns True if workflow exceeded timeout.
        """

        now = now or datetime.utcnow()

        return now >= started_at + self.timeout_delta

    def remaining_seconds(
        self,
        started_at: datetime,
        now: Optional[datetime] = None,
    ) -> int:
        """
        Remaining time before timeout.
        """

        now = now or datetime.utcnow()

        remaining = (
            started_at + self.timeout_delta - now
        ).total_seconds()

        return max(0, int(remaining))