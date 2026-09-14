from app.core.redis import redis_client


def check_redis() -> bool:
    try:
        return redis_client.ping()
    except Exception:
        return False