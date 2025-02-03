from typing import Dict, List, Any, Optional, Callable
import logging
from abc import ABC, abstractmethod
from datetime import datetime
import psutil
import os
import json
import asyncio
from loguru import logger

class Metric:
    """监控指标"""
    
    def __init__(self, name: str, value: Any, timestamp: datetime = None):
        """初始化
        
        Args:
            name: 指标名称
            value: 指标值
            timestamp: 时间戳
        """
        self.name = name
        self.value = value
        self.timestamp = timestamp or datetime.now()
        self.tags: Dict[str, str] = {}
        
    def add_tag(self, key: str, value: str):
        """添加标签"""
        self.tags[key] = value
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'value': self.value,
            'timestamp': self.timestamp,
            'tags': self.tags
        }

class Alert:
    """告警信息"""
    
    def __init__(self, name: str, message: str, level: str = 'info'):
        """初始化
        
        Args:
            name: 告警名称
            message: 告警消息
            level: 告警级别(info/warning/error/critical)
        """
        self.name = name
        self.message = message
        self.level = level
        self.timestamp = datetime.now()
        self.tags: Dict[str, str] = {}
        
    def add_tag(self, key: str, value: str):
        """添加标签"""
        self.tags[key] = value
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'message': self.message,
            'level': self.level,
            'timestamp': self.timestamp,
            'tags': self.tags
        }

class BaseMonitor(ABC):
    """监控系统基类"""
    
    def __init__(self):
        """初始化监控系统"""
        self.logger = logger.bind(name=self.__class__.__name__)
        self.metrics: List[Metric] = []
        self.alerts: List[Alert] = []
        self.handlers: Dict[str, List[Callable]] = {
            'metric': [],
            'alert': []
        }
        self.running = False
        self.collect_interval = 60  # 采集间隔(秒)
    
    def add_metric_handler(self, handler: Callable[[Metric], None]):
        """添加指标处理器"""
        self.handlers['metric'].append(handler)
    
    def add_alert_handler(self, handler: Callable[[Alert], None]):
        """添加告警处理器"""
        self.handlers['alert'].append(handler)
    
    async def collect_metrics(self):
        """采集指标"""
        while self.running:
            try:
                # 采集指标
                metrics = await self._collect()
                
                # 处理指标
                for metric in metrics:
                    self.metrics.append(metric)
                    # 调用处理器
                    for handler in self.handlers['metric']:
                        try:
                            await handler(metric)
                        except Exception as e:
                            self.logger.error(f"处理指标失败: {str(e)}")
                            
                # 检查告警
                alerts = await self._check_alerts()
                
                # 处理告警
                for alert in alerts:
                    self.alerts.append(alert)
                    # 调用处理器
                    for handler in self.handlers['alert']:
                        try:
                            await handler(alert)
                        except Exception as e:
                            self.logger.error(f"处理告警失败: {str(e)}")
                            
            except Exception as e:
                self.logger.error(f"采集指标失败: {str(e)}")
                
            # 等待下次采集
            await asyncio.sleep(self.collect_interval)
            
    @abstractmethod
    async def _collect(self) -> List[Metric]:
        """采集指标
        
        Returns:
            指标列表
        """
        pass
    
    @abstractmethod
    async def _check_alerts(self) -> List[Alert]:
        """检查告警
        
        Returns:
            告警列表
        """
        pass
    
    async def start(self):
        """启动监控"""
        self.running = True
        asyncio.create_task(self.collect_metrics())
    
    async def stop(self):
        """停止监控"""
        self.running = False
    
    def get_metrics(self, name: Optional[str] = None) -> List[Metric]:
        """获取指标
        
        Args:
            name: 指标名称
            
        Returns:
            指标列表
        """
        if name:
            return [m for m in self.metrics if m.name == name]
        return self.metrics
    
    def get_alerts(self, level: Optional[str] = None) -> List[Alert]:
        """获取告警
        
        Args:
            level: 告警级别
            
        Returns:
            告警列表
        """
        if level:
            return [a for a in self.alerts if a.level == level]
        return self.alerts
    
    def clear_metrics(self):
        """清空指标"""
        self.metrics.clear()
    
    def clear_alerts(self):
        """清空告警"""
        self.alerts.clear()
    
    def add_metric(self, name: str, value: Any, labels: Optional[Dict] = None):
        """添加监控指标"""
        self.metrics.append(Metric(name, value))
    
    def get_metric(self, name: str) -> Optional[Metric]:
        """获取监控指标"""
        return next((m for m in self.metrics if m.name == name), None)
    
    def add_alert_rule(self, name: str, rule: Dict):
        """添加告警规则"""
        self.logger.info(f"Added alert rule: {name}")
    
    def remove_alert_rule(self, name: str):
        """移除告警规则"""
        self.logger.info(f"Removed alert rule: {name}")
    
    def add_alert(self, alert: Alert):
        """添加告警"""
        self.alerts.append(alert)
        self.logger.warning(f"Alert: {alert.message}")
    
    def check_alert_rules(self):
        """检查告警规则"""
        for alert in self.alerts:
            try:
                # 检查告警规则
                pass
            except Exception as e:
                self.logger.error(f"Error checking alert rule: {str(e)}")
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统指标"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            self.add_metric('system.cpu.usage', cpu_percent, {'unit': '%'})
            self.add_metric('system.memory.total', memory.total, {'unit': 'bytes'})
            self.add_metric('system.memory.used', memory.used, {'unit': 'bytes'})
            self.add_metric('system.memory.percent', memory.percent, {'unit': '%'})
            self.add_metric('system.disk.total', disk.total, {'unit': 'bytes'})
            self.add_metric('system.disk.used', disk.used, {'unit': 'bytes'})
            self.add_metric('system.disk.percent', disk.percent, {'unit': '%'})
            
            return {
                'cpu': {
                    'usage': cpu_percent
                },
                'memory': {
                    'total': memory.total,
                    'used': memory.used,
                    'percent': memory.percent
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'percent': disk.percent
                }
            }
        except Exception as e:
            self.logger.error(f"Error getting system metrics: {str(e)}")
            return {}
    
    def save_metrics(self, filename: str):
        """保存监控指标"""
        try:
            os.makedirs('output/metrics', exist_ok=True)
            filepath = os.path.join('output/metrics', filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump([m.to_dict() for m in self.metrics], f, indent=2, default=str)
            self.logger.info(f"Metrics saved to {filepath}")
        except Exception as e:
            self.logger.error(f"Error saving metrics: {str(e)}")
    
    def load_metrics(self, filename: str):
        """加载监控指标"""
        try:
            filepath = os.path.join('output/metrics', filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                self.metrics = [Metric(**m) for m in json.load(f)]
            self.logger.info(f"Metrics loaded from {filepath}")
        except Exception as e:
            self.logger.error(f"Error loading metrics: {str(e)}")
    
    @abstractmethod
    async def check_health(self) -> bool:
        """检查健康状态"""
        pass 