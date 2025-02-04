"""缓存同步测试模块"""

import pytest
import asyncio
from typing import Dict, Any, AsyncGenerator
from src.cache.cache_sync import CacheEvent, CacheEventBus, CacheSyncManager
from src.cache.local_cache import LRUCache
from src.cache.redis_cache import RedisCache
from redis.asyncio import Redis

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
async def local_cache():
    """本地缓存"""
    cache = LRUCache(
        name="local",
        max_size=1000,
        cleanup_interval=60
    )
    await cache.start()
    try:
        yield cache
    finally:
        await cache.stop()

@pytest.fixture
async def remote_cache(redis_client):
    """远程缓存"""
    cache = RedisCache(
        name="remote",
        redis=redis_client,
        prefix="remote:",
        default_ttl=60
    )
    try:
        yield cache
    finally:
        await cache.clear()

@pytest.fixture
def event_bus():
    """事件总线"""
    return CacheEventBus("test_bus")

@pytest.fixture
async def sync_manager(local_cache, remote_cache, event_bus):
    """同步管理器"""
    manager = CacheSyncManager(
        name="test_sync",
        local_cache=local_cache,
        remote_cache=remote_cache,
        event_bus=event_bus,
        sync_interval=1
    )
    await manager.start()
    try:
        yield manager
    finally:
        await manager.stop()

@pytest.mark.timeout(5)
async def test_cache_event():
    """测试缓存事件"""
    # 创建事件
    event = CacheEvent(
        event_type="set",
        key="key",
        value="value",
        ttl=60,
        version=1
    )
    
    # 转换为字典
    data = event.to_dict()
    
    # 从字典创建事件
    new_event = CacheEvent.from_dict(data)
    
    # 验证属性
    assert new_event.event_type == event.event_type
    assert new_event.key == event.key
    assert new_event.value == event.value
    assert new_event.ttl == event.ttl
    assert new_event.version == event.version
    assert abs(new_event.timestamp - event.timestamp) < 0.1

@pytest.mark.timeout(5)
async def test_event_bus(event_bus):
    """测试事件总线"""
    events = []
    
    # 定义回调函数
    async def callback(event):
        events.append(event)
    
    # 订阅事件
    event_bus.subscribe("set", callback)
    
    # 发布事件
    event = CacheEvent("set", "key", "value")
    await event_bus.publish(event)
    
    # 等待事件处理
    await asyncio.sleep(0.1)
    
    # 验证回调
    assert len(events) == 1
    assert events[0].key == "key"
    assert events[0].value == "value"
    
    # 取消订阅
    event_bus.unsubscribe("set", callback)
    
    # 再次发布
    await event_bus.publish(event)
    await asyncio.sleep(0.1)
    
    # 验证未触发回调
    assert len(events) == 1

@pytest.mark.timeout(5)
async def test_sync_manager_set(sync_manager, local_cache, remote_cache):
    """测试同步管理器设置操作"""
    # 创建事件
    event = CacheEvent("set", "key", "value")
    
    # 发布事件
    await sync_manager.publish_event(event)
    
    # 等待同步
    await asyncio.sleep(1.1)
    
    # 验证本地缓存
    local_value = await local_cache.get("key")
    assert local_value == "value"
    
    # 验证远程缓存
    remote_value = await remote_cache.get("key")
    assert remote_value == "value"

@pytest.mark.timeout(5)
async def test_sync_manager_delete(sync_manager, local_cache, remote_cache):
    """测试同步管理器删除操作"""
    # 设置初始数据
    event = CacheEvent("set", "key", "value")
    await sync_manager.publish_event(event)
    await asyncio.sleep(0.1)
    
    # 删除数据
    event = CacheEvent("delete", "key")
    await sync_manager.publish_event(event)
    await asyncio.sleep(0.1)
    
    # 验证本地缓存
    local_exists = await local_cache.exists("key")
    assert local_exists is False
    
    # 验证远程缓存
    remote_exists = await remote_cache.exists("key")
    assert remote_exists is False

@pytest.mark.timeout(5)
async def test_sync_manager_clear(sync_manager, local_cache, remote_cache):
    """测试同步管理器清空操作"""
    # 设置初始数据
    event1 = CacheEvent("set", "key1", "value1")
    event2 = CacheEvent("set", "key2", "value2")
    await sync_manager.publish_event(event1)
    await sync_manager.publish_event(event2)
    await asyncio.sleep(0.1)
    
    # 清空数据
    event = CacheEvent("clear", "")
    await sync_manager.publish_event(event)
    await asyncio.sleep(0.1)
    
    # 验证本地缓存
    local_exists1 = await local_cache.exists("key1")
    local_exists2 = await local_cache.exists("key2")
    assert local_exists1 is False
    assert local_exists2 is False
    
    # 验证远程缓存
    remote_exists1 = await remote_cache.exists("key1")
    remote_exists2 = await remote_cache.exists("key2")
    assert remote_exists1 is False
    assert remote_exists2 is False

@pytest.mark.timeout(5)
async def test_sync_manager_version(sync_manager, local_cache, remote_cache):
    """测试同步管理器版本控制"""
    # 设置缓存（版本1）
    event1 = CacheEvent("set", "key", "value1", version=1)
    await sync_manager.publish_event(event1)
    await asyncio.sleep(0.1)
    
    # 设置缓存（版本2）
    event2 = CacheEvent("set", "key", "value2", version=2)
    await sync_manager.publish_event(event2)
    await asyncio.sleep(0.1)
    
    # 尝试设置旧版本
    event3 = CacheEvent("set", "key", "value3", version=1)
    await sync_manager.publish_event(event3)
    await asyncio.sleep(0.1)
    
    # 验证本地缓存
    local_value = await local_cache.get("key")
    assert local_value == "value2"
    
    # 验证远程缓存
    remote_value = await remote_cache.get("key")
    assert remote_value == "value2"

@pytest.mark.timeout(5)
async def test_sync_manager_concurrent(sync_manager, local_cache, remote_cache):
    """测试同步管理器并发操作"""
    # 准备多个事件
    events = [
        CacheEvent("set", f"key{i}", f"value{i}")
        for i in range(10)
    ]
    
    # 并发发布事件
    await asyncio.gather(*(
        sync_manager.publish_event(event)
        for event in events
    ))
    
    # 等待同步
    await asyncio.sleep(1.1)
    
    # 验证本地缓存
    for i in range(10):
        value = await local_cache.get(f"key{i}")
        assert value == f"value{i}"
    
    # 验证远程缓存
    for i in range(10):
        value = await remote_cache.get(f"key{i}")
        assert value == f"value{i}"

@pytest.mark.timeout(5)
async def test_sync_manager_error(sync_manager, local_cache, remote_cache):
    """测试同步管理器错误处理"""
    # 模拟网络错误
    async def error_callback(event):
        raise Exception("Network error")
    
    # 添加错误回调
    sync_manager.event_bus.subscribe("set", error_callback)
    
    # 发布事件
    event = CacheEvent("set", "key", "value")
    await sync_manager.publish_event(event)
    
    # 等待同步
    await asyncio.sleep(1.1)
    
    # 验证本地缓存
    value = await local_cache.get("key")
    assert value == "value"
    
    # 验证远程缓存（应该同步成功，因为有重试机制）
    value = await remote_cache.get("key")
    assert value == "value" 