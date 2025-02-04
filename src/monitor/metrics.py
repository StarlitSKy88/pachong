"""监控指标模块。"""

import psutil
import time
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, Any, List

from src.models.metrics import get_session, MetricRecord

class Metric:
    def __init__(self, value: float, timestamp: datetime = None):
        self.value = value
        self.timestamp = timestamp or datetime.now()

class MetricsCollector:
    def __init__(self, history_size: int = 1440):  # 默认保存24小时的数据（每分钟一个点）
        self.history_size = history_size
        self.history = defaultdict(lambda: deque(maxlen=history_size))
        self._load_history()
        
    def _load_history(self):
        """从数据库加载历史数据"""
        session = get_session()
        try:
            # 获取最近24小时的数据
            start_time = datetime.now() - timedelta(hours=24)
            records = session.query(MetricRecord).filter(
                MetricRecord.timestamp >= start_time
            ).order_by(MetricRecord.timestamp.asc()).all()
            
            # 按指标名称分组并加载到内存
            for record in records:
                self.history[record.name].append(
                    (record.timestamp, record.value)
                )
        finally:
            session.close()
    
    def _save_metric(self, name: str, value: float, timestamp: datetime = None):
        """保存指标到数据库"""
        session = get_session()
        try:
            record = MetricRecord(
                name=name,
                value=value,
                timestamp=timestamp or datetime.now()
            )
            session.add(record)
            session.commit()
        finally:
            session.close()
        
    async def collect_system_metrics(self) -> Dict[str, Metric]:
        """
        收集系统指标
        """
        metrics = {}
        current_time = datetime.now()
        
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        metrics["system.cpu.usage"] = Metric(cpu_percent, current_time)
        self.history["cpu_usage"].append((current_time, cpu_percent))
        self._save_metric("system.cpu.usage", cpu_percent, current_time)
        
        # 内存使用率
        memory = psutil.virtual_memory()
        metrics["system.memory.percent"] = Metric(memory.percent, current_time)
        self.history["memory_usage"].append((current_time, memory.percent))
        self._save_metric("system.memory.percent", memory.percent, current_time)
        
        # 磁盘使用率
        disk = psutil.disk_usage('/')
        metrics["system.disk.percent"] = Metric(disk.percent, current_time)
        self.history["disk_usage"].append((current_time, disk.percent))
        self._save_metric("system.disk.percent", disk.percent, current_time)
        
        return metrics
    
    async def collect_crawler_metrics(self) -> Dict[str, Metric]:
        """
        收集爬虫指标
        """
        metrics = {}
        current_time = datetime.now()
        
        # 模拟数据，实际项目中应该从数据库获取
        for platform in ["xhs", "bilibili"]:
            metrics[f"crawler.{platform}.content.total"] = Metric(1000, current_time)
            metrics[f"crawler.{platform}.content.recent"] = Metric(100, current_time)
            metrics[f"crawler.{platform}.content.rate"] = Metric(10.5, current_time)
            
            # 保存到数据库
            self._save_metric(f"crawler.{platform}.content.total", 1000, current_time)
            self._save_metric(f"crawler.{platform}.content.recent", 100, current_time)
            self._save_metric(f"crawler.{platform}.content.rate", 10.5, current_time)
        
        return metrics
    
    async def collect_task_metrics(self) -> Dict[str, Metric]:
        """
        收集任务指标
        """
        metrics = {}
        current_time = datetime.now()
        
        # 模拟数据，实际项目中应该从数据库获取
        total_tasks = 1000
        success_tasks = 850
        failed_tasks = 100
        running_tasks = 50
        success_rate = success_tasks / total_tasks if total_tasks > 0 else 0
        
        metrics["task.total"] = Metric(total_tasks, current_time)
        metrics["task.success"] = Metric(success_tasks, current_time)
        metrics["task.failed"] = Metric(failed_tasks, current_time)
        metrics["task.running"] = Metric(running_tasks, current_time)
        metrics["task.success_rate"] = Metric(success_rate, current_time)
        
        # 保存到数据库
        self._save_metric("task.total", total_tasks, current_time)
        self._save_metric("task.success", success_tasks, current_time)
        self._save_metric("task.failed", failed_tasks, current_time)
        self._save_metric("task.running", running_tasks, current_time)
        self._save_metric("task.success_rate", success_rate, current_time)
        
        return metrics
    
    async def collect_all_metrics(self) -> Dict[str, Metric]:
        """
        收集所有指标
        """
        metrics = {}
        metrics.update(await self.collect_system_metrics())
        metrics.update(await self.collect_crawler_metrics())
        metrics.update(await self.collect_task_metrics())
        return metrics
    
    async def get_history_data(self, hours: int = 24) -> Dict[str, List]:
        """
        获取历史数据
        
        Args:
            hours: 获取最近多少小时的数据
        
        Returns:
            包含时间戳和各项指标历史数据的字典
        """
        session = get_session()
        try:
            start_time = datetime.now() - timedelta(hours=hours)
            
            # 从数据库获取数据
            records = session.query(MetricRecord).filter(
                MetricRecord.timestamp >= start_time,
                MetricRecord.name.in_([
                    "system.cpu.usage",
                    "system.memory.percent",
                    "system.disk.percent"
                ])
            ).order_by(MetricRecord.timestamp.asc()).all()
            
            # 整理数据
            result = {
                "timestamps": [],
                "cpu_usage": [],
                "memory_usage": [],
                "disk_usage": []
            }
            
            # 按时间点分组
            data_by_time = defaultdict(dict)
            for record in records:
                data_by_time[record.timestamp][record.name] = record.value
            
            # 确保所有时间点的数据完整
            for timestamp in sorted(data_by_time.keys()):
                result["timestamps"].append(timestamp.strftime("%Y-%m-%d %H:%M:%S"))
                result["cpu_usage"].append(
                    data_by_time[timestamp].get("system.cpu.usage", 0)
                )
                result["memory_usage"].append(
                    data_by_time[timestamp].get("system.memory.percent", 0)
                )
                result["disk_usage"].append(
                    data_by_time[timestamp].get("system.disk.percent", 0)
                )
            
            return result
        finally:
            session.close()
    
    def clean_old_data(self, days: int = 7):
        """清理旧数据"""
        session = get_session()
        try:
            start_time = datetime.now() - timedelta(days=days)
            session.query(MetricRecord).filter(
                MetricRecord.timestamp < start_time
            ).delete()
            session.commit()
        finally:
            session.close() 