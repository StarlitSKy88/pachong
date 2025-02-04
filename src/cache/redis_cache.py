"""Redis缓存模块"""

import json
import time
import asyncio
from typing import Dict, Any, Optional, List, Union, AsyncContextManager
from contextlib import asynccontextmanager
from redis.asyncio import Redis
from .cache_manager import BaseCache, CacheEntry

class RedisCache(BaseCache):
    """Redis缓存实现"""
    
    def __init__(
        self,
        name: str,
        redis: Redis,
        prefix: str = "cache:",
        default_ttl: Optional[int] = None,
        serializer: Optional[callable] = None,
        deserializer: Optional[callable] = None
    ):
        """初始化Redis缓存
        
        Args:
            name: 缓存名称
            redis: Redis客户端实例
            prefix: 键前缀
            default_ttl: 默认过期时间（秒）
            serializer: 序列化函数
            deserializer: 反序列化函数
        """
        super().__init__(name)
        self.redis = redis
        self.prefix = prefix
        self.default_ttl = default_ttl
        self.serializer = serializer or json.dumps
        self.deserializer = deserializer or json.loads
        
    def _make_key(self, key: str) -> str:
        """生成完整的缓存键
        
        Args:
            key: 原始键
            
        Returns:
            str: 完整的缓存键
        """
        return f"{self.prefix}{key}"
        
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        try:
            value = await self.redis.get(self._make_key(key))
            if value is None:
                self._update_metrics(hit=False)
                return None
                
            self._update_metrics(hit=True)
            return self.deserializer(value)
            
        except Exception as e:
            self.logger.error(f"获取缓存失败: {str(e)}")
            return None
            
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> None:
        """设置缓存值"""
        try:
            full_key = self._make_key(key)
            serialized = self.serializer(value)
            
            if ttl is None:
                ttl = self.default_ttl
                
            if ttl is not None:
                await self.redis.setex(full_key, ttl, serialized)
            else:
                await self.redis.set(full_key, serialized)
                
        except Exception as e:
            self.logger.error(f"设置缓存失败: {str(e)}")
            
    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        try:
            result = await self.redis.delete(self._make_key(key))
            return result > 0
        except Exception as e:
            self.logger.error(f"删除缓存失败: {str(e)}")
            return False
            
    async def exists(self, key: str) -> bool:
        """检查缓存键是否存在"""
        try:
            return await self.redis.exists(self._make_key(key)) > 0
        except Exception as e:
            self.logger.error(f"检查缓存是否存在失败: {str(e)}")
            return False
            
    async def clear(self) -> None:
        """清空缓存"""
        try:
            # 获取所有匹配的键
            pattern = f"{self.prefix}*"
            cursor = 0
            while True:
                cursor, keys = await self.redis.scan(
                    cursor=cursor,
                    match=pattern,
                    count=100
                )
                if keys:
                    await self.redis.delete(*keys)
                if cursor == 0:
                    break
        except Exception as e:
            self.logger.error(f"清空缓存失败: {str(e)}")
            
    async def get_metrics(self) -> Dict[str, Any]:
        """获取缓存指标"""
        try:
            # 获取键数量
            pattern = f"{self.prefix}*"
            cursor = 0
            size = 0
            while True:
                cursor, keys = await self.redis.scan(
                    cursor=cursor,
                    match=pattern,
                    count=100
                )
                size += len(keys)
                if cursor == 0:
                    break
                    
            self._metrics["size"] = size
            return self._metrics
            
        except Exception as e:
            self.logger.error(f"获取缓存指标失败: {str(e)}")
            return self._metrics
            
    async def ttl(self, key: str) -> Optional[int]:
        """获取缓存剩余过期时间"""
        try:
            ttl = await self.redis.ttl(self._make_key(key))
            return ttl if ttl > 0 else None
        except Exception as e:
            self.logger.error(f"获取过期时间失败: {str(e)}")
            return None
            
    async def multi_get(self, keys: List[str]) -> Dict[str, Any]:
        """批量获取缓存值"""
        try:
            # 转换为完整键
            full_keys = [self._make_key(key) for key in keys]
            
            # 批量获取
            values = await self.redis.mget(full_keys)
            
            # 处理结果
            results = {}
            for key, value in zip(keys, values):
                if value is not None:
                    results[key] = self.deserializer(value)
                    self._update_metrics(hit=True)
                else:
                    self._update_metrics(hit=False)
                    
            return results
            
        except Exception as e:
            self.logger.error(f"批量获取缓存失败: {str(e)}")
            return {}
            
    async def multi_set(
        self,
        mapping: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> None:
        """批量设置缓存值"""
        try:
            # 如果没有TTL，直接使用MSET
            if ttl is None and self.default_ttl is None:
                # 转换为完整键并序列化值
                redis_mapping = {
                    self._make_key(k): self.serializer(v)
                    for k, v in mapping.items()
                }
                await self.redis.mset(redis_mapping)
                return
                
            # 如果有TTL，使用pipeline
            ttl = ttl or self.default_ttl
            async with self.redis.pipeline(transaction=True) as pipe:
                for key, value in mapping.items():
                    full_key = self._make_key(key)
                    serialized = self.serializer(value)
                    if ttl is not None:
                        await pipe.setex(full_key, ttl, serialized)
                    else:
                        await pipe.set(full_key, serialized)
                await pipe.execute()
                
        except Exception as e:
            self.logger.error(f"批量设置缓存失败: {str(e)}")
            
    async def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """增加计数器值
        
        Args:
            key: 缓存键
            amount: 增加量
            
        Returns:
            Optional[int]: 新值
        """
        try:
            return await self.redis.incrby(self._make_key(key), amount)
        except Exception as e:
            self.logger.error(f"增加计数器失败: {str(e)}")
            return None
            
    async def decr(self, key: str, amount: int = 1) -> Optional[int]:
        """减少计数器值
        
        Args:
            key: 缓存键
            amount: 减少量
            
        Returns:
            Optional[int]: 新值
        """
        try:
            return await self.redis.decrby(self._make_key(key), amount)
        except Exception as e:
            self.logger.error(f"减少计数器失败: {str(e)}")
            return None
            
    @asynccontextmanager
    async def acquire_lock(
        self,
        key: str,
        ttl: int = 30,
        retry_times: int = 3,
        retry_delay: float = 0.1
    ) -> AsyncContextManager[bool]:
        """获取分布式锁
        
        Args:
            key: 锁键
            ttl: 锁过期时间（秒）
            retry_times: 重试次数
            retry_delay: 重试延迟（秒）
            
        Returns:
            AsyncContextManager[bool]: 是否获取到锁
        """
        lock_key = f"{self.prefix}lock:{key}"
        locked = False
        
        try:
            # 尝试获取锁
            for _ in range(retry_times):
                locked = await self.redis.set(
                    lock_key,
                    "1",
                    nx=True,
                    ex=ttl
                )
                if locked:
                    break
                await asyncio.sleep(retry_delay)
                
            yield locked or False
            
        finally:
            # 释放锁
            if locked:
                await self.redis.delete(lock_key)
                
    async def scan(
        self,
        cursor: int = 0,
        match: Optional[str] = None,
        count: Optional[int] = None
    ) -> tuple[int, List[str]]:
        """扫描缓存键
        
        Args:
            cursor: 游标
            match: 匹配模式
            count: 每次扫描的键数量
            
        Returns:
            tuple[int, List[str]]: 新游标和键列表
        """
        try:
            return await self.redis.scan(
                cursor=cursor,
                match=match,
                count=count
            )
        except Exception as e:
            self.logger.error(f"扫描缓存键失败: {str(e)}")
            return 0, [] 