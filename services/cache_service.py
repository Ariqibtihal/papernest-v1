"""
Search Cache Service for PaperLens

Provides caching for search results with:
- Redis backend (persistent, scalable)
- In-memory fallback (when Redis unavailable)
- Automatic TTL expiration
- JSON serialization for PaperDTO objects

Configuration:
- REDIS_URL: Redis connection URL (optional)
- CACHE_TTL_SECONDS: Cache TTL in seconds (default: 3600)
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from loguru import logger

from schemas.paper import PaperDTO


class SearchCache:
    """
    Hybrid search cache with Redis backend and in-memory fallback.

    Features:
    - Automatic Redis connection with fallback
    - TTL-based expiration
    - LRU eviction for in-memory cache
    - PaperDTO serialization/deserialization
    """

    def __init__(self, ttl_seconds: int = 3600, max_entries: int = 1000):
        """
        Initialize search cache.

        Args:
            ttl_seconds: Time to live in seconds
            max_entries: Maximum entries for in-memory fallback
        """
        self._redis = None
        self._connected = False
        self._fallback_cache: dict[str, dict[str, Any]] = {}
        self._ttl = ttl_seconds
        self._max_entries = max_entries

        self._try_connect_redis()

    def _try_connect_redis(self):
        """Try to connect to Redis."""
        try:
            import redis.asyncio as redis

            from app.config import get_settings

            settings = get_settings()
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
            logger.info("Connected to Redis for search cache")

        except ImportError:
            logger.info("redis package not installed, using in-memory cache")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}, using in-memory cache")

    def _make_key(self, query: str, filters: dict[str, Any], sort_by: str) -> str:
        """Create cache key from query parameters."""
        params = {"query": query.lower().strip(), "filters": filters, "sort_by": sort_by}
        key_hash = hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()[:32]
        return f"search:{key_hash}"

    def get(
        self, query: str, filters: dict[str, Any], sort_by: str
    ) -> tuple[list[PaperDTO], int] | None:
        """
        Get cached search results.

        Args:
            query: Search query
            filters: Search filters
            sort_by: Sort option

        Returns:
            (papers, total) tuple or None if not cached
        """
        key = self._make_key(query, filters, sort_by)

        # Try Redis first
        if self._connected and self._redis:
            try:
                # Note: This is a sync wrapper for async Redis
                # In production, use async properly
                import asyncio

                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an async context, use sync fallback
                    return self._get_fallback(key)

                value = loop.run_until_complete(self._redis.get(key))
                if value:
                    return self._deserialize(value)
                return None
            except Exception as e:
                logger.debug(f"Redis get failed: {e}")

        # Fallback to in-memory
        return self._get_fallback(key)

    def _get_fallback(self, key: str) -> tuple[list[PaperDTO], int] | None:
        """Get from in-memory fallback cache."""
        entry = self._fallback_cache.get(key)
        if entry is None:
            return None
        if time.monotonic() - entry["ts"] > self._ttl:
            del self._fallback_cache[key]
            return None
        return entry["results"], entry["total"]

    def set(
        self, query: str, filters: dict[str, Any], sort_by: str, results: list[PaperDTO], total: int
    ) -> None:
        """
        Cache search results.

        Args:
            query: Search query
            filters: Search filters
            sort_by: Sort option
            results: List of PaperDTO
            total: Total result count
        """
        key = self._make_key(query, filters, sort_by)
        serialized = self._serialize(results, total)

        # Try Redis first
        if self._connected and self._redis:
            try:
                import asyncio

                loop = asyncio.get_event_loop()
                if not loop.is_running():
                    loop.run_until_complete(self._redis.set(key, serialized, ex=self._ttl))
                    return
            except Exception as e:
                logger.debug(f"Redis set failed: {e}")

        # Fallback to in-memory
        self._fallback_cache[key] = {
            "results": results,
            "total": total,
            "ts": time.monotonic(),
        }
        self._evict_fallback()

    def _serialize(self, results: list[PaperDTO], total: int) -> str:
        """Serialize search results to JSON."""
        papers_data = [p.model_dump() for p in results]
        value = {
            "results": papers_data,
            "total": total,
        }
        return json.dumps(value, default=str)

    def _deserialize(self, data: str) -> tuple[list[PaperDTO], int]:
        """Deserialize search results from JSON."""
        try:
            value = json.loads(data)
            papers_data = value.get("results", [])
            papers = [PaperDTO(**p) for p in papers_data]
            total = value.get("total", 0)
            return papers, total
        except Exception as e:
            logger.debug(f"Failed to deserialize cache: {e}")
            return [], 0

    def _evict_fallback(self) -> None:
        """Evict old entries from in-memory cache."""
        if len(self._fallback_cache) <= self._max_entries:
            return

        # Remove expired entries
        now = time.monotonic()
        expired = [k for k, v in self._fallback_cache.items() if now - v["ts"] > self._ttl]
        for k in expired:
            del self._fallback_cache[k]

        # If still over limit, remove oldest
        if len(self._fallback_cache) > self._max_entries:
            sorted_entries = sorted(self._fallback_cache.items(), key=lambda x: x[1]["ts"])
            for k, _ in sorted_entries[: len(self._fallback_cache) - self._max_entries]:
                del self._fallback_cache[k]

    def clear(self) -> None:
        """Clear all cache entries."""
        if self._connected and self._redis:
            try:
                import asyncio

                loop = asyncio.get_event_loop()
                if not loop.is_running():
                    loop.run_until_complete(self._redis.flushdb())
                    return
            except Exception as e:
                logger.debug(f"Redis clear failed: {e}")

        self._fallback_cache.clear()

    @property
    def size(self) -> int:
        """Get number of cached entries."""
        if self._connected and self._redis:
            try:
                import asyncio

                loop = asyncio.get_event_loop()
                if not loop.is_running():
                    return loop.run_until_complete(self._redis.dbsize())
            except Exception:
                pass
        return len(self._fallback_cache)

    @property
    def is_connected(self) -> bool:
        """Check if Redis is connected."""
        return self._connected


# Module-level singleton
_search_cache: SearchCache | None = None


def get_search_cache() -> SearchCache:
    """Get the singleton SearchCache instance."""
    global _search_cache
    if _search_cache is None:
        from app.config import get_settings

        try:
            settings = get_settings()
            ttl = settings.cache_ttl_seconds
        except Exception:
            ttl = 3600
        _search_cache = SearchCache(ttl_seconds=ttl, max_entries=1000)
    return _search_cache
