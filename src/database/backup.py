"""数据备份模块

该模块负责数据库备份管理，包括：
1. 全量备份
2. 增量备份
3. 备份验证
4. 备份恢复
5. 备份清理
"""

import os
import gzip
import json
import shutil
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set
import asyncio
import aiofiles
import hashlib

from src.utils.logger import get_logger
from src.monitor.metrics import MetricsCollector
from src.monitor.alert import AlertEngine
from src.database.models import Base
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import select

logger = get_logger(__name__)

class BackupManager:
    """备份管理器"""
    
    def __init__(
        self,
        db_url: str,
        backup_dir: str,
        metrics_collector: Optional[MetricsCollector] = None,
        alert_engine: Optional[AlertEngine] = None
    ):
        self.db_url = db_url
        self.backup_dir = Path(backup_dir)
        self.metrics_collector = metrics_collector
        self.alert_engine = alert_engine
        
        # 创建备份目录
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.full_backup_dir = self.backup_dir / 'full'
        self.full_backup_dir.mkdir(exist_ok=True)
        self.incremental_backup_dir = self.backup_dir / 'incremental'
        self.incremental_backup_dir.mkdir(exist_ok=True)
        
        # 数据库连接
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        
        # 备份状态
        self.last_full_backup: Optional[datetime] = None
        self.last_incremental_backup: Optional[datetime] = None
        self._load_backup_status()
    
    def _load_backup_status(self):
        """加载备份状态"""
        status_file = self.backup_dir / 'backup_status.json'
        if status_file.exists():
            with open(status_file, 'r') as f:
                status = json.load(f)
                self.last_full_backup = datetime.fromisoformat(status.get('last_full_backup'))
                self.last_incremental_backup = datetime.fromisoformat(status.get('last_incremental_backup'))
    
    def _save_backup_status(self):
        """保存备份状态"""
        status_file = self.backup_dir / 'backup_status.json'
        status = {
            'last_full_backup': self.last_full_backup.isoformat() if self.last_full_backup else None,
            'last_incremental_backup': self.last_incremental_backup.isoformat() if self.last_incremental_backup else None
        }
        with open(status_file, 'w') as f:
            json.dump(status, f)
    
    async def create_full_backup(self) -> str:
        """创建全量备份"""
        start_time = datetime.now()
        backup_id = start_time.strftime('%Y%m%d_%H%M%S')
        backup_file = self.full_backup_dir / f'backup_{backup_id}.gz'
        
        try:
            # 获取所有表
            metadata = MetaData()
            metadata.reflect(bind=self.engine)
            
            # 导出数据
            data = {}
            session = self.Session()
            try:
                for table in metadata.sorted_tables:
                    rows = session.execute(select(table)).fetchall()
                    data[table.name] = [dict(row) for row in rows]
            finally:
                session.close()
            
            # 压缩并保存
            async with aiofiles.open(backup_file, 'wb') as f:
                compressed = gzip.compress(json.dumps(data).encode())
                await f.write(compressed)
            
            # 计算校验和
            checksum = hashlib.md5(compressed).hexdigest()
            checksum_file = backup_file.with_suffix('.md5')
            async with aiofiles.open(checksum_file, 'w') as f:
                await f.write(checksum)
            
            # 更新状态
            self.last_full_backup = start_time
            self._save_backup_status()
            
            # 记录指标
            if self.metrics_collector:
                duration = (datetime.now() - start_time).total_seconds()
                self.metrics_collector.observe(
                    'backup_duration_seconds',
                    duration,
                    labels={'type': 'full'}
                )
                self.metrics_collector.increment_counter(
                    'backup_completed',
                    labels={'type': 'full'}
                )
            
            logger.info(f"Full backup completed: {backup_file}")
            return backup_id
            
        except Exception as e:
            logger.error(f"Full backup failed: {e}", exc_info=True)
            if self.alert_engine:
                await self.alert_engine.send_alert(
                    title="Full Backup Failed",
                    message=str(e),
                    level="error"
                )
            raise
    
    async def create_incremental_backup(self) -> str:
        """创建增量备份"""
        if not self.last_full_backup:
            raise ValueError("No full backup exists")
        
        start_time = datetime.now()
        backup_id = start_time.strftime('%Y%m%d_%H%M%S')
        backup_file = self.incremental_backup_dir / f'backup_{backup_id}.gz'
        
        try:
            # 获取所有表
            metadata = MetaData()
            metadata.reflect(bind=self.engine)
            
            # 导出增量数据
            data = {}
            session = self.Session()
            try:
                for table in metadata.sorted_tables:
                    # 获取上次备份后修改的数据
                    last_backup = self.last_incremental_backup or self.last_full_backup
                    if 'updated_at' in table.columns:
                        stmt = select(table).where(table.c.updated_at > last_backup)
                    else:
                        # 如果表没有updated_at字段，获取所有数据
                        stmt = select(table)
                    rows = session.execute(stmt).fetchall()
                    if rows:
                        data[table.name] = [dict(row) for row in rows]
            finally:
                session.close()
            
            # 压缩并保存
            async with aiofiles.open(backup_file, 'wb') as f:
                compressed = gzip.compress(json.dumps(data).encode())
                await f.write(compressed)
            
            # 计算校验和
            checksum = hashlib.md5(compressed).hexdigest()
            checksum_file = backup_file.with_suffix('.md5')
            async with aiofiles.open(checksum_file, 'w') as f:
                await f.write(checksum)
            
            # 更新状态
            self.last_incremental_backup = start_time
            self._save_backup_status()
            
            # 记录指标
            if self.metrics_collector:
                duration = (datetime.now() - start_time).total_seconds()
                self.metrics_collector.observe(
                    'backup_duration_seconds',
                    duration,
                    labels={'type': 'incremental'}
                )
                self.metrics_collector.increment_counter(
                    'backup_completed',
                    labels={'type': 'incremental'}
                )
            
            logger.info(f"Incremental backup completed: {backup_file}")
            return backup_id
            
        except Exception as e:
            logger.error(f"Incremental backup failed: {e}", exc_info=True)
            if self.alert_engine:
                await self.alert_engine.send_alert(
                    title="Incremental Backup Failed",
                    message=str(e),
                    level="error"
                )
            raise
    
    async def verify_backup(self, backup_id: str, backup_type: str = 'full') -> bool:
        """验证备份完整性"""
        backup_dir = self.full_backup_dir if backup_type == 'full' else self.incremental_backup_dir
        backup_file = backup_dir / f'backup_{backup_id}.gz'
        checksum_file = backup_file.with_suffix('.md5')
        
        if not backup_file.exists() or not checksum_file.exists():
            return False
        
        try:
            # 读取备份文件
            async with aiofiles.open(backup_file, 'rb') as f:
                content = await f.read()
            
            # 计算校验和
            calculated_checksum = hashlib.md5(content).hexdigest()
            
            # 读取存储的校验和
            async with aiofiles.open(checksum_file, 'r') as f:
                stored_checksum = await f.read()
            
            # 验证校验和
            return calculated_checksum == stored_checksum
            
        except Exception as e:
            logger.error(f"Backup verification failed: {e}", exc_info=True)
            return False
    
    async def restore_backup(self, backup_id: str, backup_type: str = 'full') -> bool:
        """恢复备份"""
        if not await self.verify_backup(backup_id, backup_type):
            raise ValueError(f"Backup {backup_id} verification failed")
        
        backup_dir = self.full_backup_dir if backup_type == 'full' else self.incremental_backup_dir
        backup_file = backup_dir / f'backup_{backup_id}.gz'
        
        try:
            # 读取备份数据
            async with aiofiles.open(backup_file, 'rb') as f:
                content = await f.read()
            data = json.loads(gzip.decompress(content))
            
            # 恢复数据
            session = self.Session()
            try:
                metadata = MetaData()
                metadata.reflect(bind=self.engine)
                
                for table_name, rows in data.items():
                    table = metadata.tables[table_name]
                    if backup_type == 'full':
                        # 全量恢复：先清空表
                        session.execute(table.delete())
                    
                    # 插入数据
                    if rows:
                        session.execute(table.insert(), rows)
                
                session.commit()
                logger.info(f"Backup {backup_id} restored successfully")
                return True
                
            except Exception as e:
                session.rollback()
                raise
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Backup restoration failed: {e}", exc_info=True)
            if self.alert_engine:
                await self.alert_engine.send_alert(
                    title="Backup Restoration Failed",
                    message=str(e),
                    level="error"
                )
            raise
    
    async def cleanup_old_backups(self, days: int = 30):
        """清理旧备份"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        try:
            # 清理全量备份
            for backup_file in self.full_backup_dir.glob('backup_*.gz'):
                backup_date = datetime.strptime(backup_file.stem[7:], '%Y%m%d_%H%M%S')
                if backup_date < cutoff_date:
                    backup_file.unlink()
                    checksum_file = backup_file.with_suffix('.md5')
                    if checksum_file.exists():
                        checksum_file.unlink()
            
            # 清理增量备份
            for backup_file in self.incremental_backup_dir.glob('backup_*.gz'):
                backup_date = datetime.strptime(backup_file.stem[7:], '%Y%m%d_%H%M%S')
                if backup_date < cutoff_date:
                    backup_file.unlink()
                    checksum_file = backup_file.with_suffix('.md5')
                    if checksum_file.exists():
                        checksum_file.unlink()
            
            logger.info(f"Cleaned up backups older than {days} days")
            
        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}", exc_info=True)
            if self.alert_engine:
                await self.alert_engine.send_alert(
                    title="Backup Cleanup Failed",
                    message=str(e),
                    level="error"
                )
            raise
    
    def get_backup_info(self) -> Dict:
        """获取备份信息"""
        return {
            'last_full_backup': self.last_full_backup.isoformat() if self.last_full_backup else None,
            'last_incremental_backup': self.last_incremental_backup.isoformat() if self.last_incremental_backup else None,
            'backup_dir': str(self.backup_dir),
            'full_backups': len(list(self.full_backup_dir.glob('backup_*.gz'))),
            'incremental_backups': len(list(self.incremental_backup_dir.glob('backup_*.gz')))
        } 