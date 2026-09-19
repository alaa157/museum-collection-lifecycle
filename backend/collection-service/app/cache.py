import json
import logging

from redis import Redis

from app.core.config import get_settings


logger = logging.getLogger(__name__)
settings = get_settings()

redis_client = Redis.from_url(
    settings.redis_url,
    decode_responses=True,
    socket_connect_timeout=2,
    socket_timeout=2,
)


def get_json(key: str):
    try:
        value = redis_client.get(key)
        return json.loads(value) if value else None
    except Exception:
        logger.exception("Redis read failed for key %s", key)
        return None


def set_json(key: str, value, ttl: int = 30):
    try:
        redis_client.setex(
            key,
            ttl,
            json.dumps(value, default=str),
        )
    except Exception:
        logger.exception("Redis write failed for key %s", key)


def delete_prefix(prefix: str):
    try:
        keys = list(redis_client.scan_iter(match=f"{prefix}*"))
        if keys:
            redis_client.delete(*keys)
    except Exception:
        logger.exception("Redis invalidation failed for prefix %s", prefix)
