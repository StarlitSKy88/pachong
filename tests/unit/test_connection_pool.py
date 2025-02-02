"""连接池管理器测试模块"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.database.connection_pool import (
    BaseConnectionPool,
    SQLAlchemyPool,
    RedisConnectionPool,
    MongoConnectionPool,
    ConnectionPoolManager
)
from src.utils.config_manager import ConfigManager

class TestPool(BaseConnectionPool):
    """测试用连接池类"""
    
    async def create_pool(self) -> None:
        self._pool = Mock()
        
    async def close(self) -> None:
        self._pool = None
        
    async def get_metrics(self) -> dict:
        return self._metrics

@pytest.fixture
def config_manager():
    """配置管理器实例"""
    return ConfigManager()

@pytest.fixture
def pool_manager(config_manager):
    """连接池管理器实例"""
    return ConnectionPoolManager(config_manager)

@pytest.mark.asyncio
async def test_sqlalchemy_pool():
    """测试SQLAlchemy连接池"""
    config = {
        "url": "postgresql+asyncpg://user:pass@localhost/db",
        "pool_size": 5,
        "max_overflow": 10
    }
    pool = SQLAlchemyPool("test_sql", config)
    
    # 测试创建连接池
    with patch("src.database.connection_pool.create_async_engine") as mock_engine:
        await pool.create_pool()
        mock_engine.assert_called_once()
        
    # 测试获取指标
    metrics = await pool.get_metrics()
    assert "total_connections" in metrics
    assert "active_connections" in metrics
    assert "idle_connections" in metrics
    
    # 测试关闭连接池
    await pool.close()
    assert pool._pool is None

@pytest.mark.asyncio
async def test_redis_pool():
    """测试Redis连接池"""
    config = {
        "host": "localhost",
        "port": 6379,
        "db": 0,
        "max_connections": 10
    }
    pool = RedisConnectionPool("test_redis", config)
    
    # 测试创建连接池
    with patch("src.database.connection_pool.RedisPool") as mock_pool:
        await pool.create_pool()
        mock_pool.assert_called_once()
        
    # 测试获取指标
    metrics = await pool.get_metrics()
    assert "total_connections" in metrics
    assert "active_connections" in metrics
    assert "idle_connections" in metrics
    
    # 测试关闭连接池
    await pool.close()
    assert pool._pool is None

@pytest.mark.asyncio
async def test_mongo_pool():
    """测试MongoDB连接池"""
    config = {
        "uri": "mongodb://localhost:27017",
        "max_pool_size": 100
    }
    pool = MongoConnectionPool("test_mongo", config)
    
    # 测试创建连接池
    with patch("src.database.connection_pool.AsyncIOMotorClient") as mock_client:
        await pool.create_pool()
        mock_client.assert_called_once()
        
    # 测试获取指标
    metrics = await pool.get_metrics()
    assert "total_connections" in metrics
    assert "active_connections" in metrics
    assert "idle_connections" in metrics
    
    # 测试关闭连接池
    await pool.close()
    assert pool._pool is None

@pytest.mark.asyncio
async def test_pool_manager_create_pool(pool_manager):
    """测试连接池管理器创建连接池"""
    # 创建测试连接池
    config = {"test": "config"}
    pool = await pool_manager.create_pool("test", TestPool, config)
    
    assert isinstance(pool, TestPool)
    assert "test" in pool_manager.pools
    assert pool_manager.pools["test"] is pool

@pytest.mark.asyncio
async def test_pool_manager_get_pool(pool_manager):
    """测试连接池管理器获取连接池"""
    # 注册测试连接池
    pool = TestPool("test", {})
    pool_manager.register_pool("test", pool)
    
    # 获取连接池
    assert pool_manager.get_pool("test") is pool
    
    # 测试获取不存在的连接池
    with pytest.raises(KeyError):
        pool_manager.get_pool("not_exists")

@pytest.mark.asyncio
async def test_pool_manager_close_all(pool_manager):
    """测试连接池管理器关闭所有连接池"""
    # 创建多个测试连接池
    pools = []
    for i in range(3):
        pool = TestPool(f"test_{i}", {})
        await pool.create_pool()
        pool_manager.register_pool(f"test_{i}", pool)
        pools.append(pool)
        
    # 关闭所有连接池
    await pool_manager.close_all()
    
    assert len(pool_manager.pools) == 0
    for pool in pools:
        assert pool._pool is None

@pytest.mark.asyncio
async def test_pool_manager_get_all_metrics(pool_manager):
    """测试连接池管理器获取所有指标"""
    # 创建多个测试连接池
    for i in range(3):
        pool = TestPool(f"test_{i}", {})
        await pool.create_pool()
        pool_manager.register_pool(f"test_{i}", pool)
        
    # 获取所有指标
    metrics = await pool_manager.get_all_metrics()
    
    assert len(metrics) == 3
    for i in range(3):
        assert f"test_{i}" in metrics
        assert "total_connections" in metrics[f"test_{i}"]
        assert "active_connections" in metrics[f"test_{i}"]
        assert "idle_connections" in metrics[f"test_{i}"]

@pytest.mark.asyncio
async def test_pool_not_initialized():
    """测试未初始化的连接池"""
    pool = TestPool("test", {})
    
    with pytest.raises(RuntimeError):
        _ = pool.pool

@pytest.mark.asyncio
async def test_pool_metrics_update():
    """测试连接池指标更新"""
    pool = TestPool("test", {"max_connections": 20})
    
    # 检查初始指标
    metrics = await pool.get_metrics()
    assert metrics["max_connections"] == 20
    assert metrics["total_connections"] == 0
    assert metrics["active_connections"] == 0
    assert metrics["idle_connections"] == 0
    
    # 创建连接池后再次检查
    await pool.create_pool()
    metrics = await pool.get_metrics()
    assert metrics["max_connections"] == 20 