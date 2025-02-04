"""告警模块。"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from enum import Enum
import json
import logging
from src.config import Config
from src.utils.notifier import EmailNotifier, DingTalkNotifier, WeChatNotifier

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
    """告警规则"""

    def __init__(
        self,
        metric_name: str,
        threshold: float,
        operator: str = ">",
        duration: int = 300,  # 5分钟
        severity: str = "warning",
    ):
        """初始化。

        Args:
            metric_name: 指标名称
            threshold: 阈值
            operator: 操作符
            duration: 持续时间（秒）
            severity: 严重程度
        """
        self.metric_name = metric_name
        self.threshold = threshold
        self.operator = operator
        self.duration = duration
        self.severity = severity

    def check(self, value: float, history: List[float]) -> bool:
        """检查是否触发告警。

        Args:
            value: 当前值
            history: 历史值列表

        Returns:
            是否触发告警
        """
        if self.operator == ">":
            return value > self.threshold
        elif self.operator == "<":
            return value < self.threshold
        elif self.operator == ">=":
            return value >= self.threshold
        elif self.operator == "<=":
            return value <= self.threshold
        elif self.operator == "==":
            return value == self.threshold
        else:
            return False

class Alert:
    def __init__(self, rule: AlertRule, value: float, timestamp: datetime = None):
        self.rule = rule
        self.value = value
        self.timestamp = timestamp or datetime.now()
        self.message = self.rule.format_message(value)

    def format_message(self, value: float) -> str:
        """格式化告警消息"""
        return self.rule.format_message(value)

class AlertEngine:
    """告警引擎"""

    def __init__(self, config: Config):
        """初始化。

        Args:
            config: 配置对象
        """
        self.config = config
        self.rules: Dict[str, AlertRule] = {}
        self.notifiers = {
            "email": EmailNotifier(config),
            "dingtalk": DingTalkNotifier(config),
            "wechat": WeChatNotifier(config),
        }
        self.alert_history: Dict[str, List[datetime]] = {}
        self._load_default_rules()
        
    def _load_default_rules(self):
        """加载默认告警规则"""
        default_rules = [
            # 系统资源告警规则
            AlertRule(
                metric_name="system.cpu.usage",
                threshold=80,
                severity=AlertSeverity.ERROR
            ),
            AlertRule(
                metric_name="system.memory.percent",
                threshold=80,
                severity=AlertSeverity.ERROR
            ),
            AlertRule(
                metric_name="system.disk.percent",
                threshold=80,
                severity=AlertSeverity.ERROR
            ),
            
            # 爬虫相关告警规则
            AlertRule(
                metric_name="crawler.xhs.content.rate",
                threshold=5,
                severity=AlertSeverity.WARNING
            ),
            AlertRule(
                metric_name="crawler.bilibili.content.rate",
                threshold=5,
                severity=AlertSeverity.WARNING
            ),
            
            # 任务相关告警规则
            AlertRule(
                metric_name="task.success_rate",
                threshold=0.8,
                severity=AlertSeverity.ERROR
            ),
            AlertRule(
                metric_name="task.running",
                threshold=100,
                severity=AlertSeverity.WARNING
            ),
            
            # 错误相关告警规则
            AlertRule(
                metric_name="crawler.error.count",
                threshold=50,
                severity=AlertSeverity.ERROR
            )
        ]
        
        for rule in default_rules:
            self.add_rule(rule)
    
    def add_rule(self, rule: AlertRule) -> None:
        """添加告警规则。

        Args:
            rule: 告警规则
        """
        self.rules[rule.metric_name] = rule
    
    def remove_rule(self, metric_name: str) -> None:
        """移除告警规则。

        Args:
            metric_name: 指标名称
        """
        if metric_name in self.rules:
            del self.rules[metric_name]
    
    def check_alert(
        self,
        metric_name: str,
        value: float,
        history: Optional[List[float]] = None,
    ) -> bool:
        """检查是否需要告警。

        Args:
            metric_name: 指标名称
            value: 当前值
            history: 历史值列表

        Returns:
            是否需要告警
        """
        if metric_name not in self.rules:
            return False

        rule = self.rules[metric_name]
        history = history or []

        # 检查是否触发告警
        if rule.check(value, history):
            # 检查是否在冷却期
            now = datetime.now()
            if metric_name in self.alert_history:
                last_alert = self.alert_history[metric_name][-1]
                if (now - last_alert).total_seconds() < self.config.ALERT_COOLDOWN:
                    return False

            # 记录告警时间
            if metric_name not in self.alert_history:
                self.alert_history[metric_name] = []
            self.alert_history[metric_name].append(now)

            return True

        return False

    def send_alert(
        self,
        metric_name: str,
        value: float,
        channels: Optional[List[str]] = None,
    ) -> None:
        """发送告警。

        Args:
            metric_name: 指标名称
            value: 当前值
            channels: 通知渠道列表
        """
        if metric_name not in self.rules:
            return

        rule = self.rules[metric_name]
        channels = channels or self.config.ALERT_CHANNELS

        # 构造告警消息
        subject = f"[{rule.severity.upper()}] {metric_name} Alert"
        message = (
            f"Metric: {metric_name}\n"
            f"Value: {value}\n"
            f"Threshold: {rule.operator} {rule.threshold}\n"
            f"Time: {datetime.now()}"
        )

        # 发送告警
        for channel in channels:
            if channel in self.notifiers:
                self.notifiers[channel].send(subject, message)
    
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
        for rule in self.rules.values():
            rules_data.append({
                "metric_name": rule.metric_name,
                "threshold": rule.threshold,
                "operator": rule.operator,
                "duration": rule.duration,
                "severity": rule.severity
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