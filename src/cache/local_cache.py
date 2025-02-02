"""本地缓存模块"""

import time
import asyncio
import threading
from typing import Dict, Any, Optional, List
from collections import OrderedDict
from .cache_manager import BaseCache, CacheEntry

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
        
    async def start(self) -> None:
        """启动缓存"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            self.logger.info(f"{self.name} 缓存已启动")
            
    async def stop(self) -> None:
        """停止缓存"""
        if self._cleanup_task is not None:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            self.logger.info(f"{self.name} 缓存已停止")
            
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self._lock:
            if key not in self._cache:
                self._update_metrics(hit=False)
                return None
                
            entry = self._cache[key]
            
            # 检查是否过期
            if entry.expired:
                del self._cache[key]
                self._update_metrics(hit=False)
                return None
                
            # 更新访问时间和命中次数
            entry.access()
            
            # 移动到最后（最近使用）
            self._cache.move_to_end(key)
            
            self._update_metrics(hit=True)
            return entry.value
            
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> None:
        """设置缓存值"""
        with self._lock:
            # 如果已存在，更新值
            if key in self._cache:
                entry = self._cache[key]
                entry.update(value, entry.version + 1)
                self._cache.move_to_end(key)
                return
                
            # 如果达到最大大小，移除最早的条目
            while len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)
                self._metrics["evictions"] += 1
                
            # 添加新条目
            entry = CacheEntry(key, value, ttl)
            self._cache[key] = entry
            self._metrics["size"] = len(self._cache)
            
    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._metrics["size"] = len(self._cache)
                return True
            return False
            
    async def exists(self, key: str) -> bool:
        """检查缓存键是否存在"""
        with self._lock:
            if key not in self._cache:
                return False
                
            entry = self._cache[key]
            if entry.expired:
                del self._cache[key]
                return False
                
            return True
            
    async def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._metrics["size"] = 0
            
    async def get_metrics(self) -> Dict[str, Any]:
        """获取缓存指标"""
        with self._lock:
            self._metrics.update({
                "max_size": self.max_size,
                "current_size": len(self._cache),
                "hit_rate": self.hit_rate
            })
            return self._metrics
            
    async def ttl(self, key: str) -> Optional[int]:
        """获取缓存剩余过期时间"""
        with self._lock:
            if key not in self._cache:
                return None
                
            entry = self._cache[key]
            if entry.ttl is None:
                return None
                
            remaining = entry.created_at + entry.ttl - time.time()
            return max(0, int(remaining))
            
    async def _cleanup_loop(self) -> None:
        """清理过期缓存的循环"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"清理缓存时出错: {str(e)}")
                
    async def _cleanup_expired(self) -> None:
        """清理过期的缓存条目"""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.expired
            ]
            for key in expired_keys:
                del self._cache[key]
            self._metrics["size"] = len(self._cache)
            
    async def multi_get(self, keys: List[str]) -> Dict[str, Any]:
        """批量获取缓存值"""
        results = {}
        with self._lock:
            for key in keys:
                if key in self._cache:
                    entry = self._cache[key]
                    if not entry.expired:
                        entry.access()
                        self._cache.move_to_end(key)
                        results[key] = entry.value
                        self._update_metrics(hit=True)
                    else:
                        del self._cache[key]
                        self._update_metrics(hit=False)
                else:
                    self._update_metrics(hit=False)
        return results
        
    async def multi_set(
        self,
        mapping: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> None:
        """批量设置缓存值"""
        with self._lock:
            for key, value in mapping.items():
                # 如果已存在，更新值
                if key in self._cache:
                    entry = self._cache[key]
                    entry.update(value, entry.version + 1)
                    self._cache.move_to_end(key)
                    continue
                    
                # 如果达到最大大小，移除最早的条目
                while len(self._cache) >= self.max_size:
                    self._cache.popitem(last=False)
                    self._metrics["evictions"] += 1
                    
                # 添加新条目
                entry = CacheEntry(key, value, ttl)
                self._cache[key] = entry
                
            self._metrics["size"] = len(self._cache) 