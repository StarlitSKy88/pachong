from typing import Dict, Any, List, Optional
import time
import asyncio
from datetime import datetime
from abc import ABC, abstractmethod
from ..utils.logger import get_logger

class BaseMonitor(ABC):
    """监控基类"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger(f"{name}_monitor")
        self.metrics = {}  # 指标数据
        self.alerts = []  # 告警列表
        self.check_interval = 60  # 检查间隔（秒）
        self._running = False
        self._task = None
        
    async def start(self):
        """启动监控"""
        if self._running:
            return
            
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
        self.logger.info(f"{self.name} monitor started")
        
    async def stop(self):
        """停止监控"""
        if not self._running:
            return
            
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self.logger.info(f"{self.name} monitor stopped")
        
    async def _monitor_loop(self):
        """监控循环"""
        while self._running:
            try:
                # 收集指标
                metrics = await self.collect_metrics()
                self.metrics.update(metrics)
                
                # 检查告警
                alerts = await self.check_alerts()
                if alerts:
                    await self.handle_alerts(alerts)
                    
                # 导出指标
                await self.export_metrics()
                
            except Exception as e:
                self.logger.error(f"Error in monitor loop: {str(e)}")
                
            await asyncio.sleep(self.check_interval)
            
    @abstractmethod
    async def collect_metrics(self) -> Dict[str, Any]:
        """收集指标
        
        Returns:
            指标数据
        """
        pass
        
    @abstractmethod
    async def check_alerts(self) -> List[Dict]:
        """检查告警
        
        Returns:
            告警列表
        """
        pass
        
    @abstractmethod
    async def handle_alerts(self, alerts: List[Dict]):
        """处理告警
        
        Args:
            alerts: 告警列表
        """
        pass
        
    @abstractmethod
    async def export_metrics(self):
        """导出指标"""
        pass
        
    def get_metrics(self) -> Dict[str, Any]:
        """获取指标数据"""
        return self.metrics
        
    def get_alerts(self) -> List[Dict]:
        """获取告警列表"""
        return self.alerts 