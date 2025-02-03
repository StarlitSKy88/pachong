"""备份调度器模块

该模块负责自动调度数据库备份任务，包括：
1. 定时全量备份
2. 定时增量备份
3. 自动清理旧备份
4. 备份状态监控
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
import json

from src.utils.logger import get_logger
from src.monitor.metrics import MetricsCollector
from src.monitor.alert import AlertEngine
from src.database.backup import BackupManager

logger = get_logger(__name__)

class BackupScheduler:
    """备份调度器"""
    
    def __init__(
        self,
        backup_manager: BackupManager,
        full_backup_interval: int = 24 * 60 * 60,  # 24小时
        incremental_backup_interval: int = 60 * 60,  # 1小时
        cleanup_interval: int = 24 * 60 * 60,  # 24小时
        retention_days: int = 30,
        metrics_collector: Optional[MetricsCollector] = None,
        alert_engine: Optional[AlertEngine] = None
    ):
        self.backup_manager = backup_manager
        self.full_backup_interval = full_backup_interval
        self.incremental_backup_interval = incremental_backup_interval
        self.cleanup_interval = cleanup_interval
        self.retention_days = retention_days
        self.metrics_collector = metrics_collector
        self.alert_engine = alert_engine
        
        # 运行状态
        self.running = False
        self.tasks = []
        
        # 上次执行时间
        self.last_full_backup_check = datetime.now()
        self.last_incremental_backup_check = datetime.now()
        self.last_cleanup_check = datetime.now()
    
    async def start(self):
        """启动调度器"""
        if self.running:
            logger.warning("Backup scheduler is already running")
            return
        
        self.running = True
        logger.info("Starting backup scheduler")
        
        # 启动调度任务
        self.tasks = [
            asyncio.create_task(self._full_backup_loop()),
            asyncio.create_task(self._incremental_backup_loop()),
            asyncio.create_task(self._cleanup_loop())
        ]
    
    async def stop(self):
        """停止调度器"""
        if not self.running:
            return
        
        self.running = False
        logger.info("Stopping backup scheduler")
        
        # 等待任务完成
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
            self.tasks.clear()
    
    async def _full_backup_loop(self):
        """全量备份循环"""
        while self.running:
            try:
                now = datetime.now()
                if (now - self.last_full_backup_check).total_seconds() >= self.full_backup_interval:
                    logger.info("Starting scheduled full backup")
                    backup_id = await self.backup_manager.create_full_backup()
                    logger.info(f"Scheduled full backup completed: {backup_id}")
                    self.last_full_backup_check = now
                
                await asyncio.sleep(60)  # 每分钟检查一次
                
            except Exception as e:
                logger.error(f"Full backup loop error: {e}", exc_info=True)
                if self.alert_engine:
                    await self.alert_engine.send_alert(
                        title="Full Backup Loop Failed",
                        message=str(e),
                        level="error"
                    )
                await asyncio.sleep(300)  # 发生错误后等待5分钟
    
    async def _incremental_backup_loop(self):
        """增量备份循环"""
        while self.running:
            try:
                now = datetime.now()
                if (now - self.last_incremental_backup_check).total_seconds() >= self.incremental_backup_interval:
                    # 只在存在全量备份时执行增量备份
                    if self.backup_manager.last_full_backup:
                        logger.info("Starting scheduled incremental backup")
                        backup_id = await self.backup_manager.create_incremental_backup()
                        logger.info(f"Scheduled incremental backup completed: {backup_id}")
                    else:
                        logger.warning("Skipping incremental backup: no full backup exists")
                    self.last_incremental_backup_check = now
                
                await asyncio.sleep(60)  # 每分钟检查一次
                
            except Exception as e:
                logger.error(f"Incremental backup loop error: {e}", exc_info=True)
                if self.alert_engine:
                    await self.alert_engine.send_alert(
                        title="Incremental Backup Loop Failed",
                        message=str(e),
                        level="error"
                    )
                await asyncio.sleep(300)  # 发生错误后等待5分钟
    
    async def _cleanup_loop(self):
        """清理循环"""
        while self.running:
            try:
                now = datetime.now()
                if (now - self.last_cleanup_check).total_seconds() >= self.cleanup_interval:
                    logger.info("Starting scheduled backup cleanup")
                    await self.backup_manager.cleanup_old_backups(self.retention_days)
                    logger.info("Scheduled backup cleanup completed")
                    self.last_cleanup_check = now
                
                await asyncio.sleep(60)  # 每分钟检查一次
                
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}", exc_info=True)
                if self.alert_engine:
                    await self.alert_engine.send_alert(
                        title="Backup Cleanup Loop Failed",
                        message=str(e),
                        level="error"
                    )
                await asyncio.sleep(300)  # 发生错误后等待5分钟
    
    def get_scheduler_status(self) -> dict:
        """获取调度器状态"""
        return {
            'running': self.running,
            'last_full_backup_check': self.last_full_backup_check.isoformat(),
            'last_incremental_backup_check': self.last_incremental_backup_check.isoformat(),
            'last_cleanup_check': self.last_cleanup_check.isoformat(),
            'full_backup_interval': self.full_backup_interval,
            'incremental_backup_interval': self.incremental_backup_interval,
            'cleanup_interval': self.cleanup_interval,
            'retention_days': self.retention_days,
            'active_tasks': len(self.tasks)
        }
    
    async def force_full_backup(self) -> str:
        """强制执行全量备份"""
        logger.info("Starting forced full backup")
        backup_id = await self.backup_manager.create_full_backup()
        self.last_full_backup_check = datetime.now()
        logger.info(f"Forced full backup completed: {backup_id}")
        return backup_id
    
    async def force_incremental_backup(self) -> str:
        """强制执行增量备份"""
        if not self.backup_manager.last_full_backup:
            raise ValueError("No full backup exists")
        
        logger.info("Starting forced incremental backup")
        backup_id = await self.backup_manager.create_incremental_backup()
        self.last_incremental_backup_check = datetime.now()
        logger.info(f"Forced incremental backup completed: {backup_id}")
        return backup_id
    
    async def force_cleanup(self):
        """强制执行清理"""
        logger.info("Starting forced backup cleanup")
        await self.backup_manager.cleanup_old_backups(self.retention_days)
        self.last_cleanup_check = datetime.now()
        logger.info("Forced backup cleanup completed") 