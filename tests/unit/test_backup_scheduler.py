"""备份调度器测试模块"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from src.database.backup_scheduler import BackupScheduler
from src.database.backup import BackupManager

@pytest.fixture
def backup_manager():
    """创建Mock备份管理器"""
    manager = AsyncMock(spec=BackupManager)
    manager.last_full_backup = datetime.now()
    return manager

@pytest.fixture
def scheduler(backup_manager):
    """创建测试用调度器"""
    return BackupScheduler(
        backup_manager=backup_manager,
        full_backup_interval=300,  # 5分钟
        incremental_backup_interval=60,  # 1分钟
        cleanup_interval=300,  # 5分钟
        retention_days=30
    )

@pytest.mark.asyncio
async def test_start_stop(scheduler):
    """测试启动和停止"""
    # 启动调度器
    await scheduler.start()
    assert scheduler.running is True
    assert len(scheduler.tasks) == 3
    
    # 重复启动
    await scheduler.start()
    assert len(scheduler.tasks) == 3
    
    # 停止调度器
    await scheduler.stop()
    assert scheduler.running is False
    assert len(scheduler.tasks) == 0

@pytest.mark.asyncio
async def test_full_backup_schedule(scheduler, backup_manager):
    """测试全量备份调度"""
    # 修改上次检查时间为6分钟前
    scheduler.last_full_backup_check = datetime.now() - timedelta(minutes=6)
    
    # 启动调度器
    await scheduler.start()
    
    # 等待执行
    await asyncio.sleep(0.1)
    
    # 验证是否执行了备份
    backup_manager.create_full_backup.assert_called_once()
    
    await scheduler.stop()

@pytest.mark.asyncio
async def test_incremental_backup_schedule(scheduler, backup_manager):
    """测试增量备份调度"""
    # 修改上次检查时间为2分钟前
    scheduler.last_incremental_backup_check = datetime.now() - timedelta(minutes=2)
    
    # 启动调度器
    await scheduler.start()
    
    # 等待执行
    await asyncio.sleep(0.1)
    
    # 验证是否执行了备份
    backup_manager.create_incremental_backup.assert_called_once()
    
    await scheduler.stop()

@pytest.mark.asyncio
async def test_cleanup_schedule(scheduler, backup_manager):
    """测试清理调度"""
    # 修改上次检查时间为6分钟前
    scheduler.last_cleanup_check = datetime.now() - timedelta(minutes=6)
    
    # 启动调度器
    await scheduler.start()
    
    # 等待执行
    await asyncio.sleep(0.1)
    
    # 验证是否执行了清理
    backup_manager.cleanup_old_backups.assert_called_once_with(30)
    
    await scheduler.stop()

@pytest.mark.asyncio
async def test_force_full_backup(scheduler, backup_manager):
    """测试强制执行全量备份"""
    backup_manager.create_full_backup.return_value = "test_backup_id"
    
    # 执行强制备份
    backup_id = await scheduler.force_full_backup()
    
    # 验证结果
    assert backup_id == "test_backup_id"
    backup_manager.create_full_backup.assert_called_once()
    assert scheduler.last_full_backup_check > datetime.now() - timedelta(seconds=1)

@pytest.mark.asyncio
async def test_force_incremental_backup(scheduler, backup_manager):
    """测试强制执行增量备份"""
    backup_manager.create_incremental_backup.return_value = "test_backup_id"
    
    # 执行强制备份
    backup_id = await scheduler.force_incremental_backup()
    
    # 验证结果
    assert backup_id == "test_backup_id"
    backup_manager.create_incremental_backup.assert_called_once()
    assert scheduler.last_incremental_backup_check > datetime.now() - timedelta(seconds=1)

@pytest.mark.asyncio
async def test_force_cleanup(scheduler, backup_manager):
    """测试强制执行清理"""
    # 执行强制清理
    await scheduler.force_cleanup()
    
    # 验证结果
    backup_manager.cleanup_old_backups.assert_called_once_with(30)
    assert scheduler.last_cleanup_check > datetime.now() - timedelta(seconds=1)

@pytest.mark.asyncio
async def test_backup_error_handling(scheduler, backup_manager):
    """测试备份错误处理"""
    # 创建Mock告警引擎
    alert_engine = AsyncMock()
    scheduler.alert_engine = alert_engine
    
    # 模拟备份失败
    backup_manager.create_full_backup.side_effect = Exception("Test error")
    
    # 修改上次检查时间为6分钟前
    scheduler.last_full_backup_check = datetime.now() - timedelta(minutes=6)
    
    # 启动调度器
    await scheduler.start()
    
    # 等待执行
    await asyncio.sleep(0.1)
    
    # 验证是否发送告警
    alert_engine.send_alert.assert_called_once()
    
    await scheduler.stop()

def test_get_scheduler_status(scheduler):
    """测试获取调度器状态"""
    status = scheduler.get_scheduler_status()
    
    assert 'running' in status
    assert 'last_full_backup_check' in status
    assert 'last_incremental_backup_check' in status
    assert 'last_cleanup_check' in status
    assert 'full_backup_interval' in status
    assert 'incremental_backup_interval' in status
    assert 'cleanup_interval' in status
    assert 'retention_days' in status
    assert 'active_tasks' in status
    
    assert status['full_backup_interval'] == 300
    assert status['incremental_backup_interval'] == 60
    assert status['cleanup_interval'] == 300
    assert status['retention_days'] == 30

@pytest.mark.asyncio
async def test_no_full_backup_exists(scheduler, backup_manager):
    """测试没有全量备份时的增量备份处理"""
    # 设置没有全量备份
    backup_manager.last_full_backup = None
    
    # 修改上次检查时间为2分钟前
    scheduler.last_incremental_backup_check = datetime.now() - timedelta(minutes=2)
    
    # 启动调度器
    await scheduler.start()
    
    # 等待执行
    await asyncio.sleep(0.1)
    
    # 验证没有执行增量备份
    backup_manager.create_incremental_backup.assert_not_called()
    
    await scheduler.stop()

@pytest.mark.asyncio
async def test_metrics_collection(scheduler, backup_manager):
    """测试指标收集"""
    # 创建Mock指标收集器
    metrics_collector = Mock()
    scheduler.metrics_collector = metrics_collector
    
    # 修改上次检查时间
    scheduler.last_full_backup_check = datetime.now() - timedelta(minutes=6)
    
    # 启动调度器
    await scheduler.start()
    
    # 等待执行
    await asyncio.sleep(0.1)
    
    # 验证是否收集了指标
    assert backup_manager.metrics_collector == metrics_collector
    
    await scheduler.stop() 