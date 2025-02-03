"""缓存存储实现"""
import json
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
import aioredis
from loguru import logger
import functools

from .base_storage import BaseStorage

class CacheStorage:
    """缓存存储实现"""
    
    def __init__(self, redis_url: str, ttl: int = 3600):
        """初始化
        
        Args:
            redis_url: Redis连接URL
            ttl: 缓存过期时间(秒)
        """
        self.redis_url = redis_url
        self.ttl = ttl
        self.redis = None
        self.logger = logger.bind(name=self.__class__.__name__)
        
    async def init(self):
        """初始化Redis连接"""
        if not self.redis:
            self.redis = await aioredis.from_url(self.redis_url)
            
    async def close(self):
        """关闭Redis连接"""
        if self.redis:
            await self.redis.close()
            self.redis = None
            
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """生成缓存键
        
        Args:
            prefix: 键前缀
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            缓存键
        """
        # 序列化参数
        key_parts = [prefix]
        
        if args:
            key_parts.extend([str(arg) for arg in args])
            
        if kwargs:
            # 排序确保键的一致性
            sorted_items = sorted(kwargs.items())
            key_parts.extend([f"{k}:{v}" for k, v in sorted_items])
            
        return ':'.join(key_parts)
        
    async def get(self, key: str) -> Optional[Dict]:
        """获取缓存
        
        Args:
            key: 缓存键
            
        Returns:
            缓存数据
        """
        try:
            await self.init()
            data = await self.redis.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            self.logger.error(f"获取缓存失败: {str(e)}")
        return None
        
    async def set(self, key: str, value: Dict, ttl: int = None) -> bool:
        """设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间(秒)
            
        Returns:
            是否成功
        """
        try:
            await self.init()
            await self.redis.set(
                key,
                json.dumps(value),
                ex=ttl or self.ttl
            )
            return True
        except Exception as e:
            self.logger.error(f"设置缓存失败: {str(e)}")
            return False
            
    async def delete(self, key: str) -> bool:
        """删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            是否成功
        """
        try:
            await self.init()
            await self.redis.delete(key)
            return True
        except Exception as e:
            self.logger.error(f"删除缓存失败: {str(e)}")
            return False
            
    async def clear(self, pattern: str = "*") -> bool:
        """清空缓存
        
        Args:
            pattern: 键模式
            
        Returns:
            是否成功
        """
        try:
            await self.init()
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
            return True
        except Exception as e:
            self.logger.error(f"清空缓存失败: {str(e)}")
            return False
            
class CachedStorage(BaseStorage):
    """带缓存的存储实现"""
    
    def __init__(self, storage: BaseStorage, cache: CacheStorage):
        """初始化
        
        Args:
            storage: 底层存储
            cache: 缓存存储
        """
        super().__init__()
        self.storage = storage
        self.cache = cache
        
    async def save(self, data: Dict[str, Any]) -> bool:
        """保存数据"""
        # 先保存到存储
        if await self.storage.save(data):
            # 更新缓存
            key = f"data:{data['id']}"
            await self.cache.set(key, data)
            return True
        return False
        
    async def get(self, id: str) -> Optional[Dict[str, Any]]:
        """获取数据"""
        # 先查缓存
        key = f"data:{id}"
        data = await self.cache.get(key)
        if data:
            return data
            
        # 缓存未命中,查存储
        data = await self.storage.get(id)
        if data:
            # 更新缓存
            await self.cache.set(key, data)
        return data
        
    async def update(self, id: str, data: Dict[str, Any]) -> bool:
        """更新数据"""
        # 先更新存储
        if await self.storage.update(id, data):
            # 删除缓存
            key = f"data:{id}"
            await self.cache.delete(key)
            return True
        return False
        
    async def delete(self, id: str) -> bool:
        """删除数据"""
        # 先删除存储
        if await self.storage.delete(id):
            # 删除缓存
            key = f"data:{id}"
            await self.cache.delete(key)
            return True
        return False
        
    async def list(self, filter: Dict[str, Any] = None,
                  sort: List[tuple] = None,
                  limit: int = 100,
                  offset: int = 0) -> List[Dict[str, Any]]:
        """列出数据"""
        # 生成缓存键
        key = self.cache._generate_key(
            'list',
            filter=filter,
            sort=sort,
            limit=limit,
            offset=offset
        )
        
        # 先查缓存
        data = await self.cache.get(key)
        if data:
            return data
            
        # 缓存未命中,查存储
        data = await self.storage.list(filter, sort, limit, offset)
        if data:
            # 更新缓存
            await self.cache.set(key, data)
        return data
        
def cached(prefix: str, ttl: int = None):
    """缓存装饰器
    
    Args:
        prefix: 缓存键前缀
        ttl: 过期时间(秒)
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            # 生成缓存键
            key = self.cache._generate_key(prefix, *args, **kwargs)
            
            # 先查缓存
            data = await self.cache.get(key)
            if data:
                return data
                
            # 缓存未命中,执行原函数
            data = await func(self, *args, **kwargs)
            if data:
                # 更新缓存
                await self.cache.set(key, data, ttl)
            return data
        return wrapper
    return decorator 