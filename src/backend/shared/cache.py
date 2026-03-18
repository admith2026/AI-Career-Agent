"""Redis caching layer for the Career Agent platform.

Provides async Redis client, decorator-based caching, and cache invalidation utilities.
"""

import json
import hashlib
import logging
from functools import wraps
from typing import Any, Callable

import redis.asyncio as aioredis

from shared.config import BaseServiceSettings

logger = logging.getLogger(__name__)

_settings = BaseServiceSettings()
_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Return a shared async Redis client (singleton)."""
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(
            _settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
        )
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis:
        await _redis.close()
        _redis = None


def _make_key(prefix: str, args: tuple, kwargs: dict) -> str:
    """Build a deterministic cache key from function arguments."""
    raw = json.dumps({"a": [str(a) for a in args], "k": {k: str(v) for k, v in sorted(kwargs.items())}}, sort_keys=True)
    digest = hashlib.sha256(raw.encode()).hexdigest()[:16]
    return f"cache:{prefix}:{digest}"


def cached(prefix: str, ttl: int = 300):
    """Decorator that caches the JSON-serialisable return value in Redis.

    Args:
        prefix: Cache key namespace (e.g. ``jobs:list``).
        ttl: Time-to-live in seconds (default 5 min).
    """

    def decorator(fn: Callable):
        @wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            r = await get_redis()
            key = _make_key(prefix, args, kwargs)
            try:
                hit = await r.get(key)
                if hit is not None:
                    return json.loads(hit)
            except Exception:
                logger.debug("Cache read failed for %s", key)

            result = await fn(*args, **kwargs)

            try:
                await r.set(key, json.dumps(result, default=str), ex=ttl)
            except Exception:
                logger.debug("Cache write failed for %s", key)

            return result

        return wrapper

    return decorator


async def invalidate(pattern: str) -> int:
    """Delete all keys matching a glob pattern (e.g. ``cache:jobs:*``)."""
    r = await get_redis()
    keys = []
    async for key in r.scan_iter(match=pattern, count=200):
        keys.append(key)
    if keys:
        await r.delete(*keys)
    return len(keys)


async def cache_get(key: str) -> Any | None:
    r = await get_redis()
    val = await r.get(key)
    return json.loads(val) if val else None


async def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    r = await get_redis()
    await r.set(key, json.dumps(value, default=str), ex=ttl)
