import json
import logging
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)


class MemoryBackend:
    def __init__(self):
        self._store: dict[str, tuple[float, str]] = {}

    def get(self, key: str) -> Optional[str]:
        item = self._store.get(key)
        if item is None:
            return None
        expires_at, value = item
        if time.time() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: str, ttl: int):
        self._store[key] = (time.time() + ttl, value)

    def delete(self, key: str):
        self._store.pop(key, None)

    def clear(self):
        self._store.clear()


class RedisBackend:
    def __init__(self, redis_url: str):
        import redis.asyncio as aioredis
        self._client = aioredis.from_url(redis_url, decode_responses=True)

    async def get(self, key: str) -> Optional[str]:
        try:
            return await self._client.get(key)
        except Exception as e:
            logger.warning(f"Redis get error: {e}")
            return None

    async def set(self, key: str, value: str, ttl: int):
        try:
            await self._client.setex(key, ttl, value)
        except Exception as e:
            logger.warning(f"Redis set error: {e}")

    async def delete(self, key: str):
        try:
            await self._client.delete(key)
        except Exception as e:
            logger.warning(f"Redis delete error: {e}")

    async def clear(self):
        try:
            await self._client.flushdb()
        except Exception as e:
            logger.warning(f"Redis flush error: {e}")


class CacheService:
    def __init__(self, redis_url: Optional[str] = None):
        self._memory = MemoryBackend()
        self._redis: Optional[RedisBackend] = None
        if redis_url:
            try:
                self._redis = RedisBackend(redis_url)
                logger.info("Cache: Redis backend initialized")
            except Exception as e:
                logger.warning(f"Cache: Redis unavailable, using memory: {e}")
                self._redis = None

    def _make_key(self, prefix: str, key: str) -> str:
        return f"skycast:{prefix}:{key}"

    def get_sync(self, prefix: str, key: str) -> Optional[Any]:
        cache_key = self._make_key(prefix, key)
        raw = self._memory.get(cache_key)
        if raw is not None:
            try:
                return json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                return None
        return None

    def set_sync(self, prefix: str, key: str, value: Any, ttl: int = 300):
        cache_key = self._make_key(prefix, key)
        try:
            raw = json.dumps(value, default=str)
            self._memory.set(cache_key, raw, ttl)
        except (TypeError, ValueError) as e:
            logger.warning(f"Cache serialization error: {e}")

    async def get(self, prefix: str, key: str) -> Optional[Any]:
        cache_key = self._make_key(prefix, key)
        raw = self._memory.get(cache_key)
        if raw is not None:
            try:
                return json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                return None
        if self._redis:
            raw = await self._redis.get(cache_key)
            if raw is not None:
                self._memory.set(cache_key, raw, 60)
                try:
                    return json.loads(raw)
                except (json.JSONDecodeError, TypeError):
                    return None
        return None

    async def set(self, prefix: str, key: str, value: Any, ttl: int = 300):
        cache_key = self._make_key(prefix, key)
        try:
            raw = json.dumps(value, default=str)
            self._memory.set(cache_key, raw, ttl)
            if self._redis:
                await self._redis.set(cache_key, raw, ttl)
        except (TypeError, ValueError) as e:
            logger.warning(f"Cache serialization error: {e}")

    async def invalidate(self, prefix: str, key: str):
        cache_key = self._make_key(prefix, key)
        self._memory.delete(cache_key)
        if self._redis:
            await self._redis.delete(cache_key)

    async def clear_all(self):
        self._memory.clear()
        if self._redis:
            await self._redis.clear()
