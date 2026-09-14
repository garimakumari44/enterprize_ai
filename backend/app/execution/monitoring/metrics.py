"""
Application Metrics Collector.

Tracks:
- Workflow executions
- Worker activity
- Queue statistics
- Runtime performance

Designed to be extended with Prometheus/OpenTelemetry.
"""

from collections import defaultdict
from threading import Lock
from time import time


class MetricsCollector:
    """
    Thread-safe in-memory metrics collector.

    Used across workers and execution engine.
    """

    def __init__(self):
        self.lock = Lock()

        # Counters
        self.counters = defaultdict(int)

        # Gauges
        self.gauges = defaultdict(int)

        # Histograms / timing values
        self.timings = defaultdict(list)

        # Start time
        self.started_at = time()


    # -------------------------------------------------
    # Counter Metrics
    # -------------------------------------------------

    def increment(
        self,
        metric_name: str,
        value: int = 1
    ):
        """
        Increment a counter metric.

        Example:

        metrics.increment(
            "workflow.execution.completed"
        )
        """

        with self.lock:
            self.counters[metric_name] += value


    def decrement(
        self,
        metric_name: str,
        value: int = 1
    ):
        """
        Decrease a counter metric.
        """

        with self.lock:
            self.counters[metric_name] -= value


    # -------------------------------------------------
    # Gauge Metrics
    # -------------------------------------------------

    def set_gauge(
        self,
        metric_name: str,
        value: int
    ):
        """
        Set current value.

        Example:

        active_workers = 5
        """

        with self.lock:
            self.gauges[metric_name] = value


    def get_gauge(
        self,
        metric_name: str
    ):
        return self.gauges.get(
            metric_name,
            0
        )


    # -------------------------------------------------
    # Timing Metrics
    # -------------------------------------------------

    def record_time(
        self,
        metric_name: str,
        duration: float
    ):
        """
        Store execution duration.

        Example:

        workflow.execution.duration
        """

        with self.lock:
            self.timings[metric_name].append(
                duration
            )


    def get_average_time(
        self,
        metric_name: str
    ):
        """
        Calculate average duration.
        """

        values = self.timings.get(
            metric_name,
            []
        )

        if not values:
            return 0

        return sum(values) / len(values)


    # -------------------------------------------------
    # Snapshot
    # -------------------------------------------------

    def snapshot(self):
        """
        Return current metrics state.

        Used by monitoring APIs.
        """

        with self.lock:

            return {
                "uptime_seconds": (
                    time() - self.started_at
                ),

                "counters": dict(
                    self.counters
                ),

                "gauges": dict(
                    self.gauges
                ),

                "timings": {
                    key: {
                        "count": len(values),
                        "average": (
                            sum(values) / len(values)
                            if values else 0
                        )
                    }
                    for key, values
                    in self.timings.items()
                }
            }


# -------------------------------------------------
# Global Metrics Instance
# -------------------------------------------------

metrics = MetricsCollector()