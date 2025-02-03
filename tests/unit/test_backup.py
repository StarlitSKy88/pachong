"""备份管理器测试模块"""

import pytest
import os
import json
import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from src.database.backup import BackupManager
from src.database.models import Base
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker

# 测试数据库配置
TEST_DB_URL = 'sqlite:///test.db'
TEST_BACKUP_DIR = 'test_backups'

# 测试表定义
class TestTable(Base):
    __tablename__ = 'test_table'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    updated_at = Column(DateTime, default=datetime.now)

@pytest.fixture
def backup_manager():
    """创建测试用备份管理器"""
    # 创建测试数据库
    engine = create_engine(TEST_DB_URL)
    Base.metadata.create_all(engine)
    
    # 创建备份管理器
    manager = BackupManager(
        db_url=TEST_DB_URL,
        backup_dir=TEST_BACKUP_DIR
    )
    
    yield manager
    
    # 清理测试数据
    Base.metadata.drop_all(engine)
    if os.path.exists('test.db'):
        os.remove('test.db')
    if os.path.exists(TEST_BACKUP_DIR):
        shutil.rmtree(TEST_BACKUP_DIR)

@pytest.fixture
def test_data(backup_manager):
    """创建测试数据"""
    Session = sessionmaker(bind=backup_manager.engine)
    session = Session()
    
    try:
        # 插入测试数据
        for i in range(5):
            item = TestTable(name=f'test_{i}')
            session.add(item)
        session.commit()
    finally:
        session.close()

@pytest.mark.asyncio
async def test_create_full_backup(backup_manager, test_data):
    """测试创建全量备份"""
    # 创建备份
    backup_id = await backup_manager.create_full_backup()
    
    # 验证备份文件存在
    backup_file = backup_manager.full_backup_dir / f'backup_{backup_id}.gz'
    assert backup_file.exists()
    
    # 验证校验和文件存在
    checksum_file = backup_file.with_suffix('.md5')
    assert checksum_file.exists()
    
    # 验证备份状态已更新
    assert backup_manager.last_full_backup is not None
    
    # 验证备份内容
    with gzip.open(backup_file, 'rb') as f:
        data = json.loads(f.read().decode())
    assert 'test_table' in data
    assert len(data['test_table']) == 5

@pytest.mark.asyncio
async def test_create_incremental_backup(backup_manager, test_data):
    """测试创建增量备份"""
    # 先创建全量备份
    await backup_manager.create_full_backup()
    
    # 添加新数据
    Session = sessionmaker(bind=backup_manager.engine)
    session = Session()
    try:
        item = TestTable(name='incremental_test')
        session.add(item)
        session.commit()
    finally:
        session.close()
    
    # 创建增量备份
    backup_id = await backup_manager.create_incremental_backup()
    
    # 验证备份文件存在
    backup_file = backup_manager.incremental_backup_dir / f'backup_{backup_id}.gz'
    assert backup_file.exists()
    
    # 验证备份内容
    with gzip.open(backup_file, 'rb') as f:
        data = json.loads(f.read().decode())
    assert 'test_table' in data
    assert len(data['test_table']) == 1
    assert data['test_table'][0]['name'] == 'incremental_test'

@pytest.mark.asyncio
async def test_verify_backup(backup_manager, test_data):
    """测试备份验证"""
    # 创建备份
    backup_id = await backup_manager.create_full_backup()
    
    # 验证正确的备份
    assert await backup_manager.verify_backup(backup_id, 'full') is True
    
    # 验证不存在的备份
    assert await backup_manager.verify_backup('nonexistent', 'full') is False
    
    # 修改备份文件内容
    backup_file = backup_manager.full_backup_dir / f'backup_{backup_id}.gz'
    with open(backup_file, 'wb') as f:
        f.write(b'corrupted data')
    
    # 验证损坏的备份
    assert await backup_manager.verify_backup(backup_id, 'full') is False

@pytest.mark.asyncio
async def test_restore_backup(backup_manager, test_data):
    """测试备份恢复"""
    # 创建备份
    backup_id = await backup_manager.create_full_backup()
    
    # 清空数据库
    Session = sessionmaker(bind=backup_manager.engine)
    session = Session()
    try:
        session.query(TestTable).delete()
        session.commit()
    finally:
        session.close()
    
    # 恢复备份
    success = await backup_manager.restore_backup(backup_id, 'full')
    assert success is True
    
    # 验证数据已恢复
    session = Session()
    try:
        count = session.query(TestTable).count()
        assert count == 5
    finally:
        session.close()

@pytest.mark.asyncio
async def test_cleanup_old_backups(backup_manager, test_data):
    """测试清理旧备份"""
    # 创建多个备份
    backup_ids = []
    for _ in range(3):
        backup_id = await backup_manager.create_full_backup()
        backup_ids.append(backup_id)
        await asyncio.sleep(0.1)  # 确保备份时间不同
    
    # 修改第一个备份的时间为31天前
    old_backup_file = backup_manager.full_backup_dir / f'backup_{backup_ids[0]}.gz'
    old_time = datetime.now() - timedelta(days=31)
    os.utime(old_backup_file, (old_time.timestamp(), old_time.timestamp()))
    
    # 清理旧备份
    await backup_manager.cleanup_old_backups(days=30)
    
    # 验证旧备份已删除
    assert not old_backup_file.exists()
    assert not old_backup_file.with_suffix('.md5').exists()
    
    # 验证新备份仍存在
    for backup_id in backup_ids[1:]:
        backup_file = backup_manager.full_backup_dir / f'backup_{backup_id}.gz'
        assert backup_file.exists()

@pytest.mark.asyncio
async def test_metrics_collection(backup_manager, test_data):
    """测试指标收集"""
    # 创建Mock指标收集器
    metrics_collector = Mock()
    metrics_collector.observe = Mock()
    metrics_collector.increment_counter = Mock()
    backup_manager.metrics_collector = metrics_collector
    
    # 创建备份
    await backup_manager.create_full_backup()
    
    # 验证指标收集
    assert metrics_collector.observe.call_count >= 1
    assert metrics_collector.increment_counter.call_count >= 1

@pytest.mark.asyncio
async def test_alert_engine(backup_manager):
    """测试告警引擎"""
    # 创建Mock告警引擎
    alert_engine = AsyncMock()
    backup_manager.alert_engine = alert_engine
    
    # 触发错误（尝试创建增量备份但没有全量备份）
    with pytest.raises(ValueError):
        await backup_manager.create_incremental_backup()
    
    # 验证告警
    alert_engine.send_alert.assert_called_once()

def test_get_backup_info(backup_manager, test_data):
    """测试获取备份信息"""
    info = backup_manager.get_backup_info()
    
    assert 'last_full_backup' in info
    assert 'last_incremental_backup' in info
    assert 'backup_dir' in info
    assert 'full_backups' in info
    assert 'incremental_backups' in info
    
    assert info['backup_dir'] == str(backup_manager.backup_dir)
    assert info['full_backups'] == 0
    assert info['incremental_backups'] == 0 