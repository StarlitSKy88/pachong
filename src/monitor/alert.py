from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum
import json
import logging
from notifier import EmailNotifier

class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertOperator(str, Enum):
    GT = ">"  # 大于
    LT = "<"  # 小于
    GE = ">="  # 大于等于
    LE = "<="  # 小于等于
    EQ = "=="  # 等于
    NE = "!="  # 不等于

class AlertRule:
    def __init__(
        self,
        name: str,
        metric: str,
        operator: AlertOperator,
        threshold: float,
        severity: AlertSeverity,
        description: str = "",
        interval: int = 300,  # 检查间隔（秒）
        enabled: bool = True,
        conditions: List[Dict] = None,  # 复合条件
        message_template: str = None  # 自定义消息模板
    ):
        self.name = name
        self.metric = metric
        self.operator = operator
        self.threshold = threshold
        self.severity = severity
        self.description = description
        self.interval = interval
        self.enabled = enabled
        self.conditions = conditions or []
        self.message_template = message_template or "{description}: {metric} = {value}"
        self.last_check_time = None
        
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
    
    def check_conditions(self, metrics: Dict[str, Any]) -> bool:
        """检查复合条件"""
        if not self.conditions:
            return True
            
        for condition in self.conditions:
            metric_value = metrics.get(condition["metric"])
            if not metric_value:
                continue
                
            rule = AlertRule(
                name="condition",
                metric=condition["metric"],
                operator=condition["operator"],
                threshold=condition["threshold"],
                severity=self.severity
            )
            
            if not rule.check_value(metric_value.value):
                return False
        
        return True
    
    def format_message(self, value: float) -> str:
        """格式化告警消息"""
        return self.message_template.format(
            name=self.name,
            description=self.description,
            metric=self.metric,
            value=value,
            threshold=self.threshold,
            operator=self.operator
        )

class Alert:
    def __init__(self, rule: AlertRule, value: float, timestamp: datetime = None):
        self.rule = rule
        self.value = value
        self.timestamp = timestamp or datetime.now()
        self.message = rule.format_message(value)

class AlertEngine:
    def __init__(self):
        self.rules: List[AlertRule] = []
        self.alerts: List[Alert] = []
        self.notifier = None
        self._load_default_rules()
        
    def _load_default_rules(self):
        """加载默认告警规则"""
        default_rules = [
            # 系统资源告警规则
            AlertRule(
                name="高CPU使用率",
                metric="system.cpu.usage",
                operator=AlertOperator.GT,
                threshold=80,
                severity=AlertSeverity.ERROR,
                description="CPU使用率超过80%",
                interval=300
            ),
            AlertRule(
                name="高内存使用率",
                metric="system.memory.percent",
                operator=AlertOperator.GT,
                threshold=80,
                severity=AlertSeverity.ERROR,
                description="内存使用率超过80%",
                interval=300
            ),
            AlertRule(
                name="高磁盘使用率",
                metric="system.disk.percent",
                operator=AlertOperator.GT,
                threshold=80,
                severity=AlertSeverity.ERROR,
                description="磁盘使用率超过80%",
                interval=300
            ),
            
            # 爬虫相关告警规则
            AlertRule(
                name="爬取速率过低",
                metric="crawler.xhs.content.rate",
                operator=AlertOperator.LT,
                threshold=5,
                severity=AlertSeverity.WARNING,
                description="小红书爬取速率低于5条/小时",
                interval=3600,
                conditions=[
                    {
                        "metric": "task.running",
                        "operator": AlertOperator.GT,
                        "threshold": 0
                    }
                ]
            ),
            AlertRule(
                name="爬取速率过低",
                metric="crawler.bilibili.content.rate",
                operator=AlertOperator.LT,
                threshold=5,
                severity=AlertSeverity.WARNING,
                description="B站爬取速率低于5条/小时",
                interval=3600,
                conditions=[
                    {
                        "metric": "task.running",
                        "operator": AlertOperator.GT,
                        "threshold": 0
                    }
                ]
            ),
            
            # 任务相关告警规则
            AlertRule(
                name="低任务成功率",
                metric="task.success_rate",
                operator=AlertOperator.LT,
                threshold=0.8,
                severity=AlertSeverity.ERROR,
                description="任务成功率低于80%",
                interval=1800
            ),
            AlertRule(
                name="任务积压",
                metric="task.running",
                operator=AlertOperator.GT,
                threshold=100,
                severity=AlertSeverity.WARNING,
                description="运行中任务数超过100",
                interval=600
            ),
            
            # 错误相关告警规则
            AlertRule(
                name="高错误率",
                metric="crawler.error.count",
                operator=AlertOperator.GT,
                threshold=50,
                severity=AlertSeverity.ERROR,
                description="错误数量超过50",
                interval=900
            )
        ]
        
        for rule in default_rules:
            self.add_rule(rule)
    
    def add_rule(self, rule: AlertRule):
        """添加告警规则"""
        self.rules.append(rule)
    
    def remove_rule(self, rule_name: str):
        """删除告警规则"""
        self.rules = [r for r in self.rules if r.name != rule_name]
    
    def enable_rule(self, rule_name: str):
        """启用告警规则"""
        for rule in self.rules:
            if rule.name == rule_name:
                rule.enabled = True
                break
    
    def disable_rule(self, rule_name: str):
        """禁用告警规则"""
        for rule in self.rules:
            if rule.name == rule_name:
                rule.enabled = False
                break
    
    def add_alert(self, alert: Alert):
        """添加告警"""
        self.alerts.append(alert)
    
    def setup_email_notifier(self, smtp_host: str, smtp_port: int, username: str, password: str, to_addr: str):
        """
        设置邮件通知器
        """
        self.notifier = EmailNotifier(smtp_host, smtp_port, username, password)
        self.to_addr = to_addr
    
    def check_rules(self, metrics: Dict[str, Any]) -> List[Alert]:
        """检查所有规则并生成告警"""
        current_time = datetime.now()
        new_alerts = []
        
        for rule in self.rules:
            if not rule.enabled:
                continue
                
            # 检查是否到达检查间隔
            if (rule.last_check_time and 
                (current_time - rule.last_check_time).total_seconds() < rule.interval):
                continue
            
            metric = metrics.get(rule.metric)
            if not metric:
                continue
            
            # 检查值和复合条件
            if (rule.check_value(metric.value) and 
                rule.check_conditions(metrics)):
                alert = Alert(rule, metric.value, current_time)
                self.add_alert(alert)
                new_alerts.append(alert)
            
            rule.last_check_time = current_time
        
        # 如果有新告警且配置了通知器，发送通知
        if new_alerts and self.notifier:
            alerts_data = [{
                'rule': alert.rule,
                'value': alert.value,
                'timestamp': alert.timestamp
            } for alert in new_alerts]
            self.notifier.send_alert(self.to_addr, alerts_data)
        
        return new_alerts
    
    def get_recent_alerts(self, hours: int = 24, limit: int = None) -> List[Alert]:
        """获取最近的告警"""
        start_time = datetime.now() - timedelta(hours=hours)
        recent_alerts = [
            alert for alert in self.alerts 
            if alert.timestamp >= start_time
        ]
        recent_alerts.sort(key=lambda x: x.timestamp, reverse=True)
        
        if limit:
            recent_alerts = recent_alerts[:limit]
        
        return recent_alerts
    
    def clean_old_alerts(self, days: int = 7):
        """清理旧告警"""
        start_time = datetime.now() - timedelta(days=days)
        self.alerts = [
            alert for alert in self.alerts 
            if alert.timestamp >= start_time
        ]
    
    def export_rules(self, file_path: str):
        """导出告警规则到文件"""
        rules_data = []
        for rule in self.rules:
            rules_data.append({
                "name": rule.name,
                "metric": rule.metric,
                "operator": rule.operator,
                "threshold": rule.threshold,
                "severity": rule.severity,
                "description": rule.description,
                "interval": rule.interval,
                "enabled": rule.enabled,
                "conditions": rule.conditions,
                "message_template": rule.message_template
            })
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(rules_data, f, ensure_ascii=False, indent=2)
    
    def import_rules(self, file_path: str):
        """从文件导入告警规则"""
        with open(file_path, 'r', encoding='utf-8') as f:
            rules_data = json.load(f)
        
        for rule_data in rules_data:
            rule = AlertRule(**rule_data)
            self.add_rule(rule) 