"""缓存同步模块"""

import asyncio
import json
from typing import Dict, Any, Optional, List, Set, Callable
from datetime import datetime
from .cache_manager import BaseCache
from ..utils.logger import get_logger

class CacheEvent:
    """缓存事件"""
    
    def __init__(
        self,
        event_type: str,
        key: str,
        value: Optional[Any] = None,
        ttl: Optional[int] = None,
        version: int = 1,
        timestamp: Optional[float] = None
    ):
        """初始化缓存事件
        
        Args:
            event_type: 事件类型（set/delete/clear）
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
            version: 版本号
            timestamp: 时间戳
        """
        self.event_type = event_type
        self.key = key
        self.value = value
        self.ttl = ttl
        self.version = version
        self.timestamp = timestamp or datetime.now().timestamp()
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            Dict[str, Any]: 事件字典
        """
        return {
            "event_type": self.event_type,
            "key": self.key,
            "value": self.value,
            "ttl": self.ttl,
            "version": self.version,
            "timestamp": self.timestamp
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CacheEvent":
        """从字典创建事件
        
        Args:
            data: 事件字典
            
        Returns:
            CacheEvent: 事件实例
        """
        return cls(
            event_type=data["event_type"],
            key=data["key"],
            value=data["value"],
            ttl=data["ttl"],
            version=data["version"],
            timestamp=data["timestamp"]
        )

class CacheEventBus:
    """缓存事件总线"""
    
    def __init__(self, name: str):
        """初始化事件总线
        
        Args:
            name: 事件总线名称
        """
        self.name = name
        self.logger = get_logger(f"{name}_event_bus")
        self.subscribers: Dict[str, Set[Callable]] = {}
        
    def subscribe(self, event_type: str, callback: Callable) -> None:
        """订阅事件
        
        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = set()
        self.subscribers[event_type].add(callback)
        
    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        """取消订阅事件
        
        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        if event_type in self.subscribers:
            self.subscribers[event_type].discard(callback)
            
    async def publish(self, event: CacheEvent) -> None:
        """发布事件
        
        Args:
            event: 缓存事件
        """
        if event.event_type not in self.subscribers:
            return
            
        for callback in self.subscribers[event.event_type]:
            try:
                await callback(event)
            except Exception as e:
                self.logger.error(f"处理事件失败: {str(e)}")

class CacheSyncManager:
    """缓存同步管理器"""
    
    def __init__(
        self,
        name: str,
        local_cache: BaseCache,
        remote_cache: BaseCache,
        event_bus: Optional[CacheEventBus] = None,
        sync_interval: int = 60
    ):
        """初始化缓存同步管理器
        
        Args:
            name: 同步管理器名称
            local_cache: 本地缓存
            remote_cache: 远程缓存
            event_bus: 事件总线
            sync_interval: 同步间隔（秒）
        """
        self.name = name
        self.logger = get_logger(f"{name}_sync")
        self.local_cache = local_cache
        self.remote_cache = remote_cache
        self.event_bus = event_bus or CacheEventBus(f"{name}_event_bus")
        self.sync_interval = sync_interval
        self._sync_task = None
        self._running = False
        self._versions = {}  # 存储每个键的最新版本
        
        # 订阅事件
        self.event_bus.subscribe("set", self._handle_set_event)
        self.event_bus.subscribe("delete", self._handle_delete_event)
        self.event_bus.subscribe("clear", self._handle_clear_event)
        
    async def start(self) -> None:
        """启动同步管理器"""
        if self._running:
            return
            
        self._running = True
        self._sync_task = asyncio.create_task(self._sync_loop())
        self.logger.info(f"{self.name} 同步管理器已启动")
        
    async def stop(self) -> None:
        """停止同步管理器"""
        if not self._running:
            return
            
        self._running = False
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
            self._sync_task = None
            
        self.logger.info(f"{self.name} 同步管理器已停止")
        
    async def _sync_loop(self) -> None:
        """同步循环"""
        while self._running:
            try:
                await self._sync_caches()
                await asyncio.sleep(self.sync_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"同步缓存失败: {str(e)}")
                await asyncio.sleep(1)
                
    async def _sync_caches(self) -> None:
        """同步缓存"""
        try:
            # 获取远程缓存的所有键
            pattern = f"{self.remote_cache.prefix}*"
            cursor = 0
            while True:
                cursor, keys = await self.remote_cache.scan(
                    cursor=cursor,
                    match=pattern,
                    count=100
                )
                
                # 处理每个键
                for key in keys:
                    # 获取远程值和TTL
                    value = await self.remote_cache.get(key)
                    ttl = await self.remote_cache.ttl(key)
                    
                    # 更新本地缓存
                    if value is not None:
                        await self.local_cache.set(key, value, ttl)
                        
                if cursor == 0:
                    break
                    
        except Exception as e:
            self.logger.error(f"同步缓存失败: {str(e)}")
            
    async def _handle_set_event(self, event: CacheEvent) -> None:
        """处理设置事件"""
        try:
            # 检查版本
            current_version = self._versions.get(event.key, 0)
            if event.version <= current_version:
                return
                
            # 更新版本
            self._versions[event.key] = event.version
            
            # 更新远程缓存
            await self.remote_cache.set(
                event.key,
                event.value,
                event.ttl
            )
            
            # 更新本地缓存
            await self.local_cache.set(
                event.key,
                event.value,
                event.ttl
            )
            
        except Exception as e:
            self.logger.error(f"处理设置事件失败: {str(e)}")
            
    async def _handle_delete_event(self, event: CacheEvent) -> None:
        """处理删除事件"""
        try:
            # 检查版本
            current_version = self._versions.get(event.key, 0)
            if event.version <= current_version:
                return
                
            # 更新版本
            self._versions[event.key] = event.version
            
            # 删除远程缓存
            await self.remote_cache.delete(event.key)
            
            # 删除本地缓存
            await self.local_cache.delete(event.key)
            
        except Exception as e:
            self.logger.error(f"处理删除事件失败: {str(e)}")
            
    async def _handle_clear_event(self, event: CacheEvent) -> None:
        """处理清空事件"""
        try:
            # 清空远程缓存
            await self.remote_cache.clear()
            
            # 清空本地缓存
            await self.local_cache.clear()
            
            # 清空版本信息
            self._versions.clear()
            
        except Exception as e:
            self.logger.error(f"处理清空事件失败: {str(e)}")
            
    async def publish_event(self, event: CacheEvent) -> None:
        """发布事件
        
        Args:
            event: 缓存事件
        """
        # 处理事件
        if event.event_type == "set":
            await self._handle_set_event(event)
        elif event.event_type == "delete":
            await self._handle_delete_event(event)
        elif event.event_type == "clear":
            await self._handle_clear_event(event)
            
        # 发布事件
        await self.event_bus.publish(event) 