"""Redis缓存测试模块"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from redis.asyncio import Redis
from src.cache.redis_cache import RedisCache

@pytest.fixture
def redis_mock():
    """创建Redis Mock"""
    redis = AsyncMock(spec=Redis)
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.setex = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    redis.exists = AsyncMock(return_value=1)
    redis.ttl = AsyncMock(return_value=30)
    redis.mget = AsyncMock(return_value=[None])
    redis.mset = AsyncMock(return_value=True)
    redis.scan = AsyncMock(return_value=(0, []))
    redis.incrby = AsyncMock(return_value=1)
    redis.decrby = AsyncMock(return_value=0)
    redis.pipeline = MagicMock()
    return redis

@pytest.fixture
def cache(redis_mock):
    """创建缓存实例"""
    return RedisCache(
        name="test",
        redis=redis_mock,
        prefix="test:",
        default_ttl=60
    )

@pytest.mark.asyncio
async def test_cache_get(cache, redis_mock):
    """测试获取缓存值"""
    # 设置返回值
    redis_mock.get.return_value = json.dumps("test_value").encode()
    
    # 获取缓存
    value = await cache.get("key1")
    assert value == "test_value"
    
    # 验证调用
    redis_mock.get.assert_called_once_with("test:key1")
    
    # 测试缓存未命中
    redis_mock.get.return_value = None
    value = await cache.get("key2")
    assert value is None
    
    # 测试异常处理
    redis_mock.get.side_effect = Exception("Redis error")
    value = await cache.get("key3")
    assert value is None

@pytest.mark.asyncio
async def test_cache_set(cache, redis_mock):
    """测试设置缓存值"""
    # 设置缓存（带TTL）
    await cache.set("key1", "value1", ttl=30)
    redis_mock.setex.assert_called_once_with(
        "test:key1",
        30,
        json.dumps("value1")
    )
    
    # 设置缓存（使用默认TTL）
    await cache.set("key2", "value2")
    redis_mock.setex.assert_called_with(
        "test:key2",
        60,
        json.dumps("value2")
    )
    
    # 设置缓存（无TTL）
    cache.default_ttl = None
    await cache.set("key3", "value3")
    redis_mock.set.assert_called_once_with(
        "test:key3",
        json.dumps("value3")
    )
    
    # 测试异常处理
    redis_mock.setex.side_effect = Exception("Redis error")
    await cache.set("key4", "value4")  # 不应抛出异常

@pytest.mark.asyncio
async def test_cache_delete(cache, redis_mock):
    """测试删除缓存值"""
    # 删除存在的键
    assert await cache.delete("key1") is True
    redis_mock.delete.assert_called_once_with("test:key1")
    
    # 删除不存在的键
    redis_mock.delete.return_value = 0
    assert await cache.delete("key2") is False
    
    # 测试异常处理
    redis_mock.delete.side_effect = Exception("Redis error")
    assert await cache.delete("key3") is False

@pytest.mark.asyncio
async def test_cache_exists(cache, redis_mock):
    """测试检查缓存键是否存在"""
    # 键存在
    assert await cache.exists("key1") is True
    redis_mock.exists.assert_called_once_with("test:key1")
    
    # 键不存在
    redis_mock.exists.return_value = 0
    assert await cache.exists("key2") is False
    
    # 测试异常处理
    redis_mock.exists.side_effect = Exception("Redis error")
    assert await cache.exists("key3") is False

@pytest.mark.asyncio
async def test_cache_clear(cache, redis_mock):
    """测试清空缓存"""
    # 模拟扫描结果
    redis_mock.scan.side_effect = [
        (1, ["test:key1", "test:key2"]),
        (0, ["test:key3"])
    ]
    
    await cache.clear()
    
    # 验证调用
    assert redis_mock.scan.call_count == 2
    redis_mock.delete.assert_called_with("test:key3")
    
    # 测试异常处理
    redis_mock.scan.side_effect = Exception("Redis error")
    await cache.clear()  # 不应抛出异常

@pytest.mark.asyncio
async def test_cache_ttl(cache, redis_mock):
    """测试获取缓存剩余过期时间"""
    # 获取TTL
    assert await cache.ttl("key1") == 30
    redis_mock.ttl.assert_called_once_with("test:key1")
    
    # 键不存在或已过期
    redis_mock.ttl.return_value = -1
    assert await cache.ttl("key2") is None
    
    # 测试异常处理
    redis_mock.ttl.side_effect = Exception("Redis error")
    assert await cache.ttl("key3") is None

@pytest.mark.asyncio
async def test_cache_multi_get(cache, redis_mock):
    """测试批量获取缓存值"""
    # 设置返回值
    redis_mock.mget.return_value = [
        json.dumps("value1").encode(),
        None,
        json.dumps("value3").encode()
    ]
    
    # 批量获取
    values = await cache.multi_get(["key1", "key2", "key3"])
    assert values == {
        "key1": "value1",
        "key3": "value3"
    }
    
    # 验证调用
    redis_mock.mget.assert_called_once_with([
        "test:key1",
        "test:key2",
        "test:key3"
    ])
    
    # 测试异常处理
    redis_mock.mget.side_effect = Exception("Redis error")
    values = await cache.multi_get(["key4"])
    assert values == {}

@pytest.mark.asyncio
async def test_cache_multi_set(cache, redis_mock):
    """测试批量设置缓存值"""
    # 创建pipeline mock
    pipe = AsyncMock()
    pipe.execute = AsyncMock()
    redis_mock.pipeline.return_value.__aenter__.return_value = pipe
    
    # 批量设置（带TTL）
    await cache.multi_set({
        "key1": "value1",
        "key2": "value2"
    }, ttl=30)
    
    # 验证pipeline调用
    assert pipe.setex.call_count == 2
    
    # 批量设置（无TTL）
    cache.default_ttl = None
    await cache.multi_set({
        "key3": "value3",
        "key4": "value4"
    })
    
    # 验证mset调用
    redis_mock.mset.assert_called_once()
    
    # 测试异常处理
    redis_mock.pipeline.side_effect = Exception("Redis error")
    await cache.multi_set({"key5": "value5"})  # 不应抛出异常

@pytest.mark.asyncio
async def test_cache_incr(cache, redis_mock):
    """测试增加计数器值"""
    # 增加计数
    assert await cache.incr("counter") == 1
    redis_mock.incrby.assert_called_once_with("test:counter", 1)
    
    # 指定增加量
    assert await cache.incr("counter", 5) == 1
    redis_mock.incrby.assert_called_with("test:counter", 5)
    
    # 测试异常处理
    redis_mock.incrby.side_effect = Exception("Redis error")
    assert await cache.incr("counter") is None

@pytest.mark.asyncio
async def test_cache_decr(cache, redis_mock):
    """测试减少计数器值"""
    # 减少计数
    assert await cache.decr("counter") == 0
    redis_mock.decrby.assert_called_once_with("test:counter", 1)
    
    # 指定减少量
    assert await cache.decr("counter", 5) == 0
    redis_mock.decrby.assert_called_with("test:counter", 5)
    
    # 测试异常处理
    redis_mock.decrby.side_effect = Exception("Redis error")
    assert await cache.decr("counter") is None

@pytest.mark.asyncio
async def test_cache_lock(cache, redis_mock):
    """测试分布式锁"""
    # 获取锁成功
    redis_mock.set.return_value = True
    assert await cache.acquire_lock("lock1") is True
    
    # 获取锁失败
    redis_mock.set.return_value = False
    assert await cache.acquire_lock("lock2") is False
    
    # 释放锁
    redis_mock.delete.return_value = 1
    assert await cache.release_lock("lock1") is True
    
    # 释放不存在的锁
    redis_mock.delete.return_value = 0
    assert await cache.release_lock("lock2") is False 