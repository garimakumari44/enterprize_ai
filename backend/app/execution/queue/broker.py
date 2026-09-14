"""
Redis message broker.

Provides a simple interface for publishing and consuming workflow jobs.
"""

from __future__ import annotations

from typing import Optional

from redis import Redis

from .redis_client import get_redis_client


class Broker:
    """
    Message broker backed by Redis.

    Responsible only for moving serialized jobs
    between producers and workers.
    """

    def __init__(self, redis: Optional[Redis] = None) -> None:
        self.redis = redis or get_redis_client()

    def publish(self, queue_name: str, payload: str) -> int:
        """
        Push a serialized job onto a queue.

        Returns:
            Queue length after push.
        """
        return self.redis.rpush(queue_name, payload)

    def consume(
        self,
        queue_name: str,
        timeout: int = 0,
    ) -> Optional[str]:
        """
        Block until a job becomes available.

        Args:
            queue_name:
                Redis list name.

            timeout:
                Seconds to wait.
                0 means wait forever.

        Returns:
            Serialized job payload or None.
        """
        result = self.redis.blpop(queue_name, timeout=timeout)

        if result is None:
            return None

        _, payload = result
        return payload.decode("utf-8")

    def requeue(
        self,
        queue_name: str,
        payload: str,
    ) -> int:
        """
        Push a job back onto the queue.
        """
        return self.redis.lpush(queue_name, payload)

    def delete(
        self,
        queue_name: str,
    ) -> int:
        """
        Delete an entire queue.
        """
        return self.redis.delete(queue_name)

    def size(
        self,
        queue_name: str,
    ) -> int:
        """
        Return queue length.
        """
        return self.redis.llen(queue_name)

    def exists(
        self,
        queue_name: str,
    ) -> bool:
        """
        Check whether a queue exists.
        """
        return bool(self.redis.exists(queue_name))

    def ping(self) -> bool:
        """
        Check broker connectivity.
        """
        return bool(self.redis.ping())