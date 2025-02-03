"""告警聚合器模块

该模块负责对告警进行聚合，以减少告警数量，避免告警风暴。
主要功能：
1. 相同规则的告警聚合
2. 相关规则的告警关联
3. 告警计数和统计
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from collections import defaultdict

from .alert_rule import AlertStatus, AlertSeverity
from .alert_engine import Alert

logger = logging.getLogger(__name__)

class AlertAggregator:
    """告警聚合器"""
    
    def __init__(
        self,
        window_size: int = 300,  # 聚合窗口大小（秒）
        max_alerts: int = 10,    # 最大告警数
        min_interval: int = 60   # 最小告警间隔（秒）
    ):
        self.window_size = window_size
        self.max_alerts = max_alerts
        self.min_interval = min_interval
        
        # 告警聚合状态
        self.alert_groups: Dict[str, List[Alert]] = defaultdict(list)
        self.alert_counts: Dict[str, int] = defaultdict(int)
        self.last_alert_time: Dict[str, datetime] = {}
    
    def should_alert(self, alert: Alert) -> bool:
        """检查是否应该发送告警"""
        now = datetime.now()
        rule_name = alert.rule.name
        
        # 检查最小间隔
        if rule_name in self.last_alert_time:
            time_since_last = (now - self.last_alert_time[rule_name]).total_seconds()
            if time_since_last < self.min_interval:
                return False
        
        # 检查最大告警数
        if self.alert_counts[rule_name] >= self.max_alerts:
            return False
        
        return True
    
    def add_alert(self, alert: Alert) -> Optional[Alert]:
        """添加告警并返回聚合后的告警"""
        now = datetime.now()
        rule_name = alert.rule.name
        
        # 清理过期告警
        self._clean_old_alerts(now)
        
        # 检查是否应该发送告警
        if not self.should_alert(alert):
            return None
        
        # 更新计数和时间
        self.alert_counts[rule_name] += 1
        self.last_alert_time[rule_name] = now
        
        # 添加到告警组
        group = self.alert_groups[rule_name]
        group.append(alert)
        
        # 如果是第一个告警，直接返回
        if len(group) == 1:
            return alert
        
        # 创建聚合告警
        return self._create_aggregated_alert(rule_name, group)
    
    def _clean_old_alerts(self, now: datetime):
        """清理过期告警"""
        cutoff = now - timedelta(seconds=self.window_size)
        
        for rule_name, alerts in list(self.alert_groups.items()):
            # 移除过期告警
            valid_alerts = [
                alert for alert in alerts
                if alert.timestamp >= cutoff
            ]
            
            if valid_alerts:
                self.alert_groups[rule_name] = valid_alerts
                self.alert_counts[rule_name] = len(valid_alerts)
            else:
                # 如果没有有效告警，清理相关状态
                del self.alert_groups[rule_name]
                del self.alert_counts[rule_name]
                self.last_alert_time.pop(rule_name, None)
    
    def _create_aggregated_alert(self, rule_name: str, alerts: List[Alert]) -> Alert:
        """创建聚合告警"""
        # 使用最新的告警作为基础
        latest_alert = alerts[-1]
        
        # 更新描述，包含聚合信息
        description = (
            f"{latest_alert.rule.description}\n"
            f"最近{self.window_size}秒内有{len(alerts)}条相关告警"
        )
        
        # 创建聚合告警
        aggregated = Alert(
            rule=latest_alert.rule,
            value=latest_alert.value,
            timestamp=latest_alert.timestamp,
            status=latest_alert.status
        )
        aggregated.rule.description = description
        
        return aggregated
    
    def get_active_groups(self) -> Dict[str, List[Alert]]:
        """获取活动的告警组"""
        now = datetime.now()
        self._clean_old_alerts(now)
        return dict(self.alert_groups)
    
    def get_group_stats(self) -> Dict[str, Dict]:
        """获取告警组统计信息"""
        stats = {}
        now = datetime.now()
        self._clean_old_alerts(now)
        
        for rule_name, alerts in self.alert_groups.items():
            if not alerts:
                continue
                
            # 计算告警频率
            first_alert = alerts[0]
            last_alert = alerts[-1]
            duration = (last_alert.timestamp - first_alert.timestamp).total_seconds()
            frequency = len(alerts) / duration if duration > 0 else 0
            
            stats[rule_name] = {
                'count': len(alerts),
                'first_time': first_alert.timestamp,
                'last_time': last_alert.timestamp,
                'frequency': frequency,
                'severity': alerts[0].rule.severity
            }
        
        return stats
    
    def reset(self):
        """重置聚合器状态"""
        self.alert_groups.clear()
        self.alert_counts.clear()
        self.last_alert_time.clear() 