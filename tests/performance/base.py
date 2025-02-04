"""性能测试基类

该模块定义了性能测试的基础类，包括：
1. 测试环境准备
2. 性能数据收集
3. 结果分析和报告
4. 资源监控
"""

import logging
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from abc import ABC, abstractmethod
import json
import pandas as pd
import numpy as np
from pathlib import Path

from .config import (
    get_scenario_config,
    get_performance_baseline,
    get_resource_baseline,
    get_test_data
)

logger = logging.getLogger(__name__)

class PerformanceTest(ABC):
    """性能测试基类"""
    
    def __init__(
        self,
        name: str,
        component: str,
        scenario: str,
        load_level: str = 'normal_load',
        output_dir: Optional[str] = None
    ):
        self.name = name
        self.component = component
        self.scenario = scenario
        self.load_level = load_level
        
        # 加载配置
        self.config = get_scenario_config(scenario, load_level)
        self.baseline = get_performance_baseline(component)
        self.resource_baseline = get_resource_baseline()
        self.test_data = get_test_data(component)
        
        # 设置输出目录
        self.output_dir = Path(output_dir or f'test_results/{name}')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 性能数据
        self.metrics: Dict[str, List[Dict]] = {
            'response_time': [],
            'error_rate': [],
            'throughput': [],
            'resource_usage': []
        }
        
        # 测试状态
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.is_running = False
        
        # 监控间隔
        self.monitor_interval = 5  # 秒
        
        # 初始化日志
        self._init_logger()
    
    def _init_logger(self):
        """初始化日志"""
        log_file = self.output_dir / f'{self.name}.log'
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        self.logger = logging.getLogger(f'PerformanceTest.{self.name}')
        self.logger.addHandler(file_handler)
    
    async def setup(self):
        """测试环境准备"""
        self.logger.info(f"Setting up test: {self.name}")
        self.logger.info(f"Configuration: {json.dumps(self.config, indent=2)}")
        
        # 清理历史数据
        for metric in self.metrics:
            self.metrics[metric].clear()
        
        # 准备测试数据
        await self.prepare_test_data()
        
        # 准备测试环境
        await self.prepare_environment()
    
    async def run(self):
        """运行测试"""
        try:
            # 设置测试状态
            self.is_running = True
            self.start_time = datetime.now()
            
            self.logger.info(f"Starting test: {self.name}")
            self.logger.info(f"Start time: {self.start_time}")
            
            # 预热阶段
            self.logger.info("Starting warm-up phase")
            await self.warm_up()
            
            # 测试阶段
            self.logger.info("Starting test phase")
            await asyncio.gather(
                self.run_test(),
                self.monitor_resources()
            )
            
            # 冷却阶段
            self.logger.info("Starting cool-down phase")
            await self.cool_down()
            
        except Exception as e:
            self.logger.error(f"Test failed: {e}")
            raise
            
        finally:
            # 结束测试
            self.is_running = False
            self.end_time = datetime.now()
            self.logger.info(f"Test completed: {self.name}")
            self.logger.info(f"End time: {self.end_time}")
            
            # 生成报告
            await self.generate_report()
    
    async def warm_up(self):
        """预热阶段"""
        await asyncio.sleep(self.config['ramp_up'])
    
    async def cool_down(self):
        """冷却阶段"""
        await asyncio.sleep(self.config['cool_down'])
    
    async def monitor_resources(self):
        """监控系统资源"""
        while self.is_running:
            try:
                # 收集资源使用情况
                cpu_usage = await self.get_cpu_usage()
                memory_usage = await self.get_memory_usage()
                disk_usage = await self.get_disk_usage()
                
                # 记录指标
                self.metrics['resource_usage'].append({
                    'timestamp': datetime.now(),
                    'cpu_usage': cpu_usage,
                    'memory_usage': memory_usage,
                    'disk_usage': disk_usage
                })
                
                # 检查资源使用是否超过基准
                self._check_resource_usage(cpu_usage, memory_usage, disk_usage)
                
            except Exception as e:
                self.logger.error(f"Error monitoring resources: {e}")
                
            finally:
                await asyncio.sleep(self.monitor_interval)
    
    def _check_resource_usage(
        self,
        cpu_usage: float,
        memory_usage: float,
        disk_usage: float
    ):
        """检查资源使用情况"""
        # 检查CPU使用率
        if cpu_usage >= self.resource_baseline['cpu_usage']['critical']:
            self.logger.critical(f"CPU usage critical: {cpu_usage}%")
        elif cpu_usage >= self.resource_baseline['cpu_usage']['warning']:
            self.logger.warning(f"CPU usage high: {cpu_usage}%")
            
        # 检查内存使用率
        if memory_usage >= self.resource_baseline['memory_usage']['critical']:
            self.logger.critical(f"Memory usage critical: {memory_usage}%")
        elif memory_usage >= self.resource_baseline['memory_usage']['warning']:
            self.logger.warning(f"Memory usage high: {memory_usage}%")
            
        # 检查磁盘使用率
        if disk_usage >= self.resource_baseline['disk_usage']['critical']:
            self.logger.critical(f"Disk usage critical: {disk_usage}%")
        elif disk_usage >= self.resource_baseline['disk_usage']['warning']:
            self.logger.warning(f"Disk usage high: {disk_usage}%")
    
    def record_metric(
        self,
        metric_type: str,
        value: float,
        tags: Optional[Dict] = None
    ):
        """记录性能指标"""
        if metric_type not in self.metrics:
            raise ValueError(f"Unknown metric type: {metric_type}")
            
        self.metrics[metric_type].append({
            'timestamp': datetime.now(),
            'value': value,
            **(tags or {})
        })
    
    async def generate_report(self):
        """生成测试报告"""
        self.logger.info("Generating test report")
        
        # 计算测试时间
        duration = self.end_time - self.start_time
        
        # 分析性能指标
        response_time_stats = self._analyze_response_time()
        error_rate_stats = self._analyze_error_rate()
        throughput_stats = self._analyze_throughput()
        resource_stats = self._analyze_resource_usage()
        
        # 生成报告
        report = {
            'test_info': {
                'name': self.name,
                'component': self.component,
                'scenario': self.scenario,
                'load_level': self.load_level,
                'start_time': self.start_time.isoformat(),
                'end_time': self.end_time.isoformat(),
                'duration': str(duration)
            },
            'performance_metrics': {
                'response_time': response_time_stats,
                'error_rate': error_rate_stats,
                'throughput': throughput_stats
            },
            'resource_usage': resource_stats,
            'baseline_comparison': self._compare_with_baseline(
                response_time_stats,
                error_rate_stats,
                throughput_stats
            )
        }
        
        # 保存报告
        report_file = self.output_dir / f'report_{self.start_time:%Y%m%d_%H%M%S}.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        self.logger.info(f"Test report generated: {report_file}")
        
        return report
    
    def _analyze_response_time(self) -> Dict[str, float]:
        """分析响应时间"""
        if not self.metrics['response_time']:
            return {}
            
        values = [m['value'] for m in self.metrics['response_time']]
        return {
            'min': float(np.min(values)),
            'max': float(np.max(values)),
            'mean': float(np.mean(values)),
            'p50': float(np.percentile(values, 50)),
            'p90': float(np.percentile(values, 90)),
            'p95': float(np.percentile(values, 95)),
            'p99': float(np.percentile(values, 99))
        }
    
    def _analyze_error_rate(self) -> Dict[str, float]:
        """分析错误率"""
        if not self.metrics['error_rate']:
            return {}
            
        values = [m['value'] for m in self.metrics['error_rate']]
        return {
            'min': float(np.min(values)),
            'max': float(np.max(values)),
            'mean': float(np.mean(values))
        }
    
    def _analyze_throughput(self) -> Dict[str, float]:
        """分析吞吐量"""
        if not self.metrics['throughput']:
            return {}
            
        values = [m['value'] for m in self.metrics['throughput']]
        return {
            'min': float(np.min(values)),
            'max': float(np.max(values)),
            'mean': float(np.mean(values))
        }
    
    def _analyze_resource_usage(self) -> Dict[str, Dict[str, float]]:
        """分析资源使用情况"""
        if not self.metrics['resource_usage']:
            return {}
            
        result = {}
        for metric in ['cpu_usage', 'memory_usage', 'disk_usage']:
            values = [m[metric] for m in self.metrics['resource_usage']]
            result[metric] = {
                'min': float(np.min(values)),
                'max': float(np.max(values)),
                'mean': float(np.mean(values))
            }
        return result
    
    def _compare_with_baseline(
        self,
        response_time: Dict[str, float],
        error_rate: Dict[str, float],
        throughput: Dict[str, float]
    ) -> Dict[str, Any]:
        """与基准比较"""
        result = {
            'response_time': {},
            'error_rate': {},
            'throughput': {}
        }
        
        # 比较响应时间
        for percentile in ['p50', 'p90', 'p95', 'p99']:
            if percentile in response_time:
                baseline = self.baseline['response_time'][percentile]
                actual = response_time[percentile]
                result['response_time'][percentile] = {
                    'baseline': baseline,
                    'actual': actual,
                    'diff': actual - baseline,
                    'diff_percent': (actual - baseline) / baseline * 100
                }
        
        # 比较错误率
        if 'mean' in error_rate:
            baseline = self.baseline['error_rate']['normal']
            actual = error_rate['mean']
            result['error_rate'] = {
                'baseline': baseline,
                'actual': actual,
                'diff': actual - baseline,
                'diff_percent': (actual - baseline) / baseline * 100
            }
        
        # 比较吞吐量
        if 'mean' in throughput:
            baseline = self.baseline['throughput'][self.load_level]
            actual = throughput['mean']
            result['throughput'] = {
                'baseline': baseline,
                'actual': actual,
                'diff': actual - baseline,
                'diff_percent': (actual - baseline) / baseline * 100
            }
        
        return result
    
    @abstractmethod
    async def prepare_test_data(self):
        """准备测试数据"""
        pass
    
    @abstractmethod
    async def prepare_environment(self):
        """准备测试环境"""
        pass
    
    @abstractmethod
    async def run_test(self):
        """运行测试"""
        pass
    
    @abstractmethod
    async def get_cpu_usage(self) -> float:
        """获取CPU使用率"""
        pass
    
    @abstractmethod
    async def get_memory_usage(self) -> float:
        """获取内存使用率"""
        pass
    
    @abstractmethod
    async def get_disk_usage(self) -> float:
        """获取磁盘使用率"""
        pass 