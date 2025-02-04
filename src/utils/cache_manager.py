"""缓存管理模块"""

import json
import time
from typing import Any, Dict, List, Optional, Union
from collections import OrderedDict
import threading
from datetime import datetime
import asyncio

class CacheEntry:
    """缓存条目"""
    
    def __init__(self, key: str, value: Any, ttl: Optional[float] = None):
        """初始化缓存条目。
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
        """
        self.key = key
        self.value = value
        self.ttl = ttl
        self.version = 1
        self.hits = 0
        self.created_at = datetime.now().timestamp()
        
    def access(self):
        """访问缓存条目"""
        self.hits += 1
        
    def update(self, value: Any, ttl: Optional[float] = None):
        """更新缓存条目。
        
        Args:
            value: 新的缓存值
            ttl: 新的过期时间（秒）
        """
        self.value = value
        self.ttl = ttl
        self.version += 1
        self.created_at = datetime.now().timestamp()
        
    @property
    def expired(self) -> bool:
        """是否已过期"""
        if self.ttl is None:
            return False
        return datetime.now().timestamp() - self.created_at >= self.ttl

class BaseCache:
    """缓存基类"""
    
    def __init__(self, name: Optional[str] = None):
        """初始化缓存。
        
        Args:
            name: 缓存名称
        """
        self.name = name or self.__class__.__name__
        self._metrics = {
            "hits": 0,
            "misses": 0,
            "size": 0,
            "evictions": 0
        }
        self._lock = asyncio.Lock()
        
    def _update_metrics(self, hit: bool = True):
        """更新指标。
        
        Args:
            hit: 是否命中
        """
        if hit:
            self._metrics["hits"] += 1
        else:
            self._metrics["misses"] += 1
            
    @property
    def hit_rate(self) -> float:
        """获取命中率"""
        total = self._metrics["hits"] + self._metrics["misses"]
        if total == 0:
            return 0.0
        return self._metrics["hits"] / total
        
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值。
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在或已过期则返回 None
        """
        raise NotImplementedError
        
    async def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """设置缓存值。
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
        """
        raise NotImplementedError
        
    async def delete(self, key: str) -> bool:
        """删除缓存值。
        
        Args:
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        raise NotImplementedError
        
    async def exists(self, key: str) -> bool:
        """检查缓存键是否存在。
        
        Args:
            key: 缓存键
            
        Returns:
            是否存在
        """
        raise NotImplementedError
        
    async def clear(self) -> None:
        """清空缓存"""
        raise NotImplementedError
        
    async def get_metrics(self) -> Dict[str, int]:
        """获取缓存指标。
        
        Returns:
            指标字典
        """
        return self._metrics
        
    async def multi_get(self, keys: List[str]) -> Dict[str, Any]:
        """批量获取缓存值。
        
        Args:
            keys: 缓存键列表
            
        Returns:
            缓存值字典
        """
        result = {}
        for key in keys:
            value = await self.get(key)
            if value is not None:
                result[key] = value
        return result
        
    async def multi_set(self, mapping: Dict[str, Any], ttl: Optional[float] = None) -> None:
        """批量设置缓存值。
        
        Args:
            mapping: 键值映射
            ttl: 过期时间（秒）
        """
        for key, value in mapping.items():
            await self.set(key, value, ttl)
            
    async def expire(self, key: str, ttl: float) -> bool:
        """设置过期时间。
        
        Args:
            key: 缓存键
            ttl: 过期时间（秒）
            
        Returns:
            是否设置成功
        """
        if not await self.exists(key):
            return False
        value = await self.get(key)
        await self.set(key, value, ttl)
        return True
        
    async def ttl(self, key: str) -> Optional[float]:
        """获取剩余过期时间。
        
        Args:
            key: 缓存键
            
        Returns:
            剩余时间（秒），如果键不存在或没有设置过期时间则返回 None
        """
        raise NotImplementedError

class Cache(BaseCache):
    """内存缓存实现"""
    
    def __init__(self, name: Optional[str] = None):
        """初始化缓存。
        
        Args:
            name: 缓存名称
        """
        super().__init__(name)
        self._cache: Dict[str, CacheEntry] = {}
        
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值。
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在或已过期则返回 None
        """
        async with self._lock:
            if key not in self._cache:
                self._update_metrics(hit=False)
                return None
                
            entry = self._cache[key]
            if entry.expired:
                await self.delete(key)
                self._update_metrics(hit=False)
                return None
                
            entry.access()
            self._update_metrics(hit=True)
            return entry.value
            
    async def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """设置缓存值。
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
        """
        async with self._lock:
            if key in self._cache:
                self._cache[key].update(value, ttl)
            else:
                self._cache[key] = CacheEntry(key, value, ttl)
            self._metrics["size"] = len(self._cache)
            
    async def delete(self, key: str) -> bool:
        """删除缓存值。
        
        Args:
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._metrics["size"] = len(self._cache)
                return True
            return False
            
    async def exists(self, key: str) -> bool:
        """检查缓存键是否存在。
        
        Args:
            key: 缓存键
            
        Returns:
            是否存在
        """
        async with self._lock:
            if key not in self._cache:
                return False
            if self._cache[key].expired:
                await self.delete(key)
                return False
            return True
            
    async def clear(self) -> None:
        """清空缓存"""
        async with self._lock:
            self._cache.clear()
            self._metrics["size"] = 0
            self._metrics["evictions"] += 1
            
    async def ttl(self, key: str) -> Optional[float]:
        """获取剩余过期时间。
        
        Args:
            key: 缓存键
            
        Returns:
            剩余时间（秒），如果键不存在或没有设置过期时间则返回 None
        """
        async with self._lock:
            if key not in self._cache:
                return None
            entry = self._cache[key]
            if entry.ttl is None:
                return None
            remaining = entry.ttl - (datetime.now().timestamp() - entry.created_at)
            return max(0, remaining)

class CacheManager:
    """缓存管理器"""
    
    def __init__(self):
        """初始化缓存管理器"""
        self._caches: Dict[str, BaseCache] = {}
        
    def register_cache(self, name: str, cache: BaseCache) -> None:
        """注册缓存。
        
        Args:
            name: 缓存名称
            cache: 缓存实例
        """
        self._caches[name] = cache
        
    def get_cache(self, name: str) -> BaseCache:
        """获取缓存。
        
        Args:
            name: 缓存名称
            
        Returns:
            缓存实例
            
        Raises:
            KeyError: 缓存不存在
        """
        if name not in self._caches:
            raise KeyError(f"Cache not found: {name}")
        return self._caches[name] 