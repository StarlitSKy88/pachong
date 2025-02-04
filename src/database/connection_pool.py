"""数据库连接池模块。"""

from typing import Dict, Any, Optional
import asyncio
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from loguru import logger

from src.config import Config

class ConnectionPool:
    """数据库连接池"""

    def __init__(self, config: Config):
        """初始化连接池。

        Args:
            config: 配置对象
        """
        self.config = config
        self.engines: Dict[str, AsyncEngine] = {}
        self.redis_pool: Optional[Redis] = None
        self._session_factories: Dict[str, sessionmaker] = {}
        self._lock = asyncio.Lock()

    async def init(self):
        """初始化连接池。"""
        # 初始化 SQLite 连接
        sqlite_url = f"sqlite+aiosqlite:///{self.config.database.name}.db"
        self.engines['sqlite'] = create_async_engine(
            sqlite_url,
            echo=self.config.debug,
            pool_size=5,
            max_overflow=10
        )
        self._session_factories['sqlite'] = sessionmaker(
            self.engines['sqlite'],
            class_=AsyncSession,
            expire_on_commit=False
        )

        # 初始化 Redis 连接池
        if self.config.redis_url:
            self.redis_pool = Redis.from_url(
                self.config.redis_url,
                decode_responses=True
            )

    async def close(self):
        """关闭连接池。"""
        # 关闭 SQLite 连接
        for engine in self.engines.values():
            await engine.dispose()

        # 关闭 Redis 连接池
        if self.redis_pool:
            await self.redis_pool.close()

    @asynccontextmanager
    async def get_session(self, db_type: str = 'sqlite') -> AsyncSession:
        """获取数据库会话。

        Args:
            db_type: 数据库类型

        Yields:
            AsyncSession: 异步会话
        """
        if db_type not in self._session_factories:
            raise ValueError(f"不支持的数据库类型: {db_type}")

        async with self._session_factories[db_type]() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.close()

    @asynccontextmanager
    async def get_redis(self) -> Redis:
        """获取 Redis 连接。

        Yields:
            Redis: Redis 连接
        """
        if not self.redis_pool:
            raise ValueError("Redis 连接池未初始化")

        try:
            yield self.redis_pool
        except Exception as e:
            logger.error(f"Redis 操作失败: {e}")
            raise e 