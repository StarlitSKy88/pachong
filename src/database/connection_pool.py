"""数据库连接池管理模块"""

import asyncio
from typing import Dict, Any, Optional, Type, TypeVar
from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.pool import AsyncAdaptedQueuePool
from redis.asyncio import Redis, ConnectionPool as RedisPool
from motor.motor_asyncio import AsyncIOMotorClient
from ..utils.config_manager import ConfigManager
from ..utils.logger import get_logger

T = TypeVar("T")

class BaseConnectionPool(ABC):
    """连接池基类"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """初始化连接池
        
        Args:
            name: 连接池名称
            config: 连接池配置
        """
        self.name = name
        self.config = config
        self.logger = get_logger(f"{name}_pool")
        self._pool = None
        self._metrics = {
            "created_at": None,
            "total_connections": 0,
            "active_connections": 0,
            "idle_connections": 0,
            "max_connections": config.get("max_connections", 10)
        }
        
    @abstractmethod
    async def create_pool(self) -> None:
        """创建连接池"""
        pass
        
    @abstractmethod
    async def close(self) -> None:
        """关闭连接池"""
        pass
        
    @abstractmethod
    async def get_metrics(self) -> Dict[str, Any]:
        """获取连接池指标
        
        Returns:
            Dict[str, Any]: 连接池指标
        """
        pass
        
    @property
    def pool(self) -> Any:
        """获取连接池实例
        
        Returns:
            Any: 连接池实例
        """
        if self._pool is None:
            raise RuntimeError(f"{self.name} 连接池未初始化")
        return self._pool

class SQLAlchemyPool(BaseConnectionPool):
    """SQLAlchemy连接池"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """初始化SQLAlchemy连接池
        
        Args:
            name: 连接池名称
            config: 连接池配置
        """
        super().__init__(name, config)
        self.url = config["url"]
        
    async def create_pool(self) -> None:
        """创建连接池"""
        self._pool = create_async_engine(
            self.url,
            pool_size=self.config.get("pool_size", 5),
            max_overflow=self.config.get("max_overflow", 10),
            pool_timeout=self.config.get("pool_timeout", 30),
            pool_recycle=self.config.get("pool_recycle", 1800),
            pool_pre_ping=self.config.get("pool_pre_ping", True),
            poolclass=AsyncAdaptedQueuePool
        )
        self.logger.info(f"{self.name} 连接池已创建")
        
    async def close(self) -> None:
        """关闭连接池"""
        if self._pool is not None:
            await self._pool.dispose()
            self._pool = None
            self.logger.info(f"{self.name} 连接池已关闭")
            
    async def get_metrics(self) -> Dict[str, Any]:
        """获取连接池指标"""
        if self._pool is None:
            return self._metrics
            
        pool = self._pool.pool
        self._metrics.update({
            "total_connections": pool.size() + pool.overflow(),
            "active_connections": pool.checkedin() + pool.checkedout(),
            "idle_connections": pool.checkedin()
        })
        return self._metrics

class RedisConnectionPool(BaseConnectionPool):
    """Redis连接池"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """初始化Redis连接池
        
        Args:
            name: 连接池名称
            config: 连接池配置
        """
        super().__init__(name, config)
        self.host = config["host"]
        self.port = config["port"]
        self.db = config.get("db", 0)
        
    async def create_pool(self) -> None:
        """创建连接池"""
        self._pool = RedisPool(
            host=self.host,
            port=self.port,
            db=self.db,
            max_connections=self.config.get("max_connections", 10),
            timeout=self.config.get("timeout", 30)
        )
        self.logger.info(f"{self.name} 连接池已创建")
        
    async def close(self) -> None:
        """关闭连接池"""
        if self._pool is not None:
            await self._pool.disconnect()
            self._pool = None
            self.logger.info(f"{self.name} 连接池已关闭")
            
    async def get_metrics(self) -> Dict[str, Any]:
        """获取连接池指标"""
        if self._pool is None:
            return self._metrics
            
        self._metrics.update({
            "total_connections": len(self._pool._available_connections) + len(self._pool._in_use_connections),
            "active_connections": len(self._pool._in_use_connections),
            "idle_connections": len(self._pool._available_connections)
        })
        return self._metrics

class MongoConnectionPool(BaseConnectionPool):
    """MongoDB连接池"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """初始化MongoDB连接池
        
        Args:
            name: 连接池名称
            config: 连接池配置
        """
        super().__init__(name, config)
        self.uri = config["uri"]
        
    async def create_pool(self) -> None:
        """创建连接池"""
        self._pool = AsyncIOMotorClient(
            self.uri,
            maxPoolSize=self.config.get("max_pool_size", 100),
            minPoolSize=self.config.get("min_pool_size", 0),
            maxIdleTimeMS=self.config.get("max_idle_time_ms", 10000),
            waitQueueTimeoutMS=self.config.get("wait_queue_timeout_ms", 1000)
        )
        self.logger.info(f"{self.name} 连接池已创建")
        
    async def close(self) -> None:
        """关闭连接池"""
        if self._pool is not None:
            self._pool.close()
            self._pool = None
            self.logger.info(f"{self.name} 连接池已关闭")
            
    async def get_metrics(self) -> Dict[str, Any]:
        """获取连接池指标"""
        if self._pool is None:
            return self._metrics
            
        # MongoDB连接池指标需要通过命令获取
        self._metrics.update({
            "total_connections": 0,  # TODO: 实现MongoDB连接池指标收集
            "active_connections": 0,
            "idle_connections": 0
        })
        return self._metrics

class ConnectionPoolManager:
    """连接池管理器"""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """初始化连接池管理器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager or ConfigManager()
        self.logger = get_logger("pool_manager")
        self.pools: Dict[str, BaseConnectionPool] = {}
        
    def register_pool(self, name: str, pool: BaseConnectionPool) -> None:
        """注册连接池
        
        Args:
            name: 连接池名称
            pool: 连接池实例
        """
        self.pools[name] = pool
        self.logger.info(f"已注册连接池: {name}")
        
    async def create_pool(
        self,
        name: str,
        pool_type: Type[BaseConnectionPool],
        config: Dict[str, Any]
    ) -> BaseConnectionPool:
        """创建连接池
        
        Args:
            name: 连接池名称
            pool_type: 连接池类型
            config: 连接池配置
            
        Returns:
            BaseConnectionPool: 连接池实例
        """
        pool = pool_type(name, config)
        await pool.create_pool()
        self.register_pool(name, pool)
        return pool
        
    def get_pool(self, name: str) -> BaseConnectionPool:
        """获取连接池
        
        Args:
            name: 连接池名称
            
        Returns:
            BaseConnectionPool: 连接池实例
            
        Raises:
            KeyError: 当连接池不存在时
        """
        if name not in self.pools:
            raise KeyError(f"连接池不存在: {name}")
        return self.pools[name]
        
    async def close_all(self) -> None:
        """关闭所有连接池"""
        for pool in self.pools.values():
            await pool.close()
        self.pools.clear()
        self.logger.info("所有连接池已关闭")
        
    async def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """获取所有连接池指标
        
        Returns:
            Dict[str, Dict[str, Any]]: 连接池指标
        """
        metrics = {}
        for name, pool in self.pools.items():
            metrics[name] = await pool.get_metrics()
        return metrics 