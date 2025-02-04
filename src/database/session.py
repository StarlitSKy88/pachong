"""数据库会话模块。"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.config import Config
from src.models import Base

config = Config.from_env()

# 创建异步引擎
engine = create_async_engine(
    f"sqlite+aiosqlite:///{config.database.name}.db",
    echo=config.debug,
)

# 创建异步会话工厂
async_session_factory = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def init_db(is_test: bool = False):
    """初始化数据库。

    Args:
        is_test: 是否为测试环境
    """
    if is_test:
        # 测试环境使用内存数据库
        test_engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            echo=config.debug,
        )
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    else:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """获取异步会话。

    Yields:
        AsyncSession: 异步会话
    """
    async with async_session_factory() as session:
        yield session 