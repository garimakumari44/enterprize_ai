from datetime import datetime, timedelta


class ExponentialBackoff:
    """
    Calculates retry delays using exponential backoff.

    Example:

    attempt 1 -> 5 seconds
    attempt 2 -> 10 seconds
    attempt 3 -> 20 seconds
    attempt 4 -> 40 seconds

    Formula:

    delay = initial_delay * (2 ** (attempt - 1))
    """


    def __init__(
        self,
        initial_delay: int = 5,
        max_delay: int = 300
    ):
        """
        Args:
            initial_delay:
                Starting delay in seconds.

            max_delay:
                Maximum allowed delay.
        """

        self.initial_delay = initial_delay

        self.max_delay = max_delay



    def calculate_delay(
        self,
        attempt_number: int
    ) -> int:
        """
        Calculate delay before next retry.

        Args:
            attempt_number:
                Current retry attempt.

        Returns:
            Delay in seconds.
        """

        if attempt_number <= 0:
            raise ValueError(
                "Attempt number must be greater than zero"
            )


        delay = (
            self.initial_delay *
            (2 ** (attempt_number - 1))
        )


        return min(
            delay,
            self.max_delay
        )



    def next_retry_time(
        self,
        attempt_number: int
    ) -> datetime:
        """
        Returns when the next retry should execute.
        """

        delay = self.calculate_delay(
            attempt_number
        )


        return datetime.utcnow() + timedelta(
            seconds=delay
        )



    def get_schedule(
        self,
        attempts: int
    ) -> list[dict]:
        """
        Generates retry schedule.

        Example:

        [
          {
            "attempt":1,
            "delay":5
          },
          {
            "attempt":2,
            "delay":10
          }
        ]
        """

        schedule = []


        for attempt in range(
            1,
            attempts + 1
        ):

            schedule.append(
                {
                    "attempt": attempt,
                    "delay_seconds":
                        self.calculate_delay(
                            attempt
                        )
                }
            )


        return schedule