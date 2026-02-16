"""In-memory caching layer for API responses.

Provides a lightweight, async-compatible cache with configurable TTL per key,
automatic expiration, cache invalidation by prefix, and ETag support.

Architecture:
- Dict-based in-memory storage (no external dependencies)
- Per-key TTL configuration
- Prefix-based invalidation for related resource groups
- Cache decorator for easy endpoint integration
- Cache stats endpoint for monitoring
- ETag generation via content hashing

Usage:
    from app.core.cache import api_cache, cached_response, invalidate_cache

    # As decorator on route handler (returns cached JSON + headers)
    @router.get("/templates")
    @cached_response(prefix="templates", ttl=3600)
    async def list_templates(...):
        ...

    # Manual invalidation on write operations
    @router.post("/templates")
    async def create_template(...):
        result = ...
        invalidate_cache("templates")
        return result
"""

import hashlib
import json
import logging
import time
from functools import wraps
from typing import Any, Optional

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class CacheEntry:
    """A single cached value with metadata."""

    __slots__ = ("value", "etag", "created_at", "ttl", "hits")

    def __init__(self, value: Any, etag: str, ttl: int):
        self.value = value
        self.etag = etag
        self.created_at = time.monotonic()
        self.ttl = ttl
        self.hits = 0

    @property
    def is_expired(self) -> bool:
        return (time.monotonic() - self.created_at) >= self.ttl

    @property
    def age_seconds(self) -> int:
        return int(time.monotonic() - self.created_at)

    @property
    def remaining_ttl(self) -> int:
        return max(0, self.ttl - self.age_seconds)


class APICache:
    """In-memory cache for API responses.

    Features:
    - Configurable TTL per cache key
    - Prefix-based invalidation (e.g., invalidate all "templates:*" entries)
    - ETag generation for HTTP caching headers
    - Stats tracking (hits, misses, evictions)
    """

    # Default TTL values per prefix (in seconds)
    DEFAULT_TTLS = {
        "templates": 3600,       # 1 hour - templates rarely change
        "analytics": 900,        # 15 minutes - analytics aggregations
        "dashboard": 300,        # 5 minutes - dashboard data
        "categories": 900,       # 15 minutes
        "platforms": 900,        # 15 minutes
        "countries": 900,        # 15 minutes
        "frequency": 900,        # 15 minutes
        "goals": 300,            # 5 minutes
        "content_mix": 900,      # 15 minutes
        "overview": 300,         # 5 minutes
    }

    def __init__(self):
        self._store: dict[str, CacheEntry] = {}
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "invalidations": 0,
            "evictions": 0,
        }

    def _generate_etag(self, data: Any) -> str:
        """Generate ETag from response data."""
        serialized = json.dumps(data, sort_keys=True, default=str)
        return hashlib.md5(serialized.encode()).hexdigest()

    def _build_key(self, prefix: str, params: Optional[dict] = None) -> str:
        """Build a cache key from prefix and optional parameters."""
        if not params:
            return prefix
        # Sort params for consistent key generation
        sorted_params = sorted(
            (k, v) for k, v in params.items()
            if v is not None
        )
        if not sorted_params:
            return prefix
        param_str = "&".join(f"{k}={v}" for k, v in sorted_params)
        return f"{prefix}:{param_str}"

    def get(self, key: str) -> Optional[CacheEntry]:
        """Get a cached entry if it exists and is not expired."""
        entry = self._store.get(key)
        if entry is None:
            self._stats["misses"] += 1
            return None
        if entry.is_expired:
            del self._store[key]
            self._stats["evictions"] += 1
            self._stats["misses"] += 1
            return None
        entry.hits += 1
        self._stats["hits"] += 1
        return entry

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> CacheEntry:
        """Store a value in the cache."""
        prefix = key.split(":")[0]
        effective_ttl = ttl or self.DEFAULT_TTLS.get(prefix, 300)
        etag = self._generate_etag(value)
        entry = CacheEntry(value=value, etag=etag, ttl=effective_ttl)
        self._store[key] = entry
        self._stats["sets"] += 1
        return entry

    def invalidate(self, prefix: str) -> int:
        """Invalidate all cache entries matching a prefix.

        Args:
            prefix: The prefix to match (e.g., "templates" invalidates
                    "templates", "templates:category=foo", etc.)

        Returns:
            Number of entries invalidated.
        """
        keys_to_remove = [
            k for k in self._store
            if k == prefix or k.startswith(f"{prefix}:")
        ]
        for key in keys_to_remove:
            del self._store[key]
        count = len(keys_to_remove)
        if count > 0:
            self._stats["invalidations"] += count
            logger.info(f"Cache invalidated: {prefix} ({count} entries)")
        return count

    def invalidate_all(self) -> int:
        """Clear the entire cache."""
        count = len(self._store)
        self._store.clear()
        self._stats["invalidations"] += count
        logger.info(f"Cache cleared: {count} entries")
        return count

    def cleanup_expired(self) -> int:
        """Remove all expired entries. Call periodically."""
        expired_keys = [
            k for k, v in self._store.items() if v.is_expired
        ]
        for key in expired_keys:
            del self._store[key]
        self._stats["evictions"] += len(expired_keys)
        return len(expired_keys)

    def get_stats(self) -> dict:
        """Get cache statistics for monitoring."""
        # Cleanup expired entries first
        self.cleanup_expired()

        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = (
            round(self._stats["hits"] / total_requests * 100, 1)
            if total_requests > 0
            else 0.0
        )

        # Group entries by prefix
        prefix_stats = {}
        for key, entry in self._store.items():
            prefix = key.split(":")[0]
            if prefix not in prefix_stats:
                prefix_stats[prefix] = {
                    "count": 0,
                    "total_hits": 0,
                    "ttl": entry.ttl,
                }
            prefix_stats[prefix]["count"] += 1
            prefix_stats[prefix]["total_hits"] += entry.hits

        return {
            "total_entries": len(self._store),
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "hit_rate_percent": hit_rate,
            "sets": self._stats["sets"],
            "invalidations": self._stats["invalidations"],
            "evictions": self._stats["evictions"],
            "prefixes": prefix_stats,
            "default_ttls": self.DEFAULT_TTLS,
        }


