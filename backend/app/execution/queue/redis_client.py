"""
Redis client configuration.

Provides Redis connection management
for the workflow execution queue system.
"""

from __future__ import annotations

from functools import lru_cache

import redis

from app.core.config import settings


class RedisClient:
    """
    Redis connection wrapper.

    Used by:
        - Broker
        - Queue Manager
        - Workers
        - Metrics
    """

    def __init__(self) -> None:

        self.client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=False,
            socket_connect_timeout=5,
            socket_timeout=5,
            health_check_interval=30,
        )


    def get_client(self) -> redis.Redis:
        """
        Return Redis connection instance.
        """

        return self.client


    def ping(self) -> bool:
        """
        Check Redis availability.
        """

        try:
            return bool(self.client.ping())

        except redis.RedisError:
            return False


    def close(self) -> None:
        """
        Close Redis connection pool.
        """

        self.client.close()



@lru_cache()
def get_redis_client() -> redis.Redis:
    """
    Singleton Redis client.

    Prevents creating multiple
    Redis connection pools.

    Usage:

        redis = get_redis_client()

    """

    redis_client = RedisClient()

    return redis_client.get_client()