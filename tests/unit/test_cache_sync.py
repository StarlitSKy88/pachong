"""缓存同步测试模块"""

import pytest
import asyncio
import pytest_asyncio
from unittest.mock import AsyncMock, Mock
from src.cache.cache_sync import CacheEvent, CacheEventBus, CacheSyncManager
from src.cache.cache_manager import BaseCache
from datetime import datetime

class TestCache(BaseCache):
    """测试用缓存类"""
    
    def __init__(self, name: str):
        """初始化测试缓存"""
        super().__init__(name)
        self.data = {}
        self.ttl_data = {}  # 存储 TTL 信息
        self.ttl_start = {}  # 存储 TTL 开始时间
        self.redis = AsyncMock()
        self.prefix = "test:"
        
    async def get(self, key: str):
        """获取缓存值"""
        # 检查是否过期
        if key in self.ttl_data and key in self.ttl_start:
            ttl = self.ttl_data[key]
            if ttl is not None:
                elapsed = datetime.now().timestamp() - self.ttl_start[key]
                if elapsed >= ttl:
                    await self.delete(key)
                    return None
        return self.data.get(key)
        
    async def set(self, key: str, value, ttl=None):
        """设置缓存值"""
        self.data[key] = value
        if ttl is not None:
            self.ttl_data[key] = ttl
            self.ttl_start[key] = datetime.now().timestamp()
        
    async def delete(self, key: str):
        """删除缓存值"""
        if key in self.data:
            del self.data[key]
            if key in self.ttl_data:
                del self.ttl_data[key]
            if key in self.ttl_start:
                del self.ttl_start[key]
            return True
        return False
        
    async def exists(self, key: str):
        """检查缓存键是否存在"""
        return key in self.data
        
    async def clear(self):
        """清空缓存"""
        self.data.clear()
        self.ttl_data.clear()
        self.ttl_start.clear()
        
    async def get_metrics(self):
        """获取缓存指标"""
        return self._metrics
        
    async def ttl(self, key: str):
        """获取过期时间"""
        if key in self.ttl_data and key in self.ttl_start:
            ttl = self.ttl_data[key]
            if ttl is not None:
                elapsed = datetime.now().timestamp() - self.ttl_start[key]
                remaining = ttl - elapsed
                return max(0, remaining)
        return None
        
    async def scan(self, cursor: int = 0, match: str = None, count: int = 10):
        """扫描缓存键"""
        keys = list(self.data.keys())
        if match:
            import fnmatch
            keys = [k for k in keys if fnmatch.fnmatch(k, match)]
        
        start = cursor
        end = min(start + count, len(keys))
        next_cursor = end if end < len(keys) else 0
        return next_cursor, keys[start:end]

@pytest.fixture
def event():
    """创建测试事件"""
    return CacheEvent(
        event_type="set",
        key="test_key",
        value="test_value",
        ttl=60
    )

@pytest.fixture
def event_bus():
    """创建事件总线"""
    return CacheEventBus("test_bus")

@pytest.fixture
def local_cache():
    """创建本地缓存"""
    return TestCache("test_local")

@pytest.fixture
def remote_cache():
    """创建远程缓存"""
    cache = TestCache("test_remote")
    # 模拟scan方法
    cache.redis.scan = AsyncMock(return_value=(0, ["test:key1", "test:key2"]))
    return cache

@pytest_asyncio.fixture
async def sync_manager(local_cache, remote_cache, event_bus):
    """创建同步管理器"""
    manager = CacheSyncManager(
        name="test_sync",
        local_cache=local_cache,
        remote_cache=remote_cache,
        event_bus=event_bus,
        sync_interval=1
    )
    await manager.start()
    await asyncio.sleep(0.1)  # 等待同步任务启动
    try:
        yield manager
    finally:
        if manager._running:
            await manager.stop()

@pytest.mark.asyncio
async def test_cache_event():
    """测试缓存事件"""
    event = CacheEvent(
        event_type="set",
        key="test_key",
        value="test_value",
        ttl=60,
        version=1
    )
    
    # 测试转换为字典
    event_dict = event.to_dict()
    assert event_dict["event_type"] == "set"
    assert event_dict["key"] == "test_key"
    assert event_dict["value"] == "test_value"
    assert event_dict["ttl"] == 60
    assert event_dict["version"] == 1
    
    # 测试从字典创建
    new_event = CacheEvent.from_dict(event_dict)
    assert new_event.event_type == event.event_type
    assert new_event.key == event.key
    assert new_event.value == event.value
    assert new_event.ttl == event.ttl
    assert new_event.version == event.version

