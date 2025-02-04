from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from .base_monitor import BaseMonitor
from ..database import content_dao, task_log_dao
from ..crawlers import XHSCrawler, BiliBiliCrawler
from ..models import Content
from ..crawlers.proxy_manager import ProxyManager
from ..crawlers.cookie_manager import CookieManager
import time
import aiohttp
import asyncio
from ..utils.logger import get_logger
from loguru import logger
from ..utils.error_handler import MonitorError

class CrawlerMonitor(BaseMonitor):
    """爬虫监控类"""
    
    def __init__(self, name: str = "crawler_monitor"):
        """初始化爬虫监控器
        
        Args:
            name: 监控器名称
        """
        super().__init__(name)
        self.crawlers = {
            'xhs': XHSCrawler(),
            'bilibili': BiliBiliCrawler()
        }
        
        # 添加默认告警规则
        self.add_alert_rule('high_failure_rate', {
            'metric': 'crawler.task.failure_rate',
            'operator': '>',
            'threshold': 0.3,
            'message': '爬虫任务失败率过高'
        })
        
        self.add_alert_rule('low_content_count', {
            'metric': 'crawler.content.count',
            'operator': '<',
            'threshold': 100,
            'message': '内容采集数量过低'
        })
        
        self.add_alert_rule('high_error_count', {
            'metric': 'crawler.error.count',
            'operator': '>',
            'threshold': 50,
            'message': '爬虫错误数量过多'
        })
        
        self.proxy_manager = ProxyManager()
        self.cookie_manager = CookieManager()
        self.alert_webhook = None  # 告警Webhook
        self.proxy_metrics = {
            "total": 0,
            "available": 0,
            "score_avg": 0
        }
        self.cookie_metrics = {
            "total": 0,
            "valid": 0,
            "score_avg": 0
        }
        self.content_metrics = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "retry": 0
        }
    
    async def collect_metrics(self) -> Dict[str, Any]:
        """收集监控指标
        
        Returns:
            Dict[str, Any]: 监控指标数据
        """
        try:
            # 更新代理指标
            self.proxy_metrics.update(await self._collect_proxy_metrics())
            
            # 更新Cookie指标
            self.cookie_metrics.update(await self._collect_cookie_metrics())
            
            # 更新内容指标
            self.content_metrics.update(await self._collect_content_metrics())
            
            # 返回所有指标
            return {
                "proxy": self.proxy_metrics,
                "cookie": self.cookie_metrics,
                "content": self.content_metrics,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"收集指标失败: {str(e)}")
            return {}
        
    async def _collect_proxy_metrics(self) -> Dict[str, Any]:
        """收集代理指标"""
        # 这里应该从代理管理器获取实际的指标
        return {
            "total": 100,
            "available": 80,
            "score_avg": 85
        }
        
    async def _collect_cookie_metrics(self) -> Dict[str, Any]:
        """收集Cookie指标"""
        # 这里应该从Cookie管理器获取实际的指标
        return {
            "total": 50,
            "valid": 40,
            "score_avg": 75
        }
        
    async def _collect_content_metrics(self) -> Dict[str, Any]:
        """收集内容指标"""
        # 这里应该从数据库获取实际的指标
        return {
            "total": 1000,
            "success": 950,
            "failed": 30,
            "retry": 20
        }
        
    async def check_alerts(self) -> List[Dict[str, Any]]:
        """检查告警
        
        Returns:
            List[Dict[str, Any]]: 告警列表
        """
        alerts = []
        
        # 检查代理状态
        if self.proxy_metrics["available"] < 5:
            alerts.append({
                "level": "warning",
                "type": "proxy",
                "message": f"可用代理数量不足: {self.proxy_metrics['available']}"
            })
            
        if self.proxy_metrics["score_avg"] < 60:
            alerts.append({
                "level": "warning",
                "type": "proxy",
                "message": f"代理平均分数过低: {self.proxy_metrics['score_avg']}"
            })
            
        # 检查Cookie状态
        if self.cookie_metrics["valid"] < 3:
            alerts.append({
                "level": "warning",
                "type": "cookie",
                "message": f"有效Cookie数量不足: {self.cookie_metrics['valid']}"
            })
            
        if self.cookie_metrics["score_avg"] < 60:
            alerts.append({
                "level": "warning",
                "type": "cookie",
                "message": f"Cookie平均分数过低: {self.cookie_metrics['score_avg']}"
            })
            
        # 检查内容采集状态
        if self.content_metrics["failed"] > 10:
            alerts.append({
                "level": "error",
                "type": "content",
                "message": f"内容采集失败次数过多: {self.content_metrics['failed']}"
            })
            
        if self.content_metrics["retry"] > 20:
            alerts.append({
                "level": "warning",
                "type": "content",
                "message": f"内容采集重试次数过多: {self.content_metrics['retry']}"
            })
            
        return alerts
        
    async def handle_alerts(self, alerts: List[Dict[str, Any]]) -> None:
        """处理告警
        
        Args:
            alerts: 告警列表
        """
        if not alerts:
            return
            
        try:
            # 记录告警日志
            for alert in alerts:
                self.logger.warning(
                    f"[{alert['level']}] {alert['type']}: {alert['message']}"
                )
                
            # 发送告警通知
            if self.alert_webhook:
                await self._send_alert_notification(alerts)
                
        except Exception as e:
            self.logger.error(f"处理告警失败: {str(e)}")
            
    async def export_metrics(self, metrics: Dict[str, Any]) -> None:
        """导出监控指标
        
        Args:
            metrics: 监控指标数据
        """
        try:
            # 这里可以将指标导出到时序数据库（如InfluxDB）
            # 或者其他监控系统
            pass
        except Exception as e:
            self.logger.error(f"导出指标失败: {str(e)}")
            
    async def _send_alert_notification(self, alerts: List[Dict[str, Any]]) -> None:
        """发送告警通知
        
        Args:
            alerts: 告警列表
        """
        if not self.alert_webhook:
            return
            
        try:
            async with aiohttp.ClientSession() as session:
                for alert in alerts:
                    payload = {
                        "level": alert["level"],
                        "type": alert["type"],
                        "message": alert["message"],
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    async with session.post(self.alert_webhook, json=payload) as resp:
                        if resp.status != 200:
                            self.logger.error(
                                f"发送告警通知失败: {resp.status} {await resp.text()}"
                            )
        except Exception as e:
            self.logger.error(f"发送告警通知失败: {str(e)}")
            
    async def collect_metrics(self):
        """收集监控指标"""
        try:
            # 获取系统指标
            system_metrics = self.get_system_metrics()
            
            # 获取最近24小时的数据
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)
            
            # 获取内容统计
            content_stats = await self._get_content_stats(start_time, end_time)
            for metric, value in content_stats.items():
                self.add_metric(f'crawler.content.{metric}', value)
            
            # 获取任务统计
            task_stats = await self._get_task_stats(start_time, end_time)
            for metric, value in task_stats.items():
                self.add_metric(f'crawler.task.{metric}', value)
            
            # 获取错误统计
            error_stats = await self._get_error_stats(start_time, end_time)
            for metric, value in error_stats.items():
                self.add_metric(f'crawler.error.{metric}', value)
            
            # 检查告警规则
            self.check_alert_rules()
            
        except Exception as e:
            self.logger.error(f"Error collecting metrics: {str(e)}")
    
    async def _get_content_stats(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """获取内容统计"""
        try:
            # 获取各平台内容数量
            platform_counts = {}
            for platform in self.crawlers:
                count = await content_dao.count_by_platform_and_time_range(
                    platform=platform,
                    start_time=start_time,
                    end_time=end_time
                )
                platform_counts[platform] = count
            
            # 计算总数和平均值
            total_count = sum(platform_counts.values())
            avg_count = total_count / len(platform_counts) if platform_counts else 0
            
            return {
                'count': total_count,
                'average': avg_count,
                'by_platform': platform_counts
            }
            
        except Exception as e:
            self.logger.error(f"Error getting content stats: {str(e)}")
            return {}
    
    async def _get_task_stats(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """获取任务统计"""
        try:
            # 获取任务执行记录
            logs = await task_log_dao.get_logs_by_time_range(
                start_time=start_time,
                end_time=end_time
            )
            
            # 统计任务状态
            total_tasks = len(logs)
            status_counts = {}
            for log in logs:
                status = log.status
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # 计算失败率
            failed_count = status_counts.get('failed', 0)
            failure_rate = failed_count / total_tasks if total_tasks > 0 else 0
            
            return {
                'total': total_tasks,
                'success': status_counts.get('success', 0),
                'failed': failed_count,
                'running': status_counts.get('running', 0),
                'failure_rate': failure_rate
            }
            
        except Exception as e:
            self.logger.error(f"Error getting task stats: {str(e)}")
            return {}
    
    async def _get_error_stats(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """获取错误统计"""
        try:
            # 获取失败的任务记录
            failed_logs = await task_log_dao.get_failed_logs_by_time_range(
                start_time=start_time,
                end_time=end_time
            )
            
            # 统计错误类型
            error_counts = {}
            for log in failed_logs:
                error_type = self._categorize_error(log.error_message)
                error_counts[error_type] = error_counts.get(error_type, 0) + 1
            
            return {
                'count': len(failed_logs),
                'by_type': error_counts
            }
            
        except Exception as e:
            self.logger.error(f"Error getting error stats: {str(e)}")
            return {}
    
    def _categorize_error(self, error_message: str) -> str:
        """对错误进行分类"""
        if not error_message:
            return 'unknown'
            
        error_message = error_message.lower()
        
        if 'timeout' in error_message:
            return 'timeout'
        elif 'connection' in error_message:
            return 'connection'
        elif 'proxy' in error_message:
            return 'proxy'
        elif 'cookie' in error_message:
            return 'cookie'
        elif 'parse' in error_message:
            return 'parse'
        elif 'api' in error_message:
            return 'api'
        else:
            return 'other'
    
    async def check_health(self) -> bool:
        """检查健康状态"""
        try:
            # 检查系统资源
            system_metrics = self.get_system_metrics()
            if system_metrics.get('cpu', {}).get('usage', 0) > 90:
                return False
            if system_metrics.get('memory', {}).get('percent', 0) > 90:
                return False
            if system_metrics.get('disk', {}).get('percent', 0) > 90:
                return False
            
            # 检查任务状态
            task_stats = await self._get_task_stats(
                start_time=datetime.now() - timedelta(hours=1),
                end_time=datetime.now()
            )
            if task_stats.get('failure_rate', 0) > 0.5:
                return False
            
            # 检查错误数量
            error_stats = await self._get_error_stats(
                start_time=datetime.now() - timedelta(hours=1),
                end_time=datetime.now()
            )
            if error_stats.get('count', 0) > 100:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking health: {str(e)}")
            return False
    
    def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态详情"""
        return {
            'system': self.get_system_metrics(),
            'alerts': self.get_alerts(limit=10),
            'metrics': self.metrics
        } 