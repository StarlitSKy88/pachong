"""Redis缓存测试模块"""

import json
import pytest
import asyncio
from typing import Dict, Any
from redis.asyncio import Redis
from src.cache.redis_cache import RedisCache

pytestmark = pytest.mark.asyncio

@pytest.fixture
async def redis_client():
    """Redis客户端"""
    client = Redis(
        host="localhost",
        port=6379,
        db=0,
        decode_responses=True
    )
    try:
        yield client
    finally:
        await client.close()

@pytest.fixture
async def redis_cache(redis_client):
    """Redis缓存"""
    cache = RedisCache(
        name="test",
        redis=redis_client,
        prefix="test:",
        default_ttl=60
    )
    try:
        yield cache
    finally:
        await cache.clear()

@pytest.mark.timeout(5)
async def test_cache_set_get(redis_cache):
    """测试设置和获取缓存"""
    # 设置缓存
    await redis_cache.set("key", "value")
    
    # 获取缓存
    value = await redis_cache.get("key")
    
    # 验证结果
    assert value == "value"
    
    # 获取不存在的键
    value = await redis_cache.get("not_exists")
    assert value is None

@pytest.mark.timeout(5)
async def test_cache_delete(redis_cache):
    """测试删除缓存"""
    # 设置缓存
    await redis_cache.set("key", "value")
    
    # 删除缓存
    result = await redis_cache.delete("key")
    assert result is True
    
    # 验证已删除
    value = await redis_cache.get("key")
    assert value is None
    
    # 删除不存在的键
    result = await redis_cache.delete("not_exists")
    assert result is False

@pytest.mark.timeout(5)
async def test_cache_exists(redis_cache):
    """测试检查键是否存在"""
    # 设置缓存
    await redis_cache.set("key", "value")
    
    # 检查存在的键
    exists = await redis_cache.exists("key")
    assert exists is True
    
    # 检查不存在的键
    exists = await redis_cache.exists("not_exists")
    assert exists is False

@pytest.mark.timeout(5)
async def test_cache_clear(redis_cache):
    """测试清空缓存"""
    # 设置多个缓存
    await redis_cache.set("key1", "value1")
    await redis_cache.set("key2", "value2")
    
    # 清空缓存
    await redis_cache.clear()
    
    # 验证已清空
    value1 = await redis_cache.get("key1")
    value2 = await redis_cache.get("key2")
    assert value1 is None
    assert value2 is None

@pytest.mark.timeout(5)
async def test_cache_ttl(redis_cache):
    """测试过期时间"""
    # 设置带TTL的缓存
    await redis_cache.set("key", "value", ttl=1)
    
    # 验证未过期
    value = await redis_cache.get("key")
    assert value == "value"
    
    # 等待过期
    await asyncio.sleep(1.1)
    
    # 验证已过期
    value = await redis_cache.get("key")
    assert value is None

@pytest.mark.timeout(5)
async def test_cache_multi_get(redis_cache):
    """测试批量获取"""
    # 设置多个缓存
    data = {
        "key1": "value1",
        "key2": "value2",
        "key3": "value3"
    }
    for key, value in data.items():
        await redis_cache.set(key, value)
    
    # 批量获取
    values = await redis_cache.multi_get(["key1", "key2", "not_exists"])
    
    # 验证结果
    assert values == {
        "key1": "value1",
        "key2": "value2"
    }

@pytest.mark.timeout(5)
async def test_cache_multi_set(redis_cache):
    """测试批量设置"""
    # 准备数据
    data = {
        "key1": "value1",
        "key2": "value2",
        "key3": "value3"
    }
    
    # 批量设置
    await redis_cache.multi_set(data)
    
    # 验证结果
    for key, value in data.items():
        cached = await redis_cache.get(key)
        assert cached == value

@pytest.mark.timeout(5)
async def test_cache_serialization(redis_cache):
    """测试序列化"""
    # 准备复杂数据
    data = {
        "string": "value",
        "number": 123,
        "float": 3.14,
        "list": [1, 2, 3],
        "dict": {"key": "value"}
    }
    
    # 设置缓存
    await redis_cache.set("key", data)
    
    # 获取缓存
    value = await redis_cache.get("key")
    
    # 验证结果
    assert value == data

@pytest.mark.timeout(5)
async def test_cache_metrics(redis_cache):
    """测试性能指标"""
    # 设置缓存
    await redis_cache.set("key", "value")
    
    # 获取存在的键
    value = await redis_cache.get("key")
    assert value == "value"
    
    # 获取不存在的键
    value = await redis_cache.get("not_exists")
    assert value is None
    
    # 获取指标
    metrics = await redis_cache.get_metrics()
    
    # 验证指标
    assert metrics["hits"] == 1
    assert metrics["misses"] == 1
    assert metrics["size"] == 1

@pytest.mark.timeout(5)
async def test_cache_incr(redis_cache):
    """测试计数器增加"""
    # 增加计数
    value = await redis_cache.incr("counter")
    assert value == 1
    
    # 再次增加
    value = await redis_cache.incr("counter")
    assert value == 2
    
    # 增加指定值
    value = await redis_cache.incr("counter", 3)
    assert value == 5

@pytest.mark.timeout(5)
async def test_cache_decr(redis_cache):
    """测试计数器减少"""
    # 设置初始值
    await redis_cache.set("counter", 10)
    
    # 减少计数
    value = await redis_cache.decr("counter")
    assert value == 9
    
    # 再次减少
    value = await redis_cache.decr("counter")
    assert value == 8
    
    # 减少指定值
    value = await redis_cache.decr("counter", 3)
    assert value == 5

@pytest.mark.timeout(5)
async def test_cache_lock(redis_cache):
    """测试分布式锁"""
    # 获取锁
    async with redis_cache.acquire_lock("lock_key") as locked:
        assert locked is True
        
        # 尝试重复获取
        async with redis_cache.acquire_lock("lock_key") as locked:
            assert locked is False
    
    # 锁已释放，可以再次获取
    async with redis_cache.acquire_lock("lock_key") as locked:
        assert locked is True 