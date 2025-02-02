"""本地缓存测试模块"""

import pytest
import asyncio
import time
from src.cache.local_cache import LRUCache

@pytest.fixture
async def cache():
    """创建缓存实例"""
    cache = LRUCache("test", max_size=3, cleanup_interval=1)
    await cache.start()
    yield cache
    await cache.stop()

@pytest.mark.asyncio
async def test_cache_set_get(cache):
    """测试缓存的设置和获取"""
    # 设置缓存
    await cache.set("key1", "value1")
    await cache.set("key2", "value2")
    
    # 获取缓存
    assert await cache.get("key1") == "value1"
    assert await cache.get("key2") == "value2"
    assert await cache.get("key3") is None
    
    # 检查命中率
    metrics = await cache.get_metrics()
    assert metrics["hits"] == 2
    assert metrics["misses"] == 1
    assert metrics["current_size"] == 2

@pytest.mark.asyncio
async def test_cache_lru(cache):
    """测试LRU淘汰机制"""
    # 添加超过最大大小的缓存
    await cache.set("key1", "value1")
    await cache.set("key2", "value2")
    await cache.set("key3", "value3")
    await cache.set("key4", "value4")  # 应该淘汰key1
    
    # 验证最早的条目被淘汰
    assert await cache.get("key1") is None
    assert await cache.get("key2") == "value2"
    assert await cache.get("key3") == "value3"
    assert await cache.get("key4") == "value4"
    
    # 检查淘汰次数
    metrics = await cache.get_metrics()
    assert metrics["evictions"] == 1

@pytest.mark.asyncio
async def test_cache_ttl(cache):
    """测试缓存过期"""
    # 设置带TTL的缓存
    await cache.set("key1", "value1", ttl=1)
    
    # 立即获取
    assert await cache.get("key1") == "value1"
    
    # 等待过期
    await asyncio.sleep(1.1)
    
    # 再次获取
    assert await cache.get("key1") is None
    
    # 检查TTL
    assert await cache.ttl("key1") is None

@pytest.mark.asyncio
async def test_cache_exists(cache):
    """测试缓存键是否存在"""
    await cache.set("key1", "value1")
    
    assert await cache.exists("key1") is True
    assert await cache.exists("key2") is False
    
    # 设置带TTL的缓存
    await cache.set("key3", "value3", ttl=1)
    assert await cache.exists("key3") is True
    
    # 等待过期
    await asyncio.sleep(1.1)
    assert await cache.exists("key3") is False

@pytest.mark.asyncio
async def test_cache_delete(cache):
    """测试删除缓存"""
    await cache.set("key1", "value1")
    
    assert await cache.delete("key1") is True
    assert await cache.delete("key2") is False
    assert await cache.get("key1") is None

@pytest.mark.asyncio
async def test_cache_clear(cache):
    """测试清空缓存"""
    await cache.set("key1", "value1")
    await cache.set("key2", "value2")
    
    await cache.clear()
    
    assert await cache.get("key1") is None
    assert await cache.get("key2") is None
    
    metrics = await cache.get_metrics()
    assert metrics["size"] == 0

@pytest.mark.asyncio
async def test_cache_metrics(cache):
    """测试缓存指标"""
    # 添加缓存并访问
    await cache.set("key1", "value1")
    await cache.get("key1")  # 命中
    await cache.get("key2")  # 未命中
    
    metrics = await cache.get_metrics()
    assert metrics["hits"] == 1
    assert metrics["misses"] == 1
    assert metrics["current_size"] == 1
    assert metrics["max_size"] == 3
    assert 0 < metrics["hit_rate"] < 1

@pytest.mark.asyncio
async def test_cache_cleanup(cache):
    """测试缓存清理"""
    # 添加带TTL的缓存
    await cache.set("key1", "value1", ttl=1)
    await cache.set("key2", "value2")  # 无TTL
    
    # 等待清理
    await asyncio.sleep(1.5)
    
    assert await cache.get("key1") is None
    assert await cache.get("key2") == "value2"

@pytest.mark.asyncio
async def test_cache_multi_get(cache):
    """测试批量获取缓存"""
    # 设置缓存
    await cache.set("key1", "value1")
    await cache.set("key2", "value2")
    await cache.set("key3", "value3", ttl=1)
    
    # 等待key3过期
    await asyncio.sleep(1.1)
    
    # 批量获取
    results = await cache.multi_get(["key1", "key2", "key3", "key4"])
    assert results == {
        "key1": "value1",
        "key2": "value2"
    }
    
    # 检查指标
    metrics = await cache.get_metrics()
    assert metrics["hits"] == 2
    assert metrics["misses"] == 2

@pytest.mark.asyncio
async def test_cache_multi_set(cache):
    """测试批量设置缓存"""
    # 批量设置
    await cache.multi_set({
        "key1": "value1",
        "key2": "value2",
        "key3": "value3"
    }, ttl=1)
    
    # 验证设置成功
    assert await cache.get("key1") == "value1"
    assert await cache.get("key2") == "value2"
    assert await cache.get("key3") == "value3"
    
    # 等待过期
    await asyncio.sleep(1.1)
    
    # 验证全部过期
    assert await cache.get("key1") is None
    assert await cache.get("key2") is None
    assert await cache.get("key3") is None

@pytest.mark.asyncio
async def test_cache_update(cache):
    """测试更新缓存"""
    # 设置初始值
    await cache.set("key1", "value1")
    assert await cache.get("key1") == "value1"
    
    # 更新值
    await cache.set("key1", "value2")
    assert await cache.get("key1") == "value2"
    
    # 检查版本号
    with cache._lock:
        entry = cache._cache["key1"]
        assert entry.version == 2

@pytest.mark.asyncio
async def test_cache_expire(cache):
    """测试设置过期时间"""
    await cache.set("key1", "value1")
    
    # 设置过期时间
    assert await cache.expire("key1", 1) is True
    assert await cache.expire("key2", 1) is False
    
    # 等待过期
    await asyncio.sleep(1.1)
    assert await cache.get("key1") is None 