# Singleton instance
api_cache = APICache()


def cached_response(prefix: str, ttl: Optional[int] = None):
    """Decorator for caching FastAPI endpoint responses.

    Caches the JSON response and adds Cache-Control / ETag headers.
    Supports If-None-Match header for 304 Not Modified responses.

    The decorated function's keyword arguments are used as cache key params
    (excluding 'db', 'user_id', 'request').

    Args:
        prefix: Cache key prefix (e.g., "templates", "analytics")
        ttl: Optional TTL override in seconds
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request object if present
            request: Optional[Request] = kwargs.get("request")

            # Build cache key from function parameters
            cache_params = {}
            for k, v in kwargs.items():
                if k not in ("db", "request") and v is not None:
                    cache_params[k] = v
            cache_key = api_cache._build_key(prefix, cache_params)

            # Check cache
            entry = api_cache.get(cache_key)

            if entry is not None:
                # Check If-None-Match header for 304
                if request:
                    if_none_match = request.headers.get("if-none-match")
                    if if_none_match and if_none_match.strip('"') == entry.etag:
                        return JSONResponse(
                            status_code=304,
                            content=None,
                            headers={
                                "ETag": f'"{entry.etag}"',
                                "Cache-Control": f"private, max-age={entry.remaining_ttl}",
                                "X-Cache": "HIT",
                            },
                        )

                # Return cached response with headers
                return JSONResponse(
                    content=entry.value,
                    headers={
                        "ETag": f'"{entry.etag}"',
                        "Cache-Control": f"private, max-age={entry.remaining_ttl}",
                        "X-Cache": "HIT",
                        "X-Cache-Age": str(entry.age_seconds),
                    },
                )

            # Cache miss - call the actual function
            result = await func(*args, **kwargs)

            # Cache the result
            effective_ttl = ttl or api_cache.DEFAULT_TTLS.get(prefix, 300)
            new_entry = api_cache.set(cache_key, result, effective_ttl)

            return JSONResponse(
                content=result,
                headers={
                    "ETag": f'"{new_entry.etag}"',
                    "Cache-Control": f"private, max-age={effective_ttl}",
                    "X-Cache": "MISS",
                },
            )

        return wrapper
    return decorator


def invalidate_cache(*prefixes: str) -> int:
    """Invalidate cache entries for one or more prefixes.

    Usage:
        invalidate_cache("templates")
        invalidate_cache("analytics", "dashboard", "overview")
    """
    total = 0
    for prefix in prefixes:
        total += api_cache.invalidate(prefix)
    return total
