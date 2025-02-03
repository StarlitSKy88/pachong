"""告警引擎模块

该模块负责告警的处理和管理，包括：
1. 告警规则管理
2. 告警检查和触发
3. 告警通知分发
4. 告警状态管理
5. 告警历史记录
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
import json
from collections import defaultdict

from .alert_rule import AlertRule, AlertRuleGroup, AlertStatus, AlertSeverity
from .metrics_collector import MetricsCollector
from .alert_notifier import AlertNotifier
from .alert_aggregator import AlertAggregator

logger = logging.getLogger(__name__)

class Alert:
    """告警实例"""
    
    def __init__(
        self,
        rule: AlertRule,
        value: float,
        timestamp: datetime = None,
        status: str = AlertStatus.ALERTING
    ):
        self.rule = rule
        self.value = value
        self.timestamp = timestamp or datetime.now()
        self.status = status
        self.message = rule.format_message(value)
        self.handled = False
        self.handle_time: Optional[datetime] = None
        self.handler: Optional[str] = None
        self.comment: Optional[str] = None

class AlertEngine:
    """告警引擎"""
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        notifier: Optional[AlertNotifier] = None,
        aggregator: Optional[AlertAggregator] = None
    ):
        self.logger = logging.getLogger('AlertEngine')
        self.metrics_collector = metrics_collector
        self.notifier = notifier
        self.aggregator = aggregator or AlertAggregator()
        
        # 规则管理
        self.rules: Dict[str, AlertRule] = {}
        self.rule_groups: Dict[str, AlertRuleGroup] = {}
        
        # 告警管理
        self.alerts: List[Alert] = []
        self.active_alerts: Dict[str, Alert] = {}
        
        # 处理器管理
        self.handlers: Dict[str, List[Callable]] = defaultdict(list)
        
        # 初始化默认规则
        self._init_default_rules()
    
    def _init_default_rules(self):
        """初始化默认规则"""
        # 系统监控规则组
        system_group = AlertRuleGroup(
            name="system",
            description="系统资源监控规则"
        )
        
        # CPU规则
        system_group.add_rule(AlertRule(
            name="high_cpu_usage",
            metric="system.cpu.usage",
            operator=">",
            threshold=80,
            severity=AlertSeverity.WARNING,
            description="CPU使用率超过80%",
            recovery_threshold=70
        ))
        
        system_group.add_rule(AlertRule(
            name="critical_cpu_usage",
            metric="system.cpu.usage",
            operator=">",
            threshold=90,
            severity=AlertSeverity.CRITICAL,
            description="CPU使用率超过90%",
            recovery_threshold=80
        ))
        
        # 内存规则
        system_group.add_rule(AlertRule(
            name="high_memory_usage",
            metric="system.memory.percent",
            operator=">",
            threshold=80,
            severity=AlertSeverity.WARNING,
            description="内存使用率超过80%",
            recovery_threshold=70
        ))
        
        system_group.add_rule(AlertRule(
            name="critical_memory_usage",
            metric="system.memory.percent",
            operator=">",
            threshold=90,
            severity=AlertSeverity.CRITICAL,
            description="内存使用率超过90%",
            recovery_threshold=80
        ))
        
        # 磁盘规则
        system_group.add_rule(AlertRule(
            name="high_disk_usage",
            metric="system.disk.percent",
            operator=">",
            threshold=80,
            severity=AlertSeverity.WARNING,
            description="磁盘使用率超过80%",
            recovery_threshold=70
        ))
        
        system_group.add_rule(AlertRule(
            name="critical_disk_usage",
            metric="system.disk.percent",
            operator=">",
            threshold=90,
            severity=AlertSeverity.CRITICAL,
            description="磁盘使用率超过90%",
            recovery_threshold=80
        ))
        
        self.add_rule_group(system_group)
        
        # 爬虫性能规则组
        crawler_group = AlertRuleGroup(
            name="crawler",
            description="爬虫性能监控规则"
        )
        
        # 爬取速率规则
        for platform in ['xhs', 'bilibili']:
            crawler_group.add_rule(AlertRule(
                name=f"low_{platform}_crawl_rate",
                metric=f"crawler.{platform}.content.rate",
                operator="<",
                threshold=10,
                severity=AlertSeverity.WARNING,
                description=f"{platform}爬取速率低于10条/小时",
                recovery_threshold=15,
                conditions=[{
                    "metric": "task.running",
                    "operator": ">",
                    "threshold": 0
                }]
            ))
            
            crawler_group.add_rule(AlertRule(
                name=f"very_low_{platform}_crawl_rate",
                metric=f"crawler.{platform}.content.rate",
                operator="<",
                threshold=5,
                severity=AlertSeverity.ERROR,
                description=f"{platform}爬取速率低于5条/小时",
                recovery_threshold=10,
                conditions=[{
                    "metric": "task.running",
                    "operator": ">",
                    "threshold": 0
                }]
            ))
        
        self.add_rule_group(crawler_group)
        
        # 任务状态规则组
        task_group = AlertRuleGroup(
            name="task",
            description="任务状态监控规则"
        )
        
        # 任务成功率规则
        task_group.add_rule(AlertRule(
            name="low_task_success_rate",
            metric="task.success_rate",
            operator="<",
            threshold=80,
            severity=AlertSeverity.WARNING,
            description="任务成功率低于80%",
            recovery_threshold=85,
            aggregation="avg",
            aggregation_window=1800
        ))
        
        task_group.add_rule(AlertRule(
            name="very_low_task_success_rate",
            metric="task.success_rate",
            operator="<",
            threshold=60,
            severity=AlertSeverity.ERROR,
            description="任务成功率低于60%",
            recovery_threshold=70,
            aggregation="avg",
            aggregation_window=1800
        ))
        
        # 任务积压规则
        task_group.add_rule(AlertRule(
            name="high_pending_tasks",
            metric="task.pending",
            operator=">",
            threshold=100,
            severity=AlertSeverity.WARNING,
            description="待处理任务数超过100",
            recovery_threshold=80
        ))
        
        task_group.add_rule(AlertRule(
            name="very_high_pending_tasks",
            metric="task.pending",
            operator=">",
            threshold=200,
            severity=AlertSeverity.ERROR,
            description="待处理任务数超过200",
            recovery_threshold=150
        ))
        
        self.add_rule_group(task_group)
        
        # 错误监控规则组
        error_group = AlertRuleGroup(
            name="error",
            description="错误监控规则"
        )
        
        # 错误率规则
        error_group.add_rule(AlertRule(
            name="high_error_rate",
            metric="error.rate",
            operator=">",
            threshold=10,
            severity=AlertSeverity.WARNING,
            description="错误率超过10%",
            recovery_threshold=8,
            aggregation="avg",
            aggregation_window=900
        ))
        
        error_group.add_rule(AlertRule(
            name="very_high_error_rate",
            metric="error.rate",
            operator=">",
            threshold=20,
            severity=AlertSeverity.ERROR,
            description="错误率超过20%",
            recovery_threshold=15,
            aggregation="avg",
            aggregation_window=900
        ))
        
        self.add_rule_group(error_group)
    
    def add_rule(self, rule: AlertRule):
        """添加告警规则"""
        self.rules[rule.name] = rule
    
    def remove_rule(self, rule_name: str):
        """删除告警规则"""
        if rule_name in self.rules:
            rule = self.rules[rule_name]
            if rule.group:
                rule.group.remove_rule(rule_name)
            del self.rules[rule_name]
    
    def add_rule_group(self, group: AlertRuleGroup):
        """添加规则组"""
        self.rule_groups[group.name] = group
        for rule in group.rules:
            self.rules[rule.name] = rule
    
    def remove_rule_group(self, group_name: str):
        """删除规则组"""
        if group_name in self.rule_groups:
            group = self.rule_groups[group_name]
            for rule in group.rules:
                del self.rules[rule.name]
            del self.rule_groups[group_name]
    
    def add_handler(self, severity: str, handler: Callable):
        """添加告警处理器"""
        self.handlers[severity].append(handler)
    
    def remove_handler(self, severity: str, handler: Callable):
        """移除告警处理器"""
        if severity in self.handlers:
            self.handlers[severity].remove(handler)
    
    async def check_rule(self, rule: AlertRule, metrics: Dict[str, Any]) -> Optional[Alert]:
        """检查单个规则"""
        try:
            now = datetime.now()
            
            # 检查是否需要检查
            if (rule.last_check_time and 
                (now - rule.last_check_time).total_seconds() < rule.interval):
                return None
            
            # 获取指标值
            metric = metrics.get(rule.metric)
            if not metric:
                return None
            
            # 添加到历史记录
            rule.add_value(metric)
            
            # 获取聚合值
            value = rule.get_aggregated_value()
            if value is None:
                return None
            
            # 检查是否触发告警
            if rule.check_value(value):
                if rule.status == AlertStatus.NORMAL:
                    rule.status = AlertStatus.ALERTING
                    rule.alert_count += 1
                    alert = Alert(rule, value, now, AlertStatus.ALERTING)
                    
                    # 使用聚合器处理告警
                    aggregated_alert = self.aggregator.add_alert(alert)
                    if aggregated_alert:
                        await self._handle_alert(aggregated_alert)
                        return aggregated_alert
                    return None
                    
            # 检查是否恢复
            elif rule.status == AlertStatus.ALERTING and rule.check_recovery(value):
                rule.status = AlertStatus.RECOVERED
                alert = Alert(rule, value, now, AlertStatus.RECOVERED)
                await self._handle_alert(alert)
                return alert
            
            rule.last_check_time = now
            return None
            
        except Exception as e:
            self.logger.error(f"Error checking rule {rule.name}: {str(e)}")
            return None
    
    async def check_rules(self, metrics: Dict[str, Any]) -> List[Alert]:
        """检查所有规则"""
        alerts = []
        for rule in self.rules.values():
            alert = await self.check_rule(rule, metrics)
            if alert:
                alerts.append(alert)
        return alerts
    
    async def _handle_alert(self, alert: Alert):
        """处理告警"""
        self.alerts.append(alert)
        
        # 更新活动告警
        if alert.status == AlertStatus.ALERTING:
            self.active_alerts[alert.rule.name] = alert
        elif alert.status == AlertStatus.RECOVERED:
            self.active_alerts.pop(alert.rule.name, None)
        
        # 调用对应级别的处理器
        for handler in self.handlers.get(alert.rule.severity, []):
            try:
                await handler(alert)
            except Exception as e:
                self.logger.error(f"Error handling alert: {str(e)}")
        
        # 发送通知
        if self.notifier:
            try:
                await self.notifier.send_alert(alert)
            except Exception as e:
                self.logger.error(f"Error sending alert notification: {str(e)}")
    
    def get_alerts(
        self,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        group: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Alert]:
        """获取告警"""
        alerts = self.alerts
        
        if severity:
            alerts = [a for a in alerts if a.rule.severity == severity]
        
        if status:
            alerts = [a for a in alerts if a.status == status]
        
        if group:
            alerts = [a for a in alerts if a.rule.group and a.rule.group.name == group]
        
        if start_time:
            alerts = [a for a in alerts if a.timestamp >= start_time]
        
        if end_time:
            alerts = [a for a in alerts if a.timestamp <= end_time]
        
        alerts.sort(key=lambda x: x.timestamp, reverse=True)
        
        if limit:
            alerts = alerts[:limit]
        
        return alerts
    
    def get_active_alerts(self) -> List[Alert]:
        """获取活动告警"""
        return list(self.active_alerts.values())
    
    def get_recent_alerts(self, hours: int = 24, limit: Optional[int] = None) -> List[Alert]:
        """获取最近告警"""
        start_time = datetime.now() - timedelta(hours=hours)
        return self.get_alerts(start_time=start_time, limit=limit)
    
    def clear_alerts(self):
        """清除所有告警"""
        self.alerts.clear()
        self.active_alerts.clear()
    
    def clean_old_alerts(self, days: int = 7):
        """清理旧告警"""
        start_time = datetime.now() - timedelta(days=days)
        self.alerts = [a for a in self.alerts if a.timestamp >= start_time]
    
    def export_rules(self, file_path: str):
        """导出规则配置"""
        rules_data = []
        for group in self.rule_groups.values():
            group_data = {
                "name": group.name,
                "description": group.description,
                "enabled": group.enabled,
                "rules": []
            }
            
            for rule in group.rules:
                rule_data = {
                    "name": rule.name,
                    "metric": rule.metric,
                    "operator": rule.operator,
                    "threshold": rule.threshold,
                    "severity": rule.severity,
                    "description": rule.description,
                    "interval": rule.interval,
                    "enabled": rule.enabled,
                    "conditions": rule.conditions,
                    "template": rule.template,
                    "recovery_threshold": rule.recovery_threshold,
                    "recovery_window": rule.recovery_window,
                    "aggregation": rule.aggregation,
                    "aggregation_window": rule.aggregation_window
                }
                group_data["rules"].append(rule_data)
            
            rules_data.append(group_data)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(rules_data, f, ensure_ascii=False, indent=2)
    
    def get_aggregation_stats(self) -> Dict[str, Dict]:
        """获取告警聚合统计信息"""
        return self.aggregator.get_group_stats()
    
    def reset(self):
        """重置引擎状态"""
        self.alerts.clear()
        self.active_alerts.clear()
        self.aggregator.reset()
        
        for rule in self.rules.values():
            rule.reset() 