@pytest.mark.asyncio
async def test_event_bus(event_bus, event):
    """测试事件总线"""
    # 创建回调函数
    callback = AsyncMock()
    
    # 订阅事件
    event_bus.subscribe("set", callback)
    
    # 发布事件
    await event_bus.publish(event)
    callback.assert_called_once_with(event)
    
    # 取消订阅
    event_bus.unsubscribe("set", callback)
    await event_bus.publish(event)
    assert callback.call_count == 1  # 不应该再次调用
    
    # 测试异常处理
    callback.side_effect = Exception("Test error")
    event_bus.subscribe("set", callback)
    await event_bus.publish(event)  # 不应抛出异常

@pytest.mark.asyncio
async def test_sync_manager_start_stop(sync_manager):
    """测试同步管理器启动和停止"""
    assert sync_manager._running is True
    assert sync_manager._sync_task is not None
    
    await sync_manager.stop()
    assert sync_manager._running is False
    assert sync_manager._sync_task is None
    
    # 重复停止不应报错
    await sync_manager.stop()

@pytest.mark.asyncio
async def test_sync_manager_sync_caches(sync_manager, local_cache, remote_cache):
    """测试缓存同步"""
    # 设置远程缓存数据
    await remote_cache.set(f"{remote_cache.prefix}key1", "value1")
    await remote_cache.set(f"{remote_cache.prefix}key2", "value2")
    
    # 等待同步
    await asyncio.sleep(1.1)
    
    # 验证本地缓存
    assert await local_cache.get(f"{local_cache.prefix}key1") == "value1"
    assert await local_cache.get(f"{local_cache.prefix}key2") == "value2"

@pytest.mark.asyncio
async def test_sync_manager_handle_set_event(sync_manager, local_cache, remote_cache, event):
    """测试处理设置事件"""
    await sync_manager.publish_event(event)
    await asyncio.sleep(0.1)  # 等待事件处理完成
    
    # 验证本地和远程缓存
    assert await local_cache.get(event.key) == event.value
    assert await remote_cache.get(event.key) == event.value

@pytest.mark.asyncio
async def test_sync_manager_handle_delete_event(sync_manager, local_cache, remote_cache):
    """测试处理删除事件"""
    # 先设置数据
    key = "test_key"
    await local_cache.set(key, "value")
    await remote_cache.set(key, "value")
    
    # 发布删除事件
    event = CacheEvent("delete", key)
    await sync_manager.publish_event(event)
    await asyncio.sleep(0.1)  # 等待事件处理完成
    
    # 验证数据已删除
    assert await local_cache.get(key) is None
    assert await remote_cache.get(key) is None

@pytest.mark.asyncio
async def test_sync_manager_handle_clear_event(sync_manager, local_cache, remote_cache):
    """测试处理清空事件"""
    # 先设置数据
    await local_cache.set("key1", "value1")
    await local_cache.set("key2", "value2")
    await remote_cache.set("key1", "value1")
    await remote_cache.set("key2", "value2")
    
    # 发布清空事件
    event = CacheEvent("clear", "")
    await sync_manager.publish_event(event)
    await asyncio.sleep(0.1)  # 等待事件处理完成
    
    # 验证缓存已清空
    assert len(local_cache.data) == 0
    assert len(remote_cache.data) == 0

@pytest.mark.asyncio
async def test_sync_manager_error_handling(sync_manager, local_cache, remote_cache):
    """测试错误处理"""
    # 模拟错误
    local_cache.set = AsyncMock(side_effect=Exception("Local cache error"))
    remote_cache.set = AsyncMock(side_effect=Exception("Remote cache error"))
    
    # 发布事件
    event = CacheEvent("set", "key", "value")
    await sync_manager.publish_event(event)  # 不应抛出异常
    await asyncio.sleep(0.1)  # 等待事件处理完成
    
    # 模拟同步错误
    remote_cache.redis.scan = AsyncMock(side_effect=Exception("Sync error"))
    await asyncio.sleep(1.1)  # 等待同步循环
    # 不应抛出异常，应该继续运行

@pytest.mark.asyncio
async def test_sync_manager_version_conflict(sync_manager, local_cache, remote_cache):
    """测试版本冲突处理"""
    # 创建两个版本不同的事件
    event1 = CacheEvent("set", "key", "value1", version=1)
    event2 = CacheEvent("set", "key", "value2", version=2)
    
    # 按顺序发布事件
    await sync_manager.publish_event(event1)
    await asyncio.sleep(0.1)  # 等待事件处理完成
    await sync_manager.publish_event(event2)
    await asyncio.sleep(0.1)  # 等待事件处理完成
    
    # 验证使用了最新版本的值
    assert await local_cache.get("key") == "value2"
    assert await remote_cache.get("key") == "value2"

@pytest.mark.asyncio
async def test_sync_manager_concurrent_events(sync_manager, local_cache, remote_cache):
    """测试并发事件处理"""
    # 创建多个事件
    events = [
        CacheEvent("set", f"key{i}", f"value{i}")
        for i in range(10)
    ]
    
    # 并发发布事件
    await asyncio.gather(*(
        sync_manager.publish_event(event)
        for event in events
    ))
    await asyncio.sleep(0.1)  # 等待事件处理完成
    
    # 验证所有值都正确设置
    for i in range(10):
        assert await local_cache.get(f"key{i}") == f"value{i}"
        assert await remote_cache.get(f"key{i}") == f"value{i}"

@pytest.mark.asyncio
async def test_sync_manager_ttl_handling(sync_manager, local_cache, remote_cache):
    """测试TTL处理"""
    # 创建带TTL的事件
    key = f"{local_cache.prefix}key"
    event = CacheEvent("set", key, "value", ttl=0.1)  # 使用更短的TTL
    await sync_manager.publish_event(event)
    await asyncio.sleep(0.05)  # 等待事件处理完成
    
    # 验证值已设置
    assert await local_cache.get(key) == "value"
    assert await remote_cache.get(key) == "value"
    
    # 等待过期
    await asyncio.sleep(0.2)  # 等待TTL过期
    
    # 验证值已过期
    assert await local_cache.get(key) is None
    assert await remote_cache.get(key) is None

@pytest.mark.asyncio
async def test_sync_manager_invalid_events(sync_manager, local_cache, remote_cache):
    """测试无效事件处理"""
    # 创建无效事件类型
    event = CacheEvent("invalid", "key", "value")
    await sync_manager.publish_event(event)  # 不应抛出异常
    await asyncio.sleep(0.1)  # 等待事件处理完成
    
    # 创建无效键
    event = CacheEvent("set", "", "value")
    await sync_manager.publish_event(event)  # 不应抛出异常
    await asyncio.sleep(0.1)  # 等待事件处理完成
    
    # 创建无效值
    event = CacheEvent("set", "key", None)
    await sync_manager.publish_event(event)  # 不应抛出异常
    await asyncio.sleep(0.1)  # 等待事件处理完成

@pytest.mark.asyncio
async def test_sync_manager_start_twice(sync_manager):
    """测试重复启动同步管理器"""
    # 第一次启动已经在 fixture 中完成
    assert sync_manager._running is True
    assert sync_manager._sync_task is not None
    
    # 再次启动不应有影响
    await sync_manager.start()
    assert sync_manager._running is True
    assert sync_manager._sync_task is not None

@pytest.mark.asyncio
async def test_sync_manager_stop_twice(sync_manager):
    """测试重复停止同步管理器"""
    # 第一次停止
    await sync_manager.stop()
    assert sync_manager._running is False
    assert sync_manager._sync_task is None
    
    # 再次停止不应报错
    await sync_manager.stop()
    assert sync_manager._running is False
    assert sync_manager._sync_task is None

@pytest.mark.asyncio
async def test_sync_manager_sync_error(sync_manager, local_cache, remote_cache):
    """测试同步错误处理"""
    # 模拟 scan 错误
    remote_cache.scan = AsyncMock(side_effect=Exception("Scan error"))
    
    # 等待同步循环
    await asyncio.sleep(1.1)
    
    # 验证同步管理器仍在运行
    assert sync_manager._running is True
    assert sync_manager._sync_task is not None

@pytest.mark.asyncio
async def test_sync_manager_sync_empty(sync_manager, local_cache, remote_cache):
    """测试同步空缓存"""
    # 清空远程缓存
    await remote_cache.clear()
    
    # 等待同步
    await asyncio.sleep(1.1)
    
    # 验证本地缓存也为空
    assert len(local_cache.data) == 0

@pytest.mark.asyncio
async def test_sync_manager_sync_large_data(sync_manager, local_cache, remote_cache):
    """测试同步大量数据"""
    # 设置大量远程缓存数据
    for i in range(150):  # 超过一次 scan 的数量
        await remote_cache.set(f"{remote_cache.prefix}key{i}", f"value{i}")
    
    # 等待同步
    await asyncio.sleep(2.2)  # 等待两个同步周期
    
    # 验证所有数据都同步了
    for i in range(150):
        assert await local_cache.get(f"{local_cache.prefix}key{i}") == f"value{i}"

@pytest.mark.asyncio
async def test_sync_manager_sync_with_ttl(sync_manager, local_cache, remote_cache):
    """测试同步带 TTL 的数据"""
    # 设置带 TTL 的远程缓存数据
    await remote_cache.set(f"{remote_cache.prefix}key1", "value1", ttl=2)  # 增加 TTL 时间
    await remote_cache.set(f"{remote_cache.prefix}key2", "value2", ttl=4)
    
    # 等待第一次同步
    await asyncio.sleep(1.1)
    
    # 验证数据已同步
    assert await local_cache.get(f"{local_cache.prefix}key1") == "value1"
    assert await local_cache.get(f"{local_cache.prefix}key2") == "value2"
    
    # 等待第一个键过期
    await asyncio.sleep(1.1)  # 总共等待 2.2 秒，第一个键应该过期
    
    # 验证第一个键已过期，第二个键仍存在
    assert await local_cache.get(f"{local_cache.prefix}key1") is None
    assert await local_cache.get(f"{local_cache.prefix}key2") == "value2"

@pytest.mark.asyncio
async def test_sync_manager_event_error(sync_manager, local_cache, remote_cache):
    """测试事件处理错误"""
    # 模拟本地缓存错误
    local_cache.set = AsyncMock(side_effect=Exception("Set error"))
    
    # 发布事件
    event = CacheEvent("set", f"{local_cache.prefix}key", "value")
    await sync_manager.publish_event(event)
    await asyncio.sleep(0.1)  # 等待事件处理完成
    
    # 验证远程缓存仍然设置成功
    assert await remote_cache.get(f"{remote_cache.prefix}key") == "value"

@pytest.mark.asyncio
async def test_sync_manager_invalid_event_type(sync_manager, local_cache, remote_cache):
    """测试无效事件类型"""
    # 发布无效事件类型
    event = CacheEvent("invalid_type", f"{local_cache.prefix}key", "value")
    await sync_manager.publish_event(event)
    await asyncio.sleep(0.1)  # 等待事件处理完成
    
    # 验证缓存未被修改
    assert await local_cache.get(f"{local_cache.prefix}key") is None
    assert await remote_cache.get(f"{remote_cache.prefix}key") is None

@pytest.mark.asyncio
async def test_sync_manager_event_version(sync_manager, local_cache, remote_cache):
    """测试事件版本处理"""
    # 发布低版本事件
    event1 = CacheEvent("set", f"{local_cache.prefix}key", "value1", version=1)
    await sync_manager.publish_event(event1)
    await asyncio.sleep(0.1)  # 等待事件处理完成
    
    # 发布高版本事件
    event2 = CacheEvent("set", f"{local_cache.prefix}key", "value2", version=2)
    await sync_manager.publish_event(event2)
    await asyncio.sleep(0.1)  # 等待事件处理完成
    
    # 再次发布低版本事件
    event3 = CacheEvent("set", f"{local_cache.prefix}key", "value3", version=1)
    await sync_manager.publish_event(event3)
    await asyncio.sleep(0.1)  # 等待事件处理完成
    
    # 验证使用了最高版本的值
    assert await local_cache.get(f"{local_cache.prefix}key") == "value2"
    assert await remote_cache.get(f"{remote_cache.prefix}key") == "value2" 