"""Redis cache for the orchestrator."""

from __future__ import annotations

import json
import logging
from typing import Any

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)

_redis: aioredis.Redis | None = None
KEY_PREFIX = "rajiblabs:orch"


async def connect_redis() -> None:
    global _redis
    try:
        _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=5)
        await _redis.ping()
        logger.info("Orchestrator Redis connected")
    except Exception as e:
        logger.warning("Redis unavailable: %s", e)
        _redis = None


async def disconnect_redis() -> None:
    global _redis
    if _redis:
        await _redis.close()
        _redis = None


async def cache_get(namespace: str, key: str) -> Any | None:
    if _redis is None:
        return None
    try:
        val = await _redis.get(f"{KEY_PREFIX}:{namespace}:{key}")
        return json.loads(val) if val else None
    except Exception:
        return None


async def cache_set(namespace: str, key: str, value: Any, ttl: int = 300) -> None:
    if _redis is None:
        return
    try:
        await _redis.set(f"{KEY_PREFIX}:{namespace}:{key}", json.dumps(value, default=str), ex=ttl)
    except Exception:
        pass


async def cache_invalidate(namespace: str, key: str) -> None:
    if _redis is None:
        return
    try:
        await _redis.delete(f"{KEY_PREFIX}:{namespace}:{key}")
    except Exception:
        pass


async def cache_invalidate_pattern(namespace: str, pattern: str = "*") -> int:
    if _redis is None:
        return 0
    try:
        full = f"{KEY_PREFIX}:{namespace}:{pattern}"
        keys = []
        async for key in _redis.scan_iter(match=full, count=100):
            keys.append(key)
        return await _redis.delete(*keys) if keys else 0
    except Exception:
        return 0
