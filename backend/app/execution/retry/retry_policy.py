from typing import List, Optional


class RetryPolicy:
    """
    Defines retry behaviour for workflow execution failures.
    """

    VALID_BACKOFF_TYPES = {
        "fixed",
        "exponential"
    }


    def __init__(
        self,
        max_attempts: int = 3,
        backoff_type: str = "exponential",
        initial_delay: int = 5,
        max_delay: int = 300,
        retryable_errors: Optional[List[str]] = None
    ):
        """
        Args:
            max_attempts:
                Maximum number of execution attempts.

            backoff_type:
                Delay strategy.

            initial_delay:
                First retry delay in seconds.

            max_delay:
                Maximum delay cap.

            retryable_errors:
                List of errors allowed for retry.
        """

        if backoff_type not in self.VALID_BACKOFF_TYPES:
            raise ValueError(
                f"Invalid backoff type: {backoff_type}"
            )


        self.max_attempts = max_attempts

        self.backoff_type = backoff_type

        self.initial_delay = initial_delay

        self.max_delay = max_delay

        self.retryable_errors = retryable_errors or []



    def can_retry(
        self,
        attempt_number: int
    ) -> bool:
        """
        Checks whether another retry is allowed.
        """

        return attempt_number < self.max_attempts



    def is_retryable_error(
        self,
        error_type: str
    ) -> bool:
        """
        Determines whether a particular
        error should be retried.
        """

        if not self.retryable_errors:
            return True


        return error_type in self.retryable_errors



    def to_dict(self):
        """
        Serialize policy configuration.
        """

        return {
            "max_attempts": self.max_attempts,
            "backoff_type": self.backoff_type,
            "initial_delay": self.initial_delay,
            "max_delay": self.max_delay,
            "retryable_errors": self.retryable_errors
        }