"""业务监控器"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
from collections import defaultdict

from .base_monitor import BaseMonitor, Metric, Alert
from ..database.base_storage import BaseStorage

class BusinessMonitor(BaseMonitor):
    """业务监控器"""
    
    def __init__(self, storage: BaseStorage):
        """初始化
        
        Args:
            storage: 数据存储
        """
        super().__init__()
        self.storage = storage
        self.collect_interval = 300  # 5分钟采集一次
        
        # 业务指标
        self.metrics_config = {
            'total_count': {
                'name': '总数据量',
                'query': {}
            },
            'today_count': {
                'name': '今日数据量',
                'query': {
                    'created_at': {
                        '$gte': datetime.now().replace(
                            hour=0, minute=0, second=0, microsecond=0
                        )
                    }
                }
            },
            'source_count': {
                'name': '来源分布',
                'group_by': 'source'
            }
        }
        
        # 告警规则
        self.alert_rules = {
            'low_daily_count': {
                'name': '日采集量过低',
                'metric': 'today_count',
                'condition': lambda x: x < 1000,
                'level': 'warning',
                'message': '今日采集数据量低于1000条'
            },
            'source_anomaly': {
                'name': '来源异常',
                'metric': 'source_count',
                'condition': lambda x: any(v == 0 for v in x.values()),
                'level': 'error',
                'message': '存在无数据来源'
            }
        }
        
    async def _collect(self) -> List[Metric]:
        """采集业务指标"""
        metrics = []
        
        try:
            # 采集总数据量
            total_count = await self.storage.count()
            metrics.append(Metric('total_count', total_count))
            
            # 采集今日数据量
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_count = await self.storage.count({
                'created_at': {'$gte': today}
            })
            metrics.append(Metric('today_count', today_count))
            
            # 采集来源分布
            sources = await self.storage.distinct('source')
            source_counts = {}
            for source in sources:
                count = await self.storage.count({'source': source})
                source_counts[source] = count
            metrics.append(Metric('source_count', source_counts))
            
            # 采集更新时间分布
            update_times = defaultdict(int)
            items = await self.storage.list(
                sort=[('updated_at', 'DESC')],
                limit=1000
            )
            for item in items:
                hour = item['updated_at'].hour
                update_times[hour] += 1
            metrics.append(Metric('update_time_dist', dict(update_times)))
            
            # 采集版本分布
            versions = defaultdict(int)
            for item in items:
                version = item.get('version', 1)
                versions[version] += 1
            metrics.append(Metric('version_dist', dict(versions)))
            
            # 添加标签
            for metric in metrics:
                metric.add_tag('type', 'business')
                
        except Exception as e:
            self.logger.error(f"采集业务指标失败: {str(e)}")
            
        return metrics
        
    async def _check_alerts(self) -> List[Alert]:
        """检查业务告警"""
        alerts = []
        
        try:
            # 获取最新指标
            metrics = {
                m.name: m.value 
                for m in self.get_metrics()
                if m.timestamp > datetime.now() - timedelta(minutes=10)
            }
            
            # 检查告警规则
            for rule_id, rule in self.alert_rules.items():
                try:
                    metric_value = metrics.get(rule['metric'])
                    if metric_value is None:
                        continue
                        
                    if rule['condition'](metric_value):
                        alerts.append(Alert(
                            rule['name'],
                            rule['message'],
                            rule['level']
                        ))
                except Exception as e:
                    self.logger.error(f"检查告警规则失败: {rule_id}, {str(e)}")
                    
            # 添加标签
            for alert in alerts:
                alert.add_tag('type', 'business')
                
        except Exception as e:
            self.logger.error(f"检查业务告警失败: {str(e)}")
            
        return alerts
        
    def add_metric(self, name: str, config: Dict[str, Any]):
        """添加业务指标
        
        Args:
            name: 指标名称
            config: 指标配置
        """
        self.metrics_config[name] = config
        
    def add_alert_rule(self, rule_id: str, rule: Dict[str, Any]):
        """添加告警规则
        
        Args:
            rule_id: 规则ID
            rule: 规则配置
        """
        self.alert_rules[rule_id] = rule
        
    def remove_alert_rule(self, rule_id: str):
        """删除告警规则
        
        Args:
            rule_id: 规则ID
        """
        if rule_id in self.alert_rules:
            del self.alert_rules[rule_id]
            
    async def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            # 获取最新指标
            metrics = {
                m.name: m.value 
                for m in self.get_metrics()
                if m.timestamp > datetime.now() - timedelta(minutes=10)
            }
            
            # 计算统计信息
            return {
                'total_count': metrics.get('total_count', 0),
                'today_count': metrics.get('today_count', 0),
                'source_distribution': metrics.get('source_count', {}),
                'update_time_distribution': metrics.get('update_time_dist', {}),
                'version_distribution': metrics.get('version_dist', {}),
                'alert_count': len(self.get_alerts()),
                'last_update': datetime.now()
            }
        except Exception as e:
            self.logger.error(f"获取统计信息失败: {str(e)}")
            return {} 