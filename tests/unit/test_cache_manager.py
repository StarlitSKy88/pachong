"""缓存管理器测试模块"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, Mock
from src.cache.cache_manager import CacheEntry, BaseCache, CacheManager

class TestCache(BaseCache):
    """测试用缓存类"""
    
    def __init__(self, name: str = None):
        """初始化测试缓存"""
        super().__init__(name)
        self.data = {}
        self.ttl_data = {}  # 存储 TTL 信息
        self.ttl_start = {}  # 存储 TTL 开始时间
        
    async def get(self, key: str):
        """获取缓存值"""
        # 检查是否过期
        if key in self.ttl_data and key in self.ttl_start:
            ttl = self.ttl_data[key]
            if ttl is not None:
                elapsed = datetime.now().timestamp() - self.ttl_start[key]
                if elapsed >= ttl:
                    await self.delete(key)
                    self._update_metrics(hit=False)
                    return None
        value = self.data.get(key)
        self._update_metrics(hit=value is not None)
        return value
        
    async def set(self, key: str, value, ttl=None):
        """设置缓存值"""
        self.data[key] = value
        if ttl is not None:
            self.ttl_data[key] = ttl
            self.ttl_start[key] = datetime.now().timestamp()
        self._metrics["size"] = len(self.data)
        
    async def delete(self, key: str):
        """删除缓存值"""
        if key in self.data:
            del self.data[key]
            if key in self.ttl_data:
                del self.ttl_data[key]
            if key in self.ttl_start:
                del self.ttl_start[key]
            self._metrics["size"] = len(self.data)
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
        self._metrics["size"] = 0
        self._metrics["evictions"] += 1
        
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

@pytest.mark.asyncio
async def test_cache_entry():
    """测试缓存条目"""
    # 创建缓存条目
    entry = CacheEntry("key", "value", ttl=1)
    assert entry.key == "key"
    assert entry.value == "value"
    assert entry.ttl == 1
    assert entry.version == 1
    assert entry.hits == 0
    
    # 测试访问
    entry.access()
    assert entry.hits == 1
    
    # 测试更新
    entry.update("new_value", 2)
    assert entry.value == "new_value"
    assert entry.version == 2
    
    # 测试过期
    assert not entry.expired  # 刚创建，未过期
    await asyncio.sleep(1.1)  # 等待过期
    assert entry.expired  # 已过期
    
    # 测试无 TTL
    entry = CacheEntry("key", "value")
    assert not entry.expired  # 无 TTL 永不过期

@pytest.mark.asyncio
async def test_base_cache():
    """测试基础缓存"""
    cache = TestCache("test")
    
    # 测试设置和获取
    await cache.set("key", "value")
    assert await cache.get("key") == "value"
    assert await cache.exists("key")
    
    # 测试删除
    assert await cache.delete("key")
    assert not await cache.exists("key")
    assert await cache.get("key") is None
    
    # 测试批量操作
    mapping = {"key1": "value1", "key2": "value2"}
    await cache.multi_set(mapping)
    result = await cache.multi_get(["key1", "key2", "key3"])
    assert result == {"key1": "value1", "key2": "value2"}
    
    # 测试过期
    await cache.set("key", "value")
    assert await cache.expire("key", 1)
    assert await cache.get("key") == "value"
    await asyncio.sleep(1.1)
    assert await cache.get("key") is None
    
    # 测试清空
    await cache.set("key1", "value1")
    await cache.set("key2", "value2")
    await cache.clear()
    assert len(cache.data) == 0
    
    # 测试指标
    metrics = await cache.get_metrics()
    assert metrics["hits"] > 0
    assert metrics["misses"] > 0
    assert metrics["size"] == 0
    assert metrics["evictions"] == 1
    assert 0 <= cache.hit_rate <= 1.0

@pytest.mark.asyncio
async def test_cache_manager():
    """测试缓存管理器"""
    manager = CacheManager()
    cache1 = TestCache("cache1")
    cache2 = TestCache("cache2")
    
    # 测试注册缓存
    manager.register_cache("cache1", cache1)
    manager.register_cache("cache2", cache2)
    
    # 测试获取缓存
    assert manager.get_cache("cache1") == cache1
    assert manager.get_cache("cache2") == cache2
    
    # 测试获取不存在的缓存
    with pytest.raises(KeyError):
        manager.get_cache("not_exists")

@pytest.mark.asyncio
async def test_cache_ttl():
    """测试缓存 TTL"""
    cache = TestCache("test")
    
    # 设置带 TTL 的值
    await cache.set("key1", "value1", ttl=1)
    await cache.set("key2", "value2", ttl=2)
    
    # 验证 TTL
    assert await cache.ttl("key1") > 0
    assert await cache.ttl("key2") > 0
    assert await cache.ttl("key3") is None  # 不存在的键
    
    # 等待第一个键过期
    await asyncio.sleep(1.1)
    assert await cache.get("key1") is None  # 已过期
    assert await cache.get("key2") == "value2"  # 未过期
    
    # 等待第二个键过期
    await asyncio.sleep(1.1)
    assert await cache.get("key2") is None  # 已过期

@pytest.mark.asyncio
async def test_cache_metrics():
    """测试缓存指标"""
    cache = TestCache("test")
    
    # 初始指标
    metrics = await cache.get_metrics()
    assert metrics["hits"] == 0
    assert metrics["misses"] == 0
    assert metrics["size"] == 0
    assert metrics["evictions"] == 0
    assert cache.hit_rate == 0.0
    
    # 设置值并访问
    await cache.set("key", "value")
    assert await cache.get("key") == "value"  # 命中
    assert await cache.get("not_exists") is None  # 未命中
    
    # 验证指标更新
    metrics = await cache.get_metrics()
    assert metrics["hits"] == 1
    assert metrics["misses"] == 1
    assert metrics["size"] == 1
    assert cache.hit_rate == 0.5
    
    # 清空缓存
    await cache.clear()
    metrics = await cache.get_metrics()
    assert metrics["size"] == 0
    assert metrics["evictions"] == 1

@pytest.mark.asyncio
async def test_cache_hit_rate_edge_cases():
    """测试缓存命中率边缘情况"""
    cache = TestCache("test")
    
    # 初始状态（无访问）
    assert cache.hit_rate == 0.0
    
    # 只有命中
    await cache.set("key", "value")
    assert await cache.get("key") == "value"  # 命中
    assert cache.hit_rate == 1.0
    
    # 只有未命中
    assert await cache.get("not_exists") is None  # 未命中
    assert cache.hit_rate == 0.5  # (1 命中 + 1 未命中)

@pytest.mark.asyncio
async def test_cache_ttl_edge_cases():
    """测试缓存 TTL 边缘情况"""
    cache = TestCache("test")
    
    # 设置带 TTL 的值
    await cache.set("key1", "value1", ttl=0.1)  # 很短的 TTL
    await cache.set("key2", "value2")  # 无 TTL
    
    # 验证 TTL
    assert await cache.ttl("key1") > 0  # 有 TTL
    assert await cache.ttl("key2") is None  # 无 TTL
    assert await cache.ttl("key3") is None  # 不存在的键
    
    # 等待过期
    await asyncio.sleep(0.2)
    assert await cache.get("key1") is None  # 已过期
    assert await cache.get("key2") == "value2"  # 永不过期
    
    # 测试过期时间设置
    await cache.set("key3", "value3")
    assert not await cache.expire("not_exists", 1)  # 不存在的键
    assert await cache.expire("key3", 1)  # 存在的键
    await asyncio.sleep(1.1)
    assert await cache.get("key3") is None  # 已过期

@pytest.mark.asyncio
async def test_cache_manager_edge_cases():
    """测试缓存管理器边缘情况"""
    manager = CacheManager()
    cache1 = TestCache("cache1")
    
    # 测试重复注册
    manager.register_cache("cache1", cache1)
    manager.register_cache("cache1", cache1)  # 重复注册
    assert manager.get_cache("cache1") == cache1
    
    # 测试获取不存在的缓存
    with pytest.raises(KeyError, match="缓存不存在: not_exists"):
        manager.get_cache("not_exists")
    
    # 测试空缓存管理器
    empty_manager = CacheManager()
    with pytest.raises(KeyError, match="缓存不存在: any"):
        empty_manager.get_cache("any")

@pytest.mark.asyncio
async def test_cache_operations_edge_cases():
    """测试缓存操作边缘情况"""
    cache = TestCache("test")
    
    # 测试删除不存在的键
    assert not await cache.delete("not_exists")
    
    # 测试清空空缓存
    await cache.clear()  # 不应抛出异常
    
    # 测试批量操作空列表
    assert await cache.multi_get([]) == {}
    await cache.multi_set({})  # 不应抛出异常
    
    # 测试批量操作单个值
    await cache.multi_set({"key": "value"})
    assert await cache.multi_get(["key"]) == {"key": "value"}
    
    # 测试批量操作多个值（包括不存在的键）
    await cache.multi_set({"key1": "value1", "key2": "value2"})
    result = await cache.multi_get(["key1", "not_exists", "key2"])
    assert result == {"key1": "value1", "key2": "value2"}

@pytest.mark.asyncio
async def test_cache_hit_rate_zero_access():
    """测试缓存命中率 - 无访问"""
    cache = TestCache()
    assert cache.hit_rate == 0.0

@pytest.mark.asyncio
async def test_cache_hit_rate_all_hits():
    """测试缓存命中率 - 全部命中"""
    cache = TestCache()
    cache._update_metrics(hit=True)
    cache._update_metrics(hit=True)
    assert cache.hit_rate == 1.0

@pytest.mark.asyncio
async def test_cache_hit_rate_mixed():
    """测试缓存命中率 - 混合访问"""
    cache = TestCache()
    cache._update_metrics(hit=True)
    cache._update_metrics(hit=False)
    cache._update_metrics(hit=True)
    assert cache.hit_rate == 2/3

@pytest.mark.asyncio
async def test_cache_manager_complex():
    """测试缓存管理器复杂操作"""
    manager = CacheManager()
    cache1 = TestCache()
    cache2 = TestCache()
    
    # 测试注册缓存
    manager.register_cache("cache1", cache1)
    manager.register_cache("cache2", cache2)
    
    # 测试获取不存在的缓存
    with pytest.raises(KeyError, match="缓存不存在: not_exists"):
        manager.get_cache("not_exists")
    
    # 测试重复注册
    new_cache1 = TestCache()
    manager.register_cache("cache1", new_cache1)
    
    # 测试清空所有缓存
    await new_cache1.set("key1", "value1")
    await cache2.set("key2", "value2")
    await manager.clear_all()
    await asyncio.sleep(0.1)  # 等待清空操作完成
    assert await new_cache1.get("key1") is None
    assert await cache2.get("key2") is None
    
    # 重置指标
    new_cache1._metrics = {"hits": 0, "misses": 0, "size": 0, "evictions": 0}
    cache2._metrics = {"hits": 0, "misses": 0, "size": 0, "evictions": 0}
    
    # 测试获取所有指标
    await new_cache1.set("key1", "value1")
    await new_cache1.get("key1")
    await cache2.set("key2", "value2")
    await cache2.get("key2")
    await cache2.get("key3")  # miss
    
    metrics = await manager.get_all_metrics()
    assert len(metrics) == 2
    assert metrics["cache1"]["hits"] == 1
    assert metrics["cache1"]["misses"] == 0
    assert metrics["cache2"]["hits"] == 1
    assert metrics["cache2"]["misses"] == 1

@pytest.mark.asyncio
async def test_cache_operations_complex():
    """测试复杂的缓存操作"""
    cache = TestCache()
    
    # 批量设置和获取
    await cache.set("key1", "value1")
    await cache.set("key2", "value2")
    await cache.set("key3", "value3")
    
    assert await cache.get("key1") == "value1"
    assert await cache.get("key2") == "value2"
    assert await cache.get("key3") == "value3"
    assert await cache.get("key4") is None
    
    # 测试过期
    await cache.set("key_ttl", "value_ttl", ttl=1)
    assert await cache.get("key_ttl") == "value_ttl"
    await asyncio.sleep(1.1)
    assert await cache.get("key_ttl") is None
    
    # 测试清空缓存
    await cache.clear()
    assert await cache.get("key1") is None
    assert await cache.get("key2") is None
    assert await cache.get("key3") is None
    
    # 验证指标
    metrics = await cache.get_metrics()
    assert metrics["hits"] > 0
    assert metrics["misses"] > 0
    assert 0 <= cache.hit_rate <= 1

@pytest.mark.asyncio
async def test_cache_hit_rate_edge_cases_2():
    """测试缓存命中率边缘情况 2"""
    cache = TestCache("test")
    
    # 初始状态（无访问）
    assert cache.hit_rate == 0.0
    
    # 只有未命中
    for i in range(10):
        assert await cache.get(f"not_exists_{i}") is None
    assert cache.hit_rate == 0.0
    
    # 设置一个值并访问
    await cache.set("key", "value")
    assert await cache.get("key") == "value"
    assert cache.hit_rate == 1/11  # 1 命中 / 11 总访问

@pytest.mark.asyncio
async def test_cache_manager_edge_cases_2():
    """测试缓存管理器边缘情况 2"""
    manager = CacheManager()
    cache1 = TestCache("cache1")
    cache2 = TestCache("cache2")
    
    # 测试注册缓存
    manager.register_cache("cache1", cache1)
    manager.register_cache("cache2", cache2)
    
    # 测试获取缓存
    assert manager.get_cache("cache1") == cache1
    assert manager.get_cache("cache2") == cache2
    
    # 测试重复注册（覆盖）
    cache3 = TestCache("cache3")
    manager.register_cache("cache1", cache3)  # 覆盖 cache1
    assert manager.get_cache("cache1") == cache3
    
    # 测试获取不存在的缓存
    with pytest.raises(KeyError, match="缓存不存在: not_exists"):
        manager.get_cache("not_exists")
    
    # 测试空缓存管理器
    empty_manager = CacheManager()
    with pytest.raises(KeyError, match="缓存不存在: any"):
        empty_manager.get_cache("any")
    
    # 测试多次重复注册
    manager.register_cache("cache1", cache1)  # 覆盖回 cache1
    manager.register_cache("cache1", cache1)  # 重复注册相同的缓存
    assert manager.get_cache("cache1") == cache1
    
    # 测试注册多个缓存
    for i in range(10):
        cache = TestCache(f"cache{i}")
        manager.register_cache(f"cache{i}", cache)
        assert manager.get_cache(f"cache{i}") == cache

@pytest.mark.asyncio
async def test_cache_operations_edge_cases_2():
    """测试缓存操作边缘情况 2"""
    cache = TestCache("test")
    
    # 测试空操作
    assert await cache.multi_get([]) == {}
    await cache.multi_set({})
    
    # 测试单个值
    await cache.multi_set({"key": "value"})
    assert await cache.multi_get(["key"]) == {"key": "value"}
    
    # 测试多个值
    mapping = {f"key{i}": f"value{i}" for i in range(10)}
    await cache.multi_set(mapping)
    result = await cache.multi_get([f"key{i}" for i in range(10)])
    assert result == mapping
    
    # 测试不存在的键
    result = await cache.multi_get(["not_exists1", "not_exists2"])
    assert result == {}
    
    # 测试混合键
    result = await cache.multi_get(["key0", "not_exists", "key1"])
    assert result == {"key0": "value0", "key1": "value1"}
    
    # 测试过期时间
    await cache.set("key", "value", ttl=0.1)
    assert await cache.get("key") == "value"
    await asyncio.sleep(0.2)
    assert await cache.get("key") is None
    
    # 测试设置过期时间
    await cache.set("key", "value")
    assert await cache.expire("key", 0.1)
    assert await cache.get("key") == "value"
    await asyncio.sleep(0.2)
    assert await cache.get("key") is None
    
    # 测试不存在的键设置过期时间
    assert not await cache.expire("not_exists", 1) 

@pytest.mark.asyncio
async def test_base_cache_ttl():
    """测试基础缓存的TTL默认实现"""
    class MinimalCache(BaseCache):
        """最小化缓存实现"""
        def __init__(self):
            super().__init__("minimal")
            
        async def get(self, key: str): pass
        async def set(self, key: str, value, ttl=None): pass
        async def delete(self, key: str): pass
        async def exists(self, key: str): pass
        async def clear(self): pass
        async def get_metrics(self): pass
    
    cache = MinimalCache()
    assert await cache.ttl("any_key") is None 