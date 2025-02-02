"""数据库会话模块"""
from contextlib import asynccontextmanager
from typing import Optional, AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.config import get_database_config

# 全局会话工厂
async_session_factory: Optional[async_sessionmaker] = None
engine = None

def init_database(base):
    """初始化数据库

    Args:
        base: 数据库模型基类
    """
    global async_session_factory, engine
    
    # 获取数据库配置
    config = get_database_config()
    
    # 创建异步引擎
    engine = create_async_engine(
        config["url"].replace('sqlite:///', 'sqlite+aiosqlite:///'),
        **config.get("engine_kwargs", {})
    )
    
    # 创建异步会话工厂
    async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    # 创建表
    async def create_tables():
        async with engine.begin() as conn:
            await conn.run_sync(base.metadata.create_all)
    
    import asyncio
    asyncio.run(create_tables())

@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话的异步上下文管理器

    Yields:
        AsyncSession: 异步数据库会话
    """
    if async_session_factory is None:
        raise RuntimeError("数据库未初始化")
        
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def get_session() -> AsyncSession:
    """获取异步数据库会话

    Returns:
        AsyncSession: 异步数据库会话
    """
    if async_session_factory is None:
        raise RuntimeError("数据库未初始化")
    return async_session_factory() 