from typing import Dict, List, Any, Optional, Callable
import json
import logging
from datetime import datetime, timedelta
from .metrics_collector import MetricsCollector

class AlertOperator:
    """告警操作符"""
    GT = ">"  # 大于
    LT = "<"  # 小于
    GE = ">="  # 大于等于
    LE = "<="  # 小于等于
    EQ = "=="  # 等于
    NE = "!="  # 不等于

class AlertSeverity:
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertRuleGroup:
    """告警规则组"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.rules: List[AlertRule] = []
        self.enabled = True
    
    def add_rule(self, rule: 'AlertRule'):
        """添加规则"""
        self.rules.append(rule)
    
    def remove_rule(self, rule_name: str):
        """移除规则"""
        self.rules = [r for r in self.rules if r.name != rule_name]
    
    def enable(self):
        """启用规则组"""
        self.enabled = True
        for rule in self.rules:
            rule.enabled = True
    
    def disable(self):
        """禁用规则组"""
        self.enabled = False
        for rule in self.rules:
            rule.enabled = False

class AlertRule:
    """告警规则"""
    
    def __init__(
        self,
        name: str,
        metric: str,
        operator: str,
        threshold: float,
        severity: str = AlertSeverity.WARNING,
        description: str = "",
        interval: int = 300,
        enabled: bool = True,
        group: Optional[AlertRuleGroup] = None,
        conditions: List[Dict] = None,
        template: str = None,
        recovery_threshold: Optional[float] = None,
        recovery_window: int = 300,
        aggregation: str = "last",
        aggregation_window: int = 300
    ):
        self.name = name  # 规则名称
        self.metric = metric  # 指标名称
        self.operator = operator  # 操作符
        self.threshold = threshold  # 阈值
        self.severity = severity  # 严重程度
        self.description = description  # 规则描述
        self.interval = interval  # 检查间隔(秒)
        self.enabled = enabled  # 是否启用
        self.group = group  # 所属规则组
        self.conditions = conditions or []  # 复合条件
        self.template = template  # 自定义模板
        self.recovery_threshold = recovery_threshold  # 恢复阈值
        self.recovery_window = recovery_window  # 恢复窗口(秒)
        self.aggregation = aggregation  # 聚合方式: last, avg, max, min
        self.aggregation_window = aggregation_window  # 聚合窗口(秒)
        self.last_check_time = datetime.min  # 上次检查时间
        self.last_alert_time = datetime.min  # 上次告警时间
        self.alert_count = 0  # 告警次数
        self.status = "normal"  # 状态: normal, alerting, recovered
        self._history: List[Dict] = []  # 历史记录
    
    def check_value(self, value: float) -> bool:
        """检查值是否触发告警"""
        if self.operator == AlertOperator.GT:
            return value > self.threshold
        elif self.operator == AlertOperator.LT:
            return value < self.threshold
        elif self.operator == AlertOperator.GE:
            return value >= self.threshold
        elif self.operator == AlertOperator.LE:
            return value <= self.threshold
        elif self.operator == AlertOperator.EQ:
            return value == self.threshold
        elif self.operator == AlertOperator.NE:
            return value != self.threshold
        return False
    
    def check_recovery(self, value: float) -> bool:
        """检查是否恢复正常"""
        if not self.recovery_threshold:
            return not self.check_value(value)
        
        if self.operator in [AlertOperator.GT, AlertOperator.GE]:
            return value <= self.recovery_threshold
        elif self.operator in [AlertOperator.LT, AlertOperator.LE]:
            return value >= self.recovery_threshold
        else:
            return not self.check_value(value)
    
    def add_history(self, value: float, timestamp: datetime):
        """添加历史记录"""
        self._history.append({
            'value': value,
            'timestamp': timestamp
        })
        
        # 清理过期数据
        cutoff_time = timestamp - timedelta(seconds=max(
            self.aggregation_window,
            self.recovery_window
        ))
        self._history = [
            h for h in self._history
            if h['timestamp'] >= cutoff_time
        ]
    
    def get_aggregated_value(self, end_time: datetime) -> Optional[float]:
        """获取聚合值"""
        start_time = end_time - timedelta(seconds=self.aggregation_window)
        values = [
            h['value'] for h in self._history
            if start_time <= h['timestamp'] <= end_time
        ]
        
        if not values:
            return None
        
        if self.aggregation == "last":
            return values[-1]
        elif self.aggregation == "avg":
            return sum(values) / len(values)
        elif self.aggregation == "max":
            return max(values)
        elif self.aggregation == "min":
            return min(values)
        else:
            return values[-1]
    
    def format_message(self, value: float) -> str:
        """格式化告警消息"""
        if self.template:
            return self.template.format(
                name=self.name,
                description=self.description,
                metric=self.metric,
                value=value,
                threshold=self.threshold,
                operator=self.operator,
                severity=self.severity,
                alert_count=self.alert_count
            )
        
        return f"""
告警名称: {self.name}
告警级别: {self.severity}
告警描述: {self.description}
指标名称: {self.metric}
当前值: {value}
阈值: {self.operator} {self.threshold}
告警次数: {self.alert_count}
"""

class Alert:
    """告警"""
    
    def __init__(
        self,
        rule: AlertRule,
        value: float,
        timestamp: datetime = None,
        status: str = "alerting"
    ):
        self.rule = rule  # 触发的规则
        self.value = value  # 触发值
        self.timestamp = timestamp or datetime.now()  # 触发时间
        self.status = status  # 状态: alerting, recovered
        self.message = rule.format_message(value)  # 告警消息

class AlertEngine:
    """告警引擎"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.logger = logging.getLogger('AlertEngine')
        self.metrics_collector = metrics_collector
        self.rules: Dict[str, AlertRule] = {}  # 规则字典
        self.rule_groups: Dict[str, AlertRuleGroup] = {}  # 规则组字典
        self.alerts: List[Alert] = []  # 告警列表
        self.handlers: Dict[str, List[Callable]] = {  # 处理器字典
            AlertSeverity.INFO: [],
            AlertSeverity.WARNING: [],
            AlertSeverity.ERROR: [],
            AlertSeverity.CRITICAL: []
        }
        self._init_default_rules()
    
    def _init_default_rules(self):
        """初始化默认规则"""
        # 系统资源规则组
        system_group = AlertRuleGroup(
            name="system",
            description="系统资源监控规则"
        )
        
        # CPU规则
        system_group.add_rule(AlertRule(
            name="high_cpu_usage",
            metric="system.cpu.usage",
            operator=AlertOperator.GT,
            threshold=80,
            severity=AlertSeverity.WARNING,
            description="CPU使用率超过80%",
            recovery_threshold=70,
            template="""
【警告】CPU使用率过高
当前使用率: {value}%
阈值: {threshold}%
持续时间: {duration}
"""
        ))
        
        system_group.add_rule(AlertRule(
            name="critical_cpu_usage",
            metric="system.cpu.usage",
            operator=AlertOperator.GT,
            threshold=90,
            severity=AlertSeverity.CRITICAL,
            description="CPU使用率超过90%",
            recovery_threshold=80
        ))
        
        # 内存规则
        system_group.add_rule(AlertRule(
            name="high_memory_usage",
            metric="system.memory.percent",
            operator=AlertOperator.GT,
            threshold=80,
            severity=AlertSeverity.WARNING,
            description="内存使用率超过80%",
            recovery_threshold=70
        ))
        
        system_group.add_rule(AlertRule(
            name="critical_memory_usage",
            metric="system.memory.percent",
            operator=AlertOperator.GT,
            threshold=90,
            severity=AlertSeverity.CRITICAL,
            description="内存使用率超过90%",
            recovery_threshold=80
        ))
        
        # 磁盘规则
        system_group.add_rule(AlertRule(
            name="high_disk_usage",
            metric="system.disk.percent",
            operator=AlertOperator.GT,
            threshold=80,
            severity=AlertSeverity.WARNING,
            description="磁盘使用率超过80%",
            recovery_threshold=70
        ))
        
        system_group.add_rule(AlertRule(
            name="critical_disk_usage",
            metric="system.disk.percent",
            operator=AlertOperator.GT,
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
                operator=AlertOperator.LT,
                threshold=10,
                severity=AlertSeverity.WARNING,
                description=f"{platform}爬取速率低于10条/小时",
                recovery_threshold=15,
                conditions=[{
                    "metric": "task.running",
                    "operator": AlertOperator.GT,
                    "threshold": 0
                }]
            ))
            
            crawler_group.add_rule(AlertRule(
                name=f"very_low_{platform}_crawl_rate",
                metric=f"crawler.{platform}.content.rate",
                operator=AlertOperator.LT,
                threshold=5,
                severity=AlertSeverity.ERROR,
                description=f"{platform}爬取速率低于5条/小时",
                recovery_threshold=10,
                conditions=[{
                    "metric": "task.running",
                    "operator": AlertOperator.GT,
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
            operator=AlertOperator.LT,
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
            operator=AlertOperator.LT,
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
            operator=AlertOperator.GT,
            threshold=100,
            severity=AlertSeverity.WARNING,
            description="待处理任务数超过100",
            recovery_threshold=80
        ))
        
        task_group.add_rule(AlertRule(
            name="very_high_pending_tasks",
            metric="task.pending",
            operator=AlertOperator.GT,
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
            operator=AlertOperator.GT,
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
            operator=AlertOperator.GT,
            threshold=20,
            severity=AlertSeverity.ERROR,
            description="错误率超过20%",
            recovery_threshold=15,
            aggregation="avg",
            aggregation_window=900
        ))
        
        self.add_rule_group(error_group)
    
    def add_rule_group(self, group: AlertRuleGroup):
        """添加规则组"""
        self.rule_groups[group.name] = group
        for rule in group.rules:
            rule.group = group
            self.rules[rule.name] = rule
    
    def remove_rule_group(self, group_name: str):
        """移除规则组"""
        if group_name in self.rule_groups:
            group = self.rule_groups[group_name]
            for rule in group.rules:
                self.rules.pop(rule.name, None)
            del self.rule_groups[group_name]
    
    def get_rule_group(self, group_name: str) -> Optional[AlertRuleGroup]:
        """获取规则组"""
        return self.rule_groups.get(group_name)
    
    def add_rule(self, rule: AlertRule):
        """添加规则"""
        self.rules[rule.name] = rule
    
    def remove_rule(self, rule_name: str):
        """移除规则"""
        if rule_name in self.rules:
            rule = self.rules[rule_name]
            if rule.group:
                rule.group.remove_rule(rule_name)
            del self.rules[rule_name]
    
    def get_rule(self, rule_name: str) -> Optional[AlertRule]:
        """获取规则"""
        return self.rules.get(rule_name)
    
    def enable_rule(self, rule_name: str):
        """启用规则"""
        if rule_name in self.rules:
            self.rules[rule_name].enabled = True
    
    def disable_rule(self, rule_name: str):
        """禁用规则"""
        if rule_name in self.rules:
            self.rules[rule_name].enabled = False
    
    def enable_rule_group(self, group_name: str):
        """启用规则组"""
        if group_name in self.rule_groups:
            self.rule_groups[group_name].enable()
    
    def disable_rule_group(self, group_name: str):
        """禁用规则组"""
        if group_name in self.rule_groups:
            self.rule_groups[group_name].disable()
    
    def add_handler(self, severity: str, handler: Callable):
        """添加告警处理器"""
        if severity in self.handlers:
            self.handlers[severity].append(handler)
    
    def remove_handler(self, severity: str, handler: Callable):
        """移除告警处理器"""
        if severity in self.handlers:
            self.handlers[severity].remove(handler)
    
    def check_rule(self, rule: AlertRule, metrics: Dict[str, Any]) -> Optional[Alert]:
        """检查单个规则"""
        try:
            # 检查规则是否启用
            if not rule.enabled:
                return None
            
            # 检查规则组是否启用
            if rule.group and not rule.group.enabled:
                return None
            
            # 检查是否到达检查间隔
            now = datetime.now()
            if (rule.last_check_time and 
                (now - rule.last_check_time).total_seconds() < rule.interval):
                return None
            
            # 获取指标值
            metric = metrics.get(rule.metric)
            if not metric:
                return None
            
            # 添加历史记录
            rule.add_history(metric.value, now)
            
            # 获取聚合值
            value = rule.get_aggregated_value(now)
            if value is None:
                return None
            
            # 检查复合条件
            if rule.conditions:
                for condition in rule.conditions:
                    condition_metric = metrics.get(condition["metric"])
                    if not condition_metric:
                        continue
                    
                    condition_rule = AlertRule(
                        name="condition",
                        metric=condition["metric"],
                        operator=condition["operator"],
                        threshold=condition["threshold"],
                        severity=rule.severity
                    )
                    
                    if not condition_rule.check_value(condition_metric.value):
                        return None
            
            # 检查是否触发告警
            if rule.check_value(value):
                if rule.status == "normal":
                    rule.status = "alerting"
                    rule.alert_count += 1
                    alert = Alert(rule, value, now, "alerting")
                    self._handle_alert(alert)
                    return alert
            # 检查是否恢复
            elif rule.status == "alerting" and rule.check_recovery(value):
                rule.status = "recovered"
                alert = Alert(rule, value, now, "recovered")
                self._handle_alert(alert)
                return alert
            
            rule.last_check_time = now
            return None
            
        except Exception as e:
            self.logger.error(f"Error checking rule {rule.name}: {str(e)}")
            return None
    
    def check_rules(self, metrics: Dict[str, Any]) -> List[Alert]:
        """检查所有规则"""
        alerts = []
        for rule in self.rules.values():
            alert = self.check_rule(rule, metrics)
            if alert:
                alerts.append(alert)
        return alerts
    
    def _handle_alert(self, alert: Alert):
        """处理告警"""
        self.alerts.append(alert)
        
        # 调用对应级别的处理器
        for handler in self.handlers.get(alert.rule.severity, []):
            try:
                handler(alert)
            except Exception as e:
                self.logger.error(f"Error handling alert: {str(e)}")
    
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
        return self.get_alerts(status="alerting")
    
    def get_recent_alerts(self, hours: int = 24, limit: Optional[int] = None) -> List[Alert]:
        """获取最近告警"""
        start_time = datetime.now() - timedelta(hours=hours)
        return self.get_alerts(start_time=start_time, limit=limit)
    
    def clear_alerts(self):
        """清除所有告警"""
        self.alerts.clear()
    
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
    
    def import_rules(self, file_path: str):
        """导入规则配置"""
        with open(file_path, 'r', encoding='utf-8') as f:
            rules_data = json.load(f)
        
        for group_data in rules_data:
            group = AlertRuleGroup(
                name=group_data["name"],
                description=group_data["description"]
            )
            group.enabled = group_data["enabled"]
            
            for rule_data in group_data["rules"]:
                rule = AlertRule(
                    name=rule_data["name"],
                    metric=rule_data["metric"],
                    operator=rule_data["operator"],
                    threshold=rule_data["threshold"],
                    severity=rule_data["severity"],
                    description=rule_data["description"],
                    interval=rule_data["interval"],
                    enabled=rule_data["enabled"],
                    conditions=rule_data["conditions"],
                    template=rule_data["template"],
                    recovery_threshold=rule_data["recovery_threshold"],
                    recovery_window=rule_data["recovery_window"],
                    aggregation=rule_data["aggregation"],
                    aggregation_window=rule_data["aggregation_window"]
                )
                group.add_rule(rule)
            
            self.add_rule_group(group) 