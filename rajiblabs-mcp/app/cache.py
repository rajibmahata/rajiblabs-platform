from __future__ import annotations

import json
import logging
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

_cache: dict[str, Any] = {}


async def cache_get(namespace: str, key: str) -> Any | None:
    if not settings.CACHE_ENABLED:
        return None

    try:
        from app.redis import cache_get as redis_get
        return await redis_get(namespace, key)
    except Exception:
        pass

    full_key = f"{namespace}:{key}"
    return _cache.get(full_key)


async def cache_set(namespace: str, key: str, value: Any, ttl: int | None = None) -> None:
    if not settings.CACHE_ENABLED:
        return

    try:
        from app.redis import cache_set as redis_set
        await redis_set(namespace, key, value, ttl)
        return
    except Exception:
        pass

    full_key = f"{namespace}:{key}"
    _cache[full_key] = value


async def cache_invalidate(namespace: str, key: str) -> None:
    try:
        from app.redis import cache_invalidate as redis_inv
        await redis_inv(namespace, key)
    except Exception:
        pass

    full_key = f"{namespace}:{key}"
    _cache.pop(full_key, None)


async def cache_invalidate_pattern(namespace: str, pattern: str = "*") -> int:
    try:
        from app.redis import cache_invalidate_pattern as redis_inv
        return await redis_inv(namespace, pattern)
    except Exception:
        pass

    removed = 0
    prefix = f"{namespace}:"
    keys_to_remove = [k for k in _cache if k.startswith(prefix)]
    for k in keys_to_remove:
        del _cache[k]
        removed += 1
    return removed
