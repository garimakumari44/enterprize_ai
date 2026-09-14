from datetime import datetime, timedelta
from typing import Optional


class NodeTimeout:
    """
    Represents timeout configuration for a single workflow node.

    Each node may define its own timeout, allowing long-running
    operations (e.g. LLM calls) to have different limits than
    fast operations (e.g. variable assignment).
    """

    DEFAULT_TIMEOUT_SECONDS = 300  # 5 minutes

    def __init__(
        self,
        timeout_seconds: Optional[int] = None,
    ):
        self.timeout_seconds = (
            timeout_seconds
            if timeout_seconds is not None
            else self.DEFAULT_TIMEOUT_SECONDS
        )

    @property
    def timeout_delta(self) -> timedelta:
        """
        Timeout represented as a timedelta.
        """
        return timedelta(seconds=self.timeout_seconds)

    def has_timed_out(
        self,
        started_at: datetime,
        now: Optional[datetime] = None,
    ) -> bool:
        """
        Determine whether the node execution exceeded
        its configured timeout.
        """
        now = now or datetime.utcnow()

        return now >= started_at + self.timeout_delta

    def remaining_seconds(
        self,
        started_at: datetime,
        now: Optional[datetime] = None,
    ) -> int:
        """
        Remaining seconds before timeout.
        """
        now = now or datetime.utcnow()

        remaining = (
            started_at + self.timeout_delta - now
        ).total_seconds()

        return max(0, int(remaining))

    def elapsed_seconds(
        self,
        started_at: datetime,
        now: Optional[datetime] = None,
    ) -> int:
        """
        Number of elapsed execution seconds.
        """
        now = now or datetime.utcnow()

        return int(
            (now - started_at).total_seconds()
        )

    def __repr__(self) -> str:
        return (
            f"NodeTimeout("
            f"timeout_seconds={self.timeout_seconds})"
        )