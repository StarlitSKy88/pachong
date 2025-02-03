"""性能监控器"""
import psutil
import os
from typing import List, Dict, Any
from datetime import datetime
import asyncio

from .base_monitor import BaseMonitor, Metric, Alert

class PerformanceMonitor(BaseMonitor):
    """性能监控器"""
    
    def __init__(self):
        """初始化"""
        super().__init__()
        self.collect_interval = 5  # 5秒采集一次
        self.process = psutil.Process(os.getpid())
        
        # 告警阈值
        self.thresholds = {
            'cpu_percent': 80,  # CPU使用率阈值
            'memory_percent': 80,  # 内存使用率阈值
            'disk_percent': 80,  # 磁盘使用率阈值
            'network_error_rate': 0.1  # 网络错误率阈值
        }
        
    async def _collect(self) -> List[Metric]:
        """采集性能指标"""
        metrics = []
        
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            metrics.append(Metric('cpu_percent', cpu_percent))
            
            # 内存使用率
            memory = psutil.virtual_memory()
            metrics.append(Metric('memory_percent', memory.percent))
            metrics.append(Metric('memory_used', memory.used))
            metrics.append(Metric('memory_total', memory.total))
            
            # 磁盘使用率
            disk = psutil.disk_usage('/')
            metrics.append(Metric('disk_percent', disk.percent))
            metrics.append(Metric('disk_used', disk.used))
            metrics.append(Metric('disk_total', disk.total))
            
            # 网络IO
            net_io = psutil.net_io_counters()
            metrics.append(Metric('net_bytes_sent', net_io.bytes_sent))
            metrics.append(Metric('net_bytes_recv', net_io.bytes_recv))
            metrics.append(Metric('net_packets_sent', net_io.packets_sent))
            metrics.append(Metric('net_packets_recv', net_io.packets_recv))
            metrics.append(Metric('net_errin', net_io.errin))
            metrics.append(Metric('net_errout', net_io.errout))
            
            # 进程信息
            metrics.append(Metric('process_cpu_percent', self.process.cpu_percent()))
            metrics.append(Metric('process_memory_percent', self.process.memory_percent()))
            metrics.append(Metric('process_threads', len(self.process.threads())))
            metrics.append(Metric('process_fds', self.process.num_fds()))
            
            # 添加标签
            for metric in metrics:
                metric.add_tag('host', os.uname().nodename)
                metric.add_tag('pid', str(os.getpid()))
                
        except Exception as e:
            self.logger.error(f"采集性能指标失败: {str(e)}")
            
        return metrics
        
    async def _check_alerts(self) -> List[Alert]:
        """检查性能告警"""
        alerts = []
        
        try:
            # 获取最新指标
            cpu_metrics = self.get_metrics('cpu_percent')
            memory_metrics = self.get_metrics('memory_percent')
            disk_metrics = self.get_metrics('disk_percent')
            net_error_metrics = self.get_metrics('net_errin') + self.get_metrics('net_errout')
            
            if not cpu_metrics or not memory_metrics or not disk_metrics:
                return alerts
                
            # 检查CPU使用率
            cpu_percent = cpu_metrics[-1].value
            if cpu_percent > self.thresholds['cpu_percent']:
                alerts.append(Alert(
                    'high_cpu_usage',
                    f'CPU使用率过高: {cpu_percent}%',
                    'warning'
                ))
                
            # 检查内存使用率
            memory_percent = memory_metrics[-1].value
            if memory_percent > self.thresholds['memory_percent']:
                alerts.append(Alert(
                    'high_memory_usage',
                    f'内存使用率过高: {memory_percent}%',
                    'warning'
                ))
                
            # 检查磁盘使用率
            disk_percent = disk_metrics[-1].value
            if disk_percent > self.thresholds['disk_percent']:
                alerts.append(Alert(
                    'high_disk_usage',
                    f'磁盘使用率过高: {disk_percent}%',
                    'warning'
                ))
                
            # 检查网络错误率
            if net_error_metrics:
                error_rate = sum(m.value for m in net_error_metrics) / len(net_error_metrics)
                if error_rate > self.thresholds['network_error_rate']:
                    alerts.append(Alert(
                        'high_network_errors',
                        f'网络错误率过高: {error_rate:.2%}',
                        'error'
                    ))
                    
            # 添加标签
            for alert in alerts:
                alert.add_tag('host', os.uname().nodename)
                alert.add_tag('pid', str(os.getpid()))
                
        except Exception as e:
            self.logger.error(f"检查性能告警失败: {str(e)}")
            
        return alerts
        
    def set_threshold(self, metric: str, value: float):
        """设置告警阈值
        
        Args:
            metric: 指标名称
            value: 阈值
        """
        self.thresholds[metric] = value
        
    async def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        try:
            return {
                'hostname': os.uname().nodename,
                'platform': os.uname().sysname,
                'release': os.uname().release,
                'version': os.uname().version,
                'machine': os.uname().machine,
                'processor': os.uname().processor,
                'cpu_count': psutil.cpu_count(),
                'memory_total': psutil.virtual_memory().total,
                'disk_total': psutil.disk_usage('/').total,
                'boot_time': datetime.fromtimestamp(psutil.boot_time())
            }
        except Exception as e:
            self.logger.error(f"获取系统信息失败: {str(e)}")
            return {} 