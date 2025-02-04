"""连接池测试模块。"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection_pool import ConnectionPool
from src.config import Config

@pytest.fixture
def config():
    """配置对象夹具。"""
    return Config(
        database=Config.DatabaseConfig(
            type="sqlite",
            name="test"
        ),
        redis_url="redis://localhost:6379/0"
    )

@pytest.fixture
async def pool(config):
    """连接池夹具。"""
    pool = ConnectionPool(config)
    await pool.init()
    try:
        yield pool
    finally:
        await pool.close()

@pytest.mark.asyncio
async def test_init_pool(pool):
    """测试初始化连接池。"""
    assert 'sqlite' in pool.engines
    assert pool.engines['sqlite'] is not None
    assert 'sqlite' in pool._session_factories
    assert pool._session_factories['sqlite'] is not None
    assert pool.redis_pool is not None

@pytest.mark.asyncio
async def test_get_session(pool):
    """测试获取会话。"""
    async with pool.get_session() as session:
        assert isinstance(session, AsyncSession)

@pytest.mark.asyncio
async def test_get_session_invalid_type(pool):
    """测试获取无效类型的会话。"""
    with pytest.raises(ValueError):
        async with pool.get_session('invalid'):
            pass

@pytest.mark.asyncio
async def test_get_redis(pool):
    """测试获取Redis连接。"""
    async with pool.get_redis() as redis:
        assert redis is not None

@pytest.mark.asyncio
async def test_close_pool(pool):
    """测试关闭连接池。"""
    await pool.close()
    assert len(pool.engines) == 1
    assert pool.redis_pool is not None 