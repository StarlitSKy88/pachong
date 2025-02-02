"""缓存管理模块"""

import time
import asyncio
from typing import Dict, Any, Optional, List, Union, TypeVar, Generic
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from ..utils.logger import get_logger

T = TypeVar("T")

class CacheEntry(Generic[T]):
    """缓存条目"""
    
    def __init__(
        self,
        key: str,
        value: T,
        ttl: Optional[int] = None,
        version: int = 1
    ):
        """初始化缓存条目
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
            version: 版本号
        """
        self.key = key
        self.value = value
        self.created_at = time.time()
        self.accessed_at = time.time()
        self.ttl = ttl
        self.version = version
        self.hits = 0
        
    @property
    def expired(self) -> bool:
        """是否已过期"""
        if self.ttl is None:
            return False
        return time.time() > self.created_at + self.ttl
        
    def access(self) -> None:
        """访问缓存条目"""
        self.accessed_at = time.time()
        self.hits += 1
        
    def update(self, value: T, version: int) -> None:
        """更新缓存条目
        
        Args:
            value: 新值
            version: 新版本号
        """
        self.value = value
        self.version = version
        self.created_at = time.time()
        self.accessed_at = time.time()

class BaseCache(ABC):
    """缓存基类"""
    
    def __init__(self, name: str):
        """初始化缓存
        
        Args:
            name: 缓存名称
        """
        self.name = name
        self.logger = get_logger(f"{name}_cache")
        self._metrics = {
            "hits": 0,
            "misses": 0,
            "size": 0,
            "evictions": 0
        }
        
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            Optional[Any]: 缓存值
        """
        pass
        
    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> None:
        """设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
        """
        pass
        
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """删除缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否删除成功
        """
        pass
        
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """检查缓存键是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否存在
        """
        pass
        
    @abstractmethod
    async def clear(self) -> None:
        """清空缓存"""
        pass
        
    @abstractmethod
    async def get_metrics(self) -> Dict[str, Any]:
        """获取缓存指标
        
        Returns:
            Dict[str, Any]: 缓存指标
        """
        pass
        
    async def multi_get(self, keys: List[str]) -> Dict[str, Any]:
        """批量获取缓存值
        
        Args:
            keys: 缓存键列表
            
        Returns:
            Dict[str, Any]: 缓存值字典
        """
        results = {}
        for key in keys:
            value = await self.get(key)
            if value is not None:
                results[key] = value
        return results
        
    async def multi_set(
        self,
        mapping: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> None:
        """批量设置缓存值
        
        Args:
            mapping: 缓存键值映射
            ttl: 过期时间（秒）
        """
        for key, value in mapping.items():
            await self.set(key, value, ttl)
            
    async def expire(self, key: str, ttl: int) -> bool:
        """设置缓存过期时间
        
        Args:
            key: 缓存键
            ttl: 过期时间（秒）
            
        Returns:
            bool: 是否设置成功
        """
        if not await self.exists(key):
            return False
            
        value = await self.get(key)
        await self.set(key, value, ttl)
        return True
        
    async def ttl(self, key: str) -> Optional[int]:
        """获取缓存剩余过期时间
        
        Args:
            key: 缓存键
            
        Returns:
            Optional[int]: 剩余过期时间（秒）
        """
        return None  # 由子类实现
        
    def _update_metrics(self, hit: bool = True) -> None:
        """更新缓存指标
        
        Args:
            hit: 是否命中缓存
        """
        if hit:
            self._metrics["hits"] += 1
        else:
            self._metrics["misses"] += 1
            
    @property
    def hit_rate(self) -> float:
        """缓存命中率"""
        total = self._metrics["hits"] + self._metrics["misses"]
        return self._metrics["hits"] / total if total > 0 else 0.0

class CacheManager:
    """缓存管理器"""
    
    def __init__(self):
        """初始化缓存管理器"""
        self.logger = get_logger("cache_manager")
        self.caches: Dict[str, BaseCache] = {}
        
    def register_cache(self, name: str, cache: BaseCache) -> None:
        """注册缓存
        
        Args:
            name: 缓存名称
            cache: 缓存实例
        """
        self.caches[name] = cache
        self.logger.info(f"已注册缓存: {name}")
        
    def get_cache(self, name: str) -> BaseCache:
        """获取缓存
        
        Args:
            name: 缓存名称
            
        Returns:
            BaseCache: 缓存实例
            
        Raises:
            KeyError: 当缓存不存在时
        """
        if name not in self.caches:
            raise KeyError(f"缓存不存在: {name}")
        return self.caches[name]
        
    async def clear_all(self) -> None:
        """清空所有缓存"""
        for cache in self.caches.values():
            await cache.clear()
        self.logger.info("所有缓存已清空")
        
    async def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """获取所有缓存指标
        
        Returns:
            Dict[str, Dict[str, Any]]: 缓存指标
        """
        metrics = {}
        for name, cache in self.caches.items():
            metrics[name] = await cache.get_metrics()
        return metrics 