from typing import Dict, List, Any, Optional
import psutil
import time
import logging
from datetime import datetime, timedelta
from ..database import content_dao, task_log_dao, error_log_dao, request_log_dao
from ..crawlers import XHSCrawler, BiliBiliCrawler
import asyncio
from collections import defaultdict, deque
from dataclasses import dataclass, field
from ..utils.proxy_manager import ProxyManager
from ..utils.cookie_manager import CookieManager

@dataclass
class Metric:
    """指标数据类"""
    value: Any
    timestamp: datetime = field(default_factory=datetime.now)
    unit: str = ""
    description: str = ""

class MetricsCollector:
    """监控指标收集器"""
    
    def __init__(self):
        self.logger = logging.getLogger('MetricsCollector')
        self.metrics: Dict[str, Metric] = {}
        self.crawlers = {
            'xhs': XHSCrawler(),
            'bilibili': BiliBiliCrawler()
        }
        self.history_size = 1440  # 保存24小时的数据(每分钟一个点)
        self.history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=self.history_size))
        
        # 初始化依赖组件
        self.proxy_manager = ProxyManager()
        self.cookie_manager = CookieManager()
        
        # 初始化历史数据结构
        self._init_history_metrics()
    
    def _init_history_metrics(self):
        """初始化需要保存历史数据的指标"""
        history_metrics = [
            'system.cpu.usage',
            'system.memory.percent',
            'system.disk.percent',
            'crawler.xhs.content.rate',
            'crawler.bilibili.content.rate',
            'proxy.available_count',
            'proxy.success_rate',
            'cookie.valid_count',
            'cookie.success_rate',
            'request.success_rate',
            'request.latency_avg'
        ]
        for metric in history_metrics:
            self.history[metric] = deque(maxlen=self.history_size)
    
    async def collect_system_metrics(self):
        """收集系统指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics['system.cpu.usage'] = Metric(
                value=cpu_percent,
                unit='%',
                description='CPU使用率'
            )
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            self.metrics['system.memory.total'] = Metric(
                value=memory.total / (1024 * 1024 * 1024),
                unit='GB',
                description='总内存'
            )
            self.metrics['system.memory.used'] = Metric(
                value=memory.used / (1024 * 1024 * 1024),
                unit='GB',
                description='已用内存'
            )
            self.metrics['system.memory.percent'] = Metric(
                value=memory.percent,
                unit='%',
                description='内存使用率'
            )
            
            # 磁盘使用情况
            disk = psutil.disk_usage('/')
            self.metrics['system.disk.total'] = Metric(
                value=disk.total / (1024 * 1024 * 1024),
                unit='GB',
                description='总磁盘空间'
            )
            self.metrics['system.disk.used'] = Metric(
                value=disk.used / (1024 * 1024 * 1024),
                unit='GB',
                description='已用磁盘空间'
            )
            self.metrics['system.disk.percent'] = Metric(
                value=disk.percent,
                unit='%',
                description='磁盘使用率'
            )
            
            # 网络IO
            net_io = psutil.net_io_counters()
            self.metrics['system.network.bytes_sent'] = Metric(
                value=net_io.bytes_sent / (1024 * 1024),
                unit='MB',
                description='发送流量'
            )
            self.metrics['system.network.bytes_recv'] = Metric(
                value=net_io.bytes_recv / (1024 * 1024),
                unit='MB',
                description='接收流量'
            )
            
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {str(e)}")
    
    async def collect_crawler_metrics(self):
        """收集爬虫指标"""
        try:
            # 获取最近24小时的数据
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)
            
            # 内容统计
            for platform, crawler in self.crawlers.items():
                # 总内容数
                total_count = await content_dao.count_by_platform(platform)
                self.metrics[f'crawler.{platform}.content.total'] = Metric(
                    value=total_count,
                    unit='条',
                    description=f'{platform}总内容数'
                )
                
                # 最近24小时内容数
                recent_count = await content_dao.count_by_platform_and_time_range(
                    platform=platform,
                    start_time=start_time,
                    end_time=end_time
                )
                self.metrics[f'crawler.{platform}.content.recent'] = Metric(
                    value=recent_count,
                    unit='条',
                    description=f'{platform}近24小时内容数'
                )
                
                # 爬取速率（每小时）
                hourly_rate = recent_count / 24
                self.metrics[f'crawler.{platform}.content.rate'] = Metric(
                    value=hourly_rate,
                    unit='条/小时',
                    description=f'{platform}爬取速率'
                )
            
            # 任务统计
            task_stats = await task_log_dao.get_task_stats(days=1)
            for task_type, count in task_stats['type_stats'].items():
                self.metrics[f'crawler.{task_type}.count'] = Metric(
                    value=count,
                    unit='条',
                    description=f'{task_type}总任务数'
                )
            
            # 任务状态统计
            for status, count in task_stats['status_stats'].items():
                self.metrics[f'crawler.status.{status}'] = Metric(
                    value=count,
                    unit='条',
                    description=f'{status}状态任务数'
                )
            
            # 计算任务成功率
            total_tasks = sum(task_stats['status_stats'].values())
            if total_tasks > 0:
                success_rate = task_stats['status_stats'].get('success', 0) / total_tasks
                self.metrics['crawler.success_rate'] = Metric(
                    value=success_rate,
                    unit='%',
                    description='任务成功率'
                )
            
            # 错误统计
            error_stats = await self._get_error_stats(platform)
            self.metrics[f'crawler.error.count'] = Metric(
                value=error_stats['total'],
                unit='条',
                description='错误总数'
            )
            self.metrics[f'crawler.error.rate'] = Metric(
                value=error_stats['rate'],
                unit='条/小时',
                description='错误率'
            )
            
        except Exception as e:
            self.logger.error(f"Error collecting crawler metrics: {str(e)}")
    
    async def collect_proxy_metrics(self):
        """收集代理池指标"""
        try:
            # 代理数量统计
            self.metrics['proxy.total_count'] = Metric(
                value=await self._get_proxy_count(),
                unit='个',
                description='代理总数'
            )
            self.metrics['proxy.available_count'] = Metric(
                value=await self._get_available_proxy_count(),
                unit='个',
                description='可用代理数'
            )
            
            # 代理质量统计
            proxy_stats = await self._get_proxy_stats()
            self.metrics['proxy.success_rate'] = Metric(
                value=proxy_stats['success_rate'],
                unit='%',
                description='代理成功率'
            )
            self.metrics['proxy.avg_latency'] = Metric(
                value=proxy_stats['avg_latency'],
                unit='ms',
                description='代理平均延迟'
            )
            self.metrics['proxy.error_rate'] = Metric(
                value=proxy_stats['error_rate'],
                unit='%',
                description='代理错误率'
            )
            
            # 代理更新统计
            update_stats = await self._get_proxy_update_stats()
            self.metrics['proxy.update_count'] = Metric(
                value=update_stats['count'],
                unit='次',
                description='代理更新次数'
            )
            self.metrics['proxy.last_update'] = Metric(
                value=update_stats['last_update'],
                unit='',
                description='最后更新时间'
            )
            
        except Exception as e:
            self.logger.error(f"Error collecting proxy metrics: {str(e)}")
    
    async def collect_cookie_metrics(self):
        """收集Cookie池指标"""
        try:
            for platform in ['xhs', 'bilibili']:
                # Cookie数量统计
                self.metrics[f'cookie.{platform}.total_count'] = Metric(
                    value=await self._get_cookie_count(platform),
                    unit='个',
                    description=f'{platform} Cookie总数'
                )
                self.metrics[f'cookie.{platform}.valid_count'] = Metric(
                    value=await self._get_valid_cookie_count(platform),
                    unit='个',
                    description=f'{platform}有效Cookie数'
                )
                
                # Cookie质量统计
                cookie_stats = await self._get_cookie_stats(platform)
                self.metrics[f'cookie.{platform}.success_rate'] = Metric(
                    value=cookie_stats['success_rate'],
                    unit='%',
                    description=f'{platform} Cookie成功率'
                )
                self.metrics[f'cookie.{platform}.avg_age'] = Metric(
                    value=cookie_stats['avg_age'],
                    unit='小时',
                    description=f'{platform} Cookie平均年龄'
                )
                self.metrics[f'cookie.{platform}.invalid_rate'] = Metric(
                    value=cookie_stats['invalid_rate'],
                    unit='%',
                    description=f'{platform} Cookie失效率'
                )
                
                # Cookie更新统计
                update_stats = await self._get_cookie_update_stats(platform)
                self.metrics[f'cookie.{platform}.update_count'] = Metric(
                    value=update_stats['count'],
                    unit='次',
                    description=f'{platform} Cookie更新次数'
                )
                self.metrics[f'cookie.{platform}.last_update'] = Metric(
                    value=update_stats['last_update'],
                    unit='',
                    description=f'{platform} Cookie最后更新时间'
                )
                
        except Exception as e:
            self.logger.error(f"Error collecting cookie metrics: {str(e)}")
    
    async def collect_request_metrics(self):
        """收集请求统计指标"""
        try:
            for platform in ['xhs', 'bilibili']:
                # 请求统计
                request_stats = await self._get_request_stats(platform)
                self.metrics[f'request.{platform}.total'] = Metric(
                    value=request_stats['total'],
                    unit='次',
                    description=f'{platform}总请求数'
                )
                self.metrics[f'request.{platform}.success'] = Metric(
                    value=request_stats['success'],
                    unit='次',
                    description=f'{platform}成功请求数'
                )
                self.metrics[f'request.{platform}.failed'] = Metric(
                    value=request_stats['failed'],
                    unit='次',
                    description=f'{platform}失败请求数'
                )
                
                # 性能统计
                self.metrics[f'request.{platform}.success_rate'] = Metric(
                    value=request_stats['success_rate'],
                    unit='%',
                    description=f'{platform}请求成功率'
                )
                self.metrics[f'request.{platform}.latency_avg'] = Metric(
                    value=request_stats['latency_avg'],
                    unit='ms',
                    description=f'{platform}平均延迟'
                )
                self.metrics[f'request.{platform}.latency_p95'] = Metric(
                    value=request_stats['latency_p95'],
                    unit='ms',
                    description=f'{platform}P95延迟'
                )
                
                # 限流统计
                self.metrics[f'request.{platform}.throttled'] = Metric(
                    value=request_stats['throttled'],
                    unit='次',
                    description=f'{platform}被限流次数'
                )
                self.metrics[f'request.{platform}.retry'] = Metric(
                    value=request_stats['retry'],
                    unit='次',
                    description=f'{platform}重试次数'
                )
                
        except Exception as e:
            self.logger.error(f"Error collecting request metrics: {str(e)}")
    
    async def collect_all_metrics(self):
        """收集所有指标"""
        await self.collect_system_metrics()
        await self.collect_crawler_metrics()
        await self.collect_proxy_metrics()
        await self.collect_cookie_metrics()
        await self.collect_request_metrics()
        
        # 更新历史数据
        self._update_history()
    
    def get_metric(self, name: str) -> Optional[Metric]:
        """获取指标"""
        return self.metrics.get(name)
    
    def get_all_metrics(self) -> Dict[str, Metric]:
        """获取所有指标"""
        return self.metrics
    
    def get_metrics_by_prefix(self, prefix: str) -> Dict[str, Metric]:
        """获取指定前缀的指标"""
        return {
            name: metric for name, metric in self.metrics.items()
            if name.startswith(prefix)
        }
    
    def clear_metrics(self):
        """清除所有指标"""
        self.metrics.clear()
    
    def get_metrics_in_range(self, start_time: datetime, end_time: datetime) -> Dict[str, Metric]:
        """获取指定时间范围内的指标"""
        return {
            name: metric for name, metric in self.metrics.items()
            if start_time <= metric.timestamp <= end_time
        }
    
    def _update_history(self):
        """更新历史数据"""
        for metric_name, metric in self.metrics.items():
            if metric_name in self.history:
                self.history[metric_name].append((metric.timestamp, metric.value))
    
    def get_history(self, metric_name: str, hours: int = 24) -> list:
        """获取指标历史数据"""
        if metric_name not in self.history:
            return []
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            (ts, val) for ts, val in self.history[metric_name]
            if ts >= cutoff_time
        ]
    
    # 以下是辅助方法，需要根据实际情况实现
    async def _get_error_stats(self, platform: str) -> Dict[str, Any]:
        """获取错误统计"""
        try:
            # 获取最近24小时的错误日志
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)
            
            error_logs = await error_log_dao.get_error_logs(
                platform=platform,
                start_time=start_time,
                end_time=end_time
            )
            
            # 统计错误总数和类型分布
            total_errors = len(error_logs)
            error_types = defaultdict(int)
            for log in error_logs:
                error_types[log.error_type] += 1
            
            # 计算错误率（每小时）
            error_rate = total_errors / 24
            
            return {
                'total': total_errors,
                'rate': error_rate,
                'types': dict(error_types)
            }
        except Exception as e:
            self.logger.error(f"Error getting error stats: {str(e)}")
            return {'total': 0, 'rate': 0, 'types': {}}
    
    async def _get_proxy_count(self) -> int:
        """获取代理总数"""
        try:
            return len(self.proxy_manager.proxies)
        except Exception as e:
            self.logger.error(f"Error getting proxy count: {str(e)}")
            return 0
    
    async def _get_available_proxy_count(self) -> int:
        """获取可用代理数"""
        try:
            return len([
                proxy for proxy in self.proxy_manager.proxies
                if proxy.is_valid and proxy.fail_count < self.proxy_manager.max_fail_count
            ])
        except Exception as e:
            self.logger.error(f"Error getting available proxy count: {str(e)}")
            return 0
    
    async def _get_proxy_stats(self) -> Dict[str, Any]:
        """获取代理统计信息"""
        try:
            proxies = self.proxy_manager.proxies
            if not proxies:
                return {
                    'success_rate': 0,
                    'avg_latency': 0,
                    'error_rate': 0
                }
            
            # 计算成功率
            total_requests = sum(p.total_count for p in proxies)
            total_success = sum(p.success_count for p in proxies)
            success_rate = (total_success / total_requests * 100) if total_requests > 0 else 0
            
            # 计算平均延迟
            valid_latencies = [p.avg_latency for p in proxies if p.avg_latency > 0]
            avg_latency = sum(valid_latencies) / len(valid_latencies) if valid_latencies else 0
            
            # 计算错误率
            error_rate = 100 - success_rate
            
            return {
                'success_rate': success_rate,
                'avg_latency': avg_latency,
                'error_rate': error_rate
            }
        except Exception as e:
            self.logger.error(f"Error getting proxy stats: {str(e)}")
            return {
                'success_rate': 0,
                'avg_latency': 0,
                'error_rate': 0
            }
    
    async def _get_proxy_update_stats(self) -> Dict[str, Any]:
        """获取代理更新统计"""
        try:
            return {
                'count': self.proxy_manager.update_count,
                'last_update': self.proxy_manager.last_update_time
            }
        except Exception as e:
            self.logger.error(f"Error getting proxy update stats: {str(e)}")
            return {
                'count': 0,
                'last_update': datetime.min
            }
    
    async def _get_cookie_count(self, platform: str) -> int:
        """获取Cookie总数"""
        try:
            return len(self.cookie_manager.cookies[platform])
        except Exception as e:
            self.logger.error(f"Error getting cookie count: {str(e)}")
            return 0
    
    async def _get_valid_cookie_count(self, platform: str) -> int:
        """获取有效Cookie数"""
        try:
            return len([
                cookie for cookie in self.cookie_manager.cookies[platform]
                if cookie['is_valid'] and cookie['fail_count'] < self.cookie_manager.max_fail_count
            ])
        except Exception as e:
            self.logger.error(f"Error getting valid cookie count: {str(e)}")
            return 0
    
    async def _get_cookie_stats(self, platform: str) -> Dict[str, Any]:
        """获取Cookie统计信息"""
        try:
            cookies = self.cookie_manager.cookies[platform]
            if not cookies:
                return {
                    'success_rate': 0,
                    'avg_age': 0,
                    'invalid_rate': 0
                }
            
            # 计算成功率
            total_requests = sum(c['total_count'] for c in cookies)
            total_success = sum(c['success_count'] for c in cookies)
            success_rate = (total_success / total_requests * 100) if total_requests > 0 else 0
            
            # 计算平均年龄（小时）
            now = datetime.now()
            ages = [(now - c['add_time']).total_seconds() / 3600 for c in cookies]
            avg_age = sum(ages) / len(ages) if ages else 0
            
            # 计算失效率
            invalid_count = len([c for c in cookies if not c['is_valid']])
            invalid_rate = (invalid_count / len(cookies) * 100) if cookies else 0
            
            return {
                'success_rate': success_rate,
                'avg_age': avg_age,
                'invalid_rate': invalid_rate
            }
        except Exception as e:
            self.logger.error(f"Error getting cookie stats: {str(e)}")
            return {
                'success_rate': 0,
                'avg_age': 0,
                'invalid_rate': 0
            }
    
    async def _get_cookie_update_stats(self, platform: str) -> Dict[str, Any]:
        """获取Cookie更新统计"""
        try:
            return {
                'count': self.cookie_manager.update_count[platform],
                'last_update': self.cookie_manager.last_update_time[platform]
            }
        except Exception as e:
            self.logger.error(f"Error getting cookie update stats: {str(e)}")
            return {
                'count': 0,
                'last_update': datetime.min
            }
    
    async def _get_request_stats(self, platform: str) -> Dict[str, Any]:
        """获取请求统计信息"""
        try:
            # 获取最近24小时的请求日志
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)
            
            request_logs = await request_log_dao.get_request_logs(
                platform=platform,
                start_time=start_time,
                end_time=end_time
            )
            
            if not request_logs:
                return {
                    'total': 0,
                    'success': 0,
                    'failed': 0,
                    'success_rate': 0,
                    'latency_avg': 0,
                    'latency_p95': 0,
                    'throttled': 0,
                    'retry': 0
                }
            
            # 基础统计
            total = len(request_logs)
            success = len([r for r in request_logs if r.status_code == 200])
            failed = total - success
            success_rate = (success / total * 100) if total > 0 else 0
            
            # 延迟统计
            latencies = [r.latency for r in request_logs if r.latency is not None]
            latency_avg = sum(latencies) / len(latencies) if latencies else 0
            latency_p95 = sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0
            
            # 限流和重试统计
            throttled = len([r for r in request_logs if r.is_throttled])
            retry = len([r for r in request_logs if r.retry_count > 0])
            
            return {
                'total': total,
                'success': success,
                'failed': failed,
                'success_rate': success_rate,
                'latency_avg': latency_avg,
                'latency_p95': latency_p95,
                'throttled': throttled,
                'retry': retry
            }
        except Exception as e:
            self.logger.error(f"Error getting request stats: {str(e)}")
            return {
                'total': 0,
                'success': 0,
                'failed': 0,
                'success_rate': 0,
                'latency_avg': 0,
                'latency_p95': 0,
                'throttled': 0,
                'retry': 0
            } 