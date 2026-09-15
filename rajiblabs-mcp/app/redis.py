from __future__ import annotations

import logging
from typing import Any

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)

_redis: aioredis.Redis | None = None

KEY_PREFIX = "rajiblabs:mcp"


async def connect_redis() -> None:
    global _redis
    try:
        _redis = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5,
        )
        await _redis.ping()
        logger.info("Redis connected: %s", settings.REDIS_URL)
    except Exception as e:
        logger.warning("Redis unavailable, caching disabled: %s", e)
        _redis = None


async def disconnect_redis() -> None:
    global _redis
    if _redis:
        await _redis.close()
        _redis = None
        logger.info("Redis disconnected")


def get_redis() -> aioredis.Redis | None:
    return _redis


def _ns_key(namespace: str, key: str) -> str:
    return f"{KEY_PREFIX}:{namespace}:{key}"


async def cache_get(namespace: str, key: str) -> Any | None:
    if not settings.CACHE_ENABLED or _redis is None:
        return None
    try:
        val = await _redis.get(_ns_key(namespace, key))
        if val is not None:
            import json
            return json.loads(val)
    except Exception as e:
        logger.debug("cache_get error: %s", e)
    return None


async def cache_set(namespace: str, key: str, value: Any, ttl: int | None = None) -> None:
    if not settings.CACHE_ENABLED or _redis is None:
        return
    try:
        import json
        ttl = ttl or settings.CACHE_TTL_SECONDS
        await _redis.set(_ns_key(namespace, key), json.dumps(value, default=str), ex=ttl)
    except Exception as e:
        logger.debug("cache_set error: %s", e)


async def cache_invalidate(namespace: str, key: str) -> None:
    if not settings.CACHE_ENABLED or _redis is None:
        return
    try:
        await _redis.delete(_ns_key(namespace, key))
    except Exception as e:
        logger.debug("cache_invalidate error: %s", e)


async def cache_invalidate_pattern(namespace: str, pattern: str = "*") -> int:
    if not settings.CACHE_ENABLED or _redis is None:
        return 0
    try:
        full_pattern = _ns_key(namespace, pattern)
        keys = []
        async for key in _redis.scan_iter(match=full_pattern, count=100):
            keys.append(key)
        if keys:
            return await _redis.delete(*keys)
    except Exception as e:
        logger.debug("cache_invalidate_pattern error: %s", e)
    return 0
