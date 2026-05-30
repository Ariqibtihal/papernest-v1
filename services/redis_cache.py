"""
Redis Cache Service for PaperLens

Provides persistent caching using Redis for:
- Search results
- API responses
- User sessions

Features:
- Automatic TTL expiration
- JSON serialization for complex objects
- Fallback to in-memory cache if Redis unavailable
- Connection pooling

Configuration:
- REDIS_URL: Redis connection URL (default: redis://localhost:6379)
- REDIS_CACHE_TTL: Cache TTL in seconds (default: 3600)
"""

from __future__ import annotations

import json
import time
from typing import Any

from loguru import logger

from app.config import get_settings
from schemas.paper import PaperDTO


class RedisCache:
    """
    Redis-based cache with fallback to in-memory cache.

    If Redis is unavailable, falls back to in-memory cache.
    This ensures the application works even without Redis.
    """

    def __init__(self):
        """Initialize Redis cache."""
        self._redis = None
        self._fallback_cache: dict[str, dict[str, Any]] = {}
        self._connected = False
        self._try_connect()

    def _try_connect(self):
        """Try to connect to Redis."""
        try:
            import redis.asyncio as redis

            settings = get_settings()

            # Check if Redis URL is configured
            redis_url = getattr(settings, "redis_url", None)
            if not redis_url:
                logger.info("Redis URL not configured, using in-memory cache")
                return

            self._redis = redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
            )
            self._connected = True
            logger.info(f"Connected to Redis at {redis_url}")

        except ImportError:
            logger.warning("redis package not installed, using in-memory cache")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}, using in-memory cache")

    async def get(self, key: str) -> dict[str, Any] | None:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if self._connected and self._redis:
            try:
                value = await self._redis.get(key)
                if value:
                    return json.loads(value)
                return None
            except Exception as e:
                logger.debug(f"Redis get failed: {e}")
                # Fall back to in-memory cache

        # In-memory fallback
        entry = self._fallback_cache.get(key)
        if entry is None:
            return None
        if time.monotonic() - entry["ts"] > entry.get("ttl", 3600):
            del self._fallback_cache[key]
            return None
        return entry["value"]

    async def set(self, key: str, value: dict[str, Any], ttl: int = 3600) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        if self._connected and self._redis:
            try:
                serialized = json.dumps(value, default=str)
                await self._redis.set(key, serialized, ex=ttl)
                return
            except Exception as e:
                logger.debug(f"Redis set failed: {e}")
                # Fall back to in-memory cache

        # In-memory fallback
        self._fallback_cache[key] = {
            "value": value,
            "ts": time.monotonic(),
            "ttl": ttl,
        }
        self._evict_fallback()

    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        if self._connected and self._redis:
            try:
                await self._redis.delete(key)
                return
            except Exception as e:
                logger.debug(f"Redis delete failed: {e}")

        # In-memory fallback
        self._fallback_cache.pop(key, None)

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if self._connected and self._redis:
            try:
                return await self._redis.exists(key) > 0
            except Exception as e:
                logger.debug(f"Redis exists failed: {e}")

        # In-memory fallback
        return key in self._fallback_cache

    async def clear(self) -> None:
        """Clear all cache entries."""
        if self._connected and self._redis:
            try:
                await self._redis.flushdb()
                return
            except Exception as e:
                logger.debug(f"Redis clear failed: {e}")

        # In-memory fallback
        self._fallback_cache.clear()

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            try:
                await self._redis.close()
            except Exception:
                pass

    def _evict_fallback(self, max_entries: int = 1000) -> None:
        """Evict old entries from in-memory cache."""
        if len(self._fallback_cache) <= max_entries:
            return

        # Remove expired entries
        now = time.monotonic()
        expired = [k for k, v in self._fallback_cache.items() if now - v["ts"] > v.get("ttl", 3600)]
        for k in expired:
            del self._fallback_cache[k]

        # If still over limit, remove oldest
        if len(self._fallback_cache) > max_entries:
            sorted_entries = sorted(self._fallback_cache.items(), key=lambda x: x[1]["ts"])
            for k, _ in sorted_entries[: len(self._fallback_cache) - max_entries]:
                del self._fallback_cache[k]

    @property
    def is_connected(self) -> bool:
        """Check if Redis is connected."""
        return self._connected


# Search-specific cache methods
class SearchRedisCache:
    """
    Search-specific cache that serializes/deserializes PaperDTO objects.
    """

    def __init__(self, redis_cache: RedisCache):
        self._cache = redis_cache

    def _make_key(self, query: str, filters: dict[str, Any], sort_by: str) -> str:
        """Create cache key for search."""
        import hashlib

        params = {"query": query.lower().strip(), "filters": filters, "sort_by": sort_by}
        key_hash = hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()[:32]
        return f"search:{key_hash}"

    async def get(
        self, query: str, filters: dict[str, Any], sort_by: str
    ) -> tuple[list[PaperDTO], int] | None:
        """
        Get cached search results.

        Returns:
            (papers, total) tuple or None if not cached
        """
        key = self._make_key(query, filters, sort_by)
        cached = await self._cache.get(key)

        if cached is None:
            return None

        try:
            papers_data = cached.get("results", [])
            papers = [PaperDTO(**p) for p in papers_data]
            total = cached.get("total", 0)
            return papers, total
        except Exception as e:
            logger.debug(f"Failed to deserialize cached results: {e}")
            return None

    async def set(
        self,
        query: str,
        filters: dict[str, Any],
        sort_by: str,
        papers: list[PaperDTO],
        total: int,
        ttl: int = 3600,
    ) -> None:
        """
        Cache search results.

        Args:
            query: Search query
            filters: Search filters
            sort_by: Sort option
            papers: List of PaperDTO
            total: Total result count
            ttl: Time to live in seconds
        """
        key = self._make_key(query, filters, sort_by)

        try:
            papers_data = [p.model_dump() for p in papers]
            value = {
                "results": papers_data,
                "total": total,
            }
            await self._cache.set(key, value, ttl=ttl)
        except Exception as e:
            logger.debug(f"Failed to cache results: {e}")

    async def invalidate(self, query: str | None = None) -> int:
        """
        Invalidate cached search results.

        Args:
            query: Specific query to invalidate, or None for all

        Returns:
            Number of entries invalidated
        """
        if query is None:
            # Clear all search cache
            if self._cache._connected and self._cache._redis:
                try:
                    keys = []
                    async for key in self._cache._redis.scan_iter("search:*"):
                        keys.append(key)
                    if keys:
                        await self._cache._redis.delete(*keys)
                    return len(keys)
                except Exception as e:
                    logger.debug(f"Failed to clear search cache: {e}")
            return 0

        # Invalidate specific query patterns
        # This is a simple implementation - in production, use Redis tags
        return 0


# Module-level singleton
_redis_cache: RedisCache | None = None
_search_redis_cache: SearchRedisCache | None = None


def get_redis_cache() -> RedisCache:
    """Get the singleton RedisCache instance."""
    global _redis_cache
    if _redis_cache is None:
        _redis_cache = RedisCache()
    return _redis_cache


def get_search_redis_cache() -> SearchRedisCache:
    """Get the singleton SearchRedisCache instance."""
    global _search_redis_cache
    if _search_redis_cache is None:
        _search_redis_cache = SearchRedisCache(get_redis_cache())
    return _search_redis_cache
