"""Global In-Memory Cache - Application Scoped with Redis Support."""

import time
import threading
import json
from typing import Any, Dict, Optional, Tuple
from src.observability.logger import get_logger
from src.security.config import security_config

try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = get_logger("infrastructure.cache")


class GlobalMemoryCache:
    """
    Hybrid Cache: Uses Redis if configured/available, falls back to in-memory.
    Thread-safe for in-memory operations.
    Async-compatible for Redis.
    """

    def __init__(self):
        self._memory_cache: Dict[str, Tuple[Any, float]] = {}  # key -> (value, expiry)
        self._lock = threading.RLock()
        self._redis: Optional[redis.Redis] = None
        self._use_redis = False
        self._redis_backoff_seconds = 30
        self._redis_unavailable_until = 0.0
        self._redis_error_logged = False

        if REDIS_AVAILABLE and security_config.ENABLE_CACHING:
            try:
                self._redis = redis.Redis(
                    host=security_config.REDIS_HOST,
                    port=security_config.REDIS_PORT,
                    password=security_config.REDIS_PASSWORD or None,
                    ssl=security_config.REDIS_SSL,
                    decode_responses=True,
                    socket_connect_timeout=0.25,
                    socket_timeout=0.25,
                )
                self._use_redis = True
                logger.info(
                    f"Redis Cache Initialized at {security_config.REDIS_HOST}:{security_config.REDIS_PORT}"
                )
            except Exception as e:
                logger.warning(
                    f"Redis initialization failed, falling back to memory: {e}"
                )

    def _redis_ready(self) -> bool:
        """Return whether Redis should be attempted for this operation."""
        return (
            self._use_redis
            and self._redis is not None
            and time.time() >= self._redis_unavailable_until
        )

    def _mark_redis_temporarily_unavailable(self) -> None:
        """Avoid repeated expensive Redis connection attempts when service is down."""
        self._redis_unavailable_until = time.time() + self._redis_backoff_seconds

    def _handle_redis_error(self, operation: str, key: str, error: Exception) -> None:
        """
        Centralized Redis failure handling.
        If the server refuses the connection, disable Redis for the process to avoid
        repeated multi-second retries on every request.
        """
        err = str(error)
        key_info = f" for {key}" if key else ""
        if not self._redis_error_logged:
            logger.warning(
                f"Redis {operation} failed{key_info}: {error}. Falling back to memory."
            )
            self._redis_error_logged = True

        if (
            "refused" in err.lower()
            or "connecting to" in err.lower()
            or "connectionerror" in err.lower()
        ):
            self._use_redis = False
            logger.warning(
                "Redis appears unavailable; disabling Redis cache for this process."
            )
            return

        self._mark_redis_temporarily_unavailable()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache (Redis or Memory)."""
        if not security_config.ENABLE_CACHING:
            return None

        # 1. Try Redis
        if self._redis_ready():
            try:
                val = await self._redis.get(key)
                if val:
                    try:
                        return json.loads(val)
                    except json.JSONDecodeError:
                        return val
                return None
            except Exception as e:
                self._handle_redis_error("get", key, e)

        # 2. Fallback to Memory
        with self._lock:
            if key not in self._memory_cache:
                return None
            value, expiry = self._memory_cache[key]
            if time.time() > expiry:
                del self._memory_cache[key]
                return None
            return value

    async def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        """Set value in cache (Redis or Memory)."""
        if not security_config.ENABLE_CACHING:
            return

        # 1. Try Redis
        if self._redis_ready():
            try:
                val_str = json.dumps(value) if not isinstance(value, str) else value
                await self._redis.set(key, val_str, ex=ttl_seconds)
                return
            except Exception as e:
                self._handle_redis_error("set", key, e)

        # 2. Fallback to Memory
        with self._lock:
            self._memory_cache[key] = (value, time.time() + ttl_seconds)

    async def delete(self, key: str) -> None:
        """Delete key."""
        if self._redis_ready():
            try:
                await self._redis.delete(key)
            except Exception as e:
                self._handle_redis_error("delete", key, e)

        with self._lock:
            if key in self._memory_cache:
                del self._memory_cache[key]

    async def clear(self) -> None:
        """Clear all keys."""
        if self._redis_ready():
            try:
                await self._redis.flushdb()
            except Exception as e:
                self._handle_redis_error("flush", "", e)

        with self._lock:
            self._memory_cache.clear()

    async def incr(self, key: str) -> int:
        """Atomic increment."""
        if self._redis_ready():
            try:
                return await self._redis.incr(key)
            except Exception as e:
                self._handle_redis_error("incr", key, e)
                # Fallback logic for incr is complex in memory without race conditions across processes
                # Just return 1 if we can't incr safely in distributed mode
                pass

        # Memory fallback (not process-safe, but thread-safe)
        with self._lock:
            val, exp = self._memory_cache.get(key, (0, time.time() + 300))
            if time.time() > exp:
                val = 0

            # If val is dict (from our auth logic), this breaks.
            # Assuming usage for counters only.
            if isinstance(val, int):
                new_val = val + 1
                self._memory_cache[key] = (new_val, exp)
                return new_val
            return 1

    async def expire(self, key: str, ttl_seconds: int) -> None:
        """Set expiry."""
        if self._redis_ready():
            try:
                await self._redis.expire(key, ttl_seconds)
                return
            except Exception as e:
                self._handle_redis_error("expire", key, e)

        with self._lock:
            if key in self._memory_cache:
                val, _ = self._memory_cache[key]
                self._memory_cache[key] = (val, time.time() + ttl_seconds)

    async def ping(self) -> bool:
        """
        Health check for cache.
        Returns True if cache is working (Redis ping or memory check).
        """
        if not security_config.ENABLE_CACHING:
            return False

        if self._redis_ready():
            try:
                return await self._redis.ping()  # type: ignore
            except Exception as e:
                self._handle_redis_error("health-check", "", e)
                return False

        # In-memory cache is always "healthy" if the application is running
        return True


# Singleton instance
global_cache = GlobalMemoryCache()

