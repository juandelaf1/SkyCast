import time
from app.core.cache import CacheService, MemoryBackend


class TestMemoryBackend:
    def test_set_and_get(self):
        m = MemoryBackend()
        m.set("k1", "v1", 60)
        assert m.get("k1") == "v1"

    def test_expired(self):
        m = MemoryBackend()
        m.set("k2", "v2", 0)
        time.sleep(0.01)
        assert m.get("k2") is None

    def test_delete(self):
        m = MemoryBackend()
        m.set("k3", "v3", 60)
        m.delete("k3")
        assert m.get("k3") is None

    def test_clear(self):
        m = MemoryBackend()
        m.set("a", "1", 60)
        m.set("b", "2", 60)
        m.clear()
        assert m.get("a") is None
        assert m.get("b") is None

    def test_missing_key(self):
        m = MemoryBackend()
        assert m.get("nonexistent") is None


class TestCacheService:
    def test_get_set_sync(self):
        c = CacheService()
        c.set_sync("test", "key1", {"temp": 22.5, "city": "Madrid"}, ttl=60)
        result = c.get_sync("test", "key1")
        assert result == {"temp": 22.5, "city": "Madrid"}

    def test_get_set_async(self):
        import asyncio
        async def run():
            c = CacheService()
            await c.set("async", "key2", {"value": 42}, ttl=60)
            result = await c.get("async", "key2")
            return result
        result = asyncio.run(run())
        assert result == {"value": 42}

    def test_get_missing(self):
        c = CacheService()
        assert c.get_sync("test", "missing") is None

    def test_invalidate(self):
        c = CacheService()
        c.set_sync("test", "inv", "data", ttl=60)
        assert c.get_sync("test", "inv") is not None
        import asyncio
        asyncio.run(c.invalidate("test", "inv"))
        assert c.get_sync("test", "inv") is None

    def test_clear_all(self):
        c = CacheService()
        c.set_sync("a", "k1", 1, ttl=60)
        c.set_sync("b", "k2", 2, ttl=60)
        import asyncio
        asyncio.run(c.clear_all())
        assert c.get_sync("a", "k1") is None
        assert c.get_sync("b", "k2") is None

    def test_expired_ttl(self):
        c = CacheService()
        c.set_sync("test", "exp", "data", ttl=0)
        time.sleep(0.01)
        assert c.get_sync("test", "exp") is None

    def test_different_prefixes(self):
        c = CacheService()
        c.set_sync("a", "x", "a-x", 60)
        c.set_sync("b", "x", "b-x", 60)
        assert c.get_sync("a", "x") == "a-x"
        assert c.get_sync("b", "x") == "b-x"

    def test_serialize_complex(self):
        c = CacheService()
        data = {"list": [1, 2, 3], "nested": {"a": 1}, "float": 3.14}
        c.set_sync("test", "complex", data, 60)
        assert c.get_sync("test", "complex") == data
