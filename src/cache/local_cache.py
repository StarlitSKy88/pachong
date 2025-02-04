"""本地缓存模块"""

import time
import asyncio
import threading
from typing import Dict, Any, Optional, List
from collections import OrderedDict
from .cache_manager import BaseCache, CacheEntry
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class LRUCache(BaseCache):
    """LRU缓存实现"""
    
    def __init__(
        self,
        name: str,
        max_size: int = 1000,
        cleanup_interval: int = 60
    ):
        """初始化LRU缓存
        
        Args:
            name: 缓存名称
            max_size: 最大缓存条目数
            cleanup_interval: 清理间隔（秒）
        """
        super().__init__(name)
        self.max_size = max_size
        self.cleanup_interval = cleanup_interval
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.Lock()
        self._cleanup_task = None
        self._metrics = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "size": 0,
            "max_size": max_size,
            "current_size": 0
        }
        
    async def start(self) -> None:
        """启动缓存"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info(f"{self.name} 缓存已启动")
            
    async def stop(self) -> None:
        """停止缓存"""
        if self._cleanup_task is not None:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info(f"{self.name} 缓存已停止")
            
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值。
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在或已过期则返回 None
        """
        with self._lock:
            if key not in self._cache:
                self._update_metrics(hit=False)
                return None
                
            entry = self._cache[key]
            if entry.expired:
                # 直接在当前锁内删除过期的键
                del self._cache[key]
                self._metrics["current_size"] = len(self._cache)
                self._update_metrics(hit=False)
                return None
                
            # 更新LRU顺序
            self._cache.move_to_end(key)
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
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                self._cache[key].update(value, ttl)
            else:
                # 检查容量
                if len(self._cache) >= self.max_size:
                    # 移除最久未使用的条目
                    self._cache.popitem(last=False)
                    self._metrics["evictions"] += 1
                    
                self._cache[key] = CacheEntry(key, value, ttl)
                self._cache.move_to_end(key)
                
            self._metrics["current_size"] = len(self._cache)
            
    async def delete(self, key: str) -> bool:
        """删除缓存值。
        
        Args:
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._metrics["current_size"] = len(self._cache)
                return True
            return False
            
    async def exists(self, key: str) -> bool:
        """检查缓存键是否存在。
        
        Args:
            key: 缓存键
            
        Returns:
            是否存在
        """
        with self._lock:
            if key not in self._cache:
                return False
            if self._cache[key].expired:
                # 直接在当前锁内删除过期的键
                del self._cache[key]
                self._metrics["current_size"] = len(self._cache)
                return False
            return True
            
    async def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._metrics["current_size"] = 0
            self._metrics["evictions"] += 1
            
    async def get_metrics(self) -> Dict[str, Any]:
        """获取缓存指标。
        
        Returns:
            指标字典
        """
        with self._lock:
            metrics = self._metrics.copy()
            total = metrics["hits"] + metrics["misses"]
            hit_rate = metrics["hits"] / total if total > 0 else 0.0
            
            metrics.update({
                "max_size": self.max_size,
                "current_size": len(self._cache),
                "hit_rate": hit_rate
            })
            return metrics
            
    async def ttl(self, key: str) -> Optional[float]:
        """获取缓存剩余过期时间。
        
        Args:
            key: 缓存键
            
        Returns:
            剩余时间（秒），如果键不存在或没有设置过期时间则返回 None
        """
        with self._lock:
            if key not in self._cache:
                return None
                
            entry = self._cache[key]
            if entry.ttl is None:
                return None
                
            remaining = entry.created_at + entry.ttl - time.time()
            return max(0, remaining)
            
    async def _cleanup_loop(self) -> None:
        """清理过期缓存的循环"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"清理缓存时出错: {str(e)}")
                
    async def _cleanup_expired(self) -> None:
        """清理过期的缓存条目"""
        with self._lock:
            # 找出所有过期的键
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.expired
            ]
            
            # 删除过期的键
            for key in expired_keys:
                del self._cache[key]
                
            # 更新指标
            self._metrics["current_size"] = len(self._cache)
            self._metrics["evictions"] += len(expired_keys)
            
            if expired_keys:
                logger.debug(f"已清理 {len(expired_keys)} 个过期缓存条目")
                
    async def multi_get(self, keys: List[str]) -> Dict[str, Any]:
        """批量获取缓存值。
        
        Args:
            keys: 缓存键列表
            
        Returns:
            缓存值字典
        """
        results = {}
        with self._lock:
            for key in keys:
                if key in self._cache:
                    entry = self._cache[key]
                    if not entry.expired:
                        self._cache.move_to_end(key)
                        entry.access()
                        results[key] = entry.value
                        self._update_metrics(hit=True)
                    else:
                        del self._cache[key]
                        self._metrics["current_size"] = len(self._cache)
                        self._update_metrics(hit=False)
                else:
                    self._update_metrics(hit=False)
        return results
        
    async def multi_set(
        self,
        mapping: Dict[str, Any],
        ttl: Optional[float] = None
    ) -> None:
        """批量设置缓存值。
        
        Args:
            mapping: 缓存键值映射
            ttl: 过期时间（秒）
        """
        with self._lock:
            for key, value in mapping.items():
                if key in self._cache:
                    self._cache.move_to_end(key)
                    self._cache[key].update(value, ttl)
                else:
                    # 检查容量
                    if len(self._cache) >= self.max_size:
                        # 移除最久未使用的条目
                        self._cache.popitem(last=False)
                        self._metrics["evictions"] += 1
                        
                    self._cache[key] = CacheEntry(key, value, ttl)
                    self._cache.move_to_end(key)
                    
            self._metrics["current_size"] = len(self._cache)
            
    def _update_metrics(self, hit: bool = True):
        """更新指标。
        
        Args:
            hit: 是否命中
        """
        if hit:
            self._metrics["hits"] += 1
        else:
            self._metrics["misses"] += 1
            
    async def hit_rate(self) -> float:
        """获取缓存命中率"""
        with self._lock:
            total = self._metrics["hits"] + self._metrics["misses"]
            return self._metrics["hits"] / total if total > 0 else 0.0
            
    async def expire(self, key: str, ttl: float) -> bool:
        """设置过期时间。
        
        Args:
            key: 缓存键
            ttl: 过期时间（秒）
            
        Returns:
            是否设置成功
        """
        with self._lock:
            if key not in self._cache:
                return False
            self._cache[key].ttl = ttl
            self._cache[key].created_at = datetime.now().timestamp()
            return True 