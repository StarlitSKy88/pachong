"""告警规则模块

该模块定义了告警规则的基本结构和处理逻辑，包括：
1. 告警规则定义
2. 规则匹配逻辑
3. 告警状态管理
4. 告警恢复机制
5. 告警抑制机制
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class AlertOperator(str, Enum):
    """告警操作符"""
    GT = ">"  # 大于
    LT = "<"  # 小于
    GE = ">="  # 大于等于
    LE = "<="  # 小于等于
    EQ = "=="  # 等于
    NE = "!="  # 不等于

class AlertSeverity(str, Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertStatus(str, Enum):
    """告警状态"""
    NORMAL = "normal"      # 正常
    PENDING = "pending"    # 待确认
    ALERTING = "alerting"  # 告警中
    RECOVERED = "recovered"  # 已恢复
    SILENCED = "silenced"  # 已静默

class AlertRule:
    """告警规则"""
    
    def __init__(
        self,
        name: str,
        metric: str,
        operator: str,
        threshold: float,
        severity: str,
        description: str = "",
        interval: int = 60,
        enabled: bool = True,
        conditions: List[Dict] = None,
        template: str = None,
        recovery_threshold: Optional[float] = None,
        recovery_window: int = 300,
        aggregation: str = "last",
        aggregation_window: int = 300,
        silence_duration: int = 3600,
        max_alert_count: int = 3,
        group: Optional['AlertRuleGroup'] = None
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
        self.template = template
        self.recovery_threshold = recovery_threshold
        self.recovery_window = recovery_window
        self.aggregation = aggregation
        self.aggregation_window = aggregation_window
        self.silence_duration = silence_duration
        self.max_alert_count = max_alert_count
        self.group = group

        # 运行时状态
        self.status = AlertStatus.NORMAL
        self.last_check_time: Optional[datetime] = None
        self.last_alert_time: Optional[datetime] = None
        self.alert_count = 0
        self.silence_until: Optional[datetime] = None
        self.value_history: List[tuple[datetime, float]] = []
    
    def check_value(self, value: float) -> bool:
        """检查值是否触发告警"""
        if not self.enabled:
            return False
            
        # 检查静默期
        if self.silence_until and datetime.now() < self.silence_until:
            return False
            
        # 检查告警次数限制
        if self.alert_count >= self.max_alert_count:
            return False
            
        # 根据操作符比较值
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
        else:
            return False
    
    def check_recovery(self, value: float) -> bool:
        """检查是否恢复"""
        if not self.recovery_threshold:
            return not self.check_value(value)
            
        # 根据恢复阈值检查
        if self.operator in [AlertOperator.GT, AlertOperator.GE]:
            return value <= self.recovery_threshold
        elif self.operator in [AlertOperator.LT, AlertOperator.LE]:
            return value >= self.recovery_threshold
        else:
            return value == self.recovery_threshold
    
    def check_conditions(self, metrics: Dict[str, Any]) -> bool:
        """检查附加条件"""
        for condition in self.conditions:
            metric = metrics.get(condition['metric'])
            if not metric:
                return False
                
            operator = condition['operator']
            threshold = condition['threshold']
            
            if operator == AlertOperator.GT:
                if not metric > threshold:
                    return False
            elif operator == AlertOperator.LT:
                if not metric < threshold:
                    return False
            elif operator == AlertOperator.GE:
                if not metric >= threshold:
                    return False
            elif operator == AlertOperator.LE:
                if not metric <= threshold:
                    return False
            elif operator == AlertOperator.EQ:
                if not metric == threshold:
                    return False
            elif operator == AlertOperator.NE:
                if not metric != threshold:
                    return False
        
        return True
    
    def add_value(self, value: float):
        """添加值到历史记录"""
        now = datetime.now()
        self.value_history.append((now, value))
        
        # 清理过期数据
        cutoff = now - timedelta(seconds=self.aggregation_window)
        self.value_history = [
            (t, v) for t, v in self.value_history
            if t >= cutoff
        ]
    
    def get_aggregated_value(self) -> Optional[float]:
        """获取聚合值"""
        if not self.value_history:
            return None
            
        values = [v for _, v in self.value_history]
        
        if self.aggregation == "last":
            return values[-1]
        elif self.aggregation == "min":
            return min(values)
        elif self.aggregation == "max":
            return max(values)
        elif self.aggregation == "avg":
            return sum(values) / len(values)
        else:
            return None
    
    def silence(self, duration: Optional[int] = None):
        """设置静默期"""
        duration = duration or self.silence_duration
        self.silence_until = datetime.now() + timedelta(seconds=duration)
        self.status = AlertStatus.SILENCED
    
    def unsilence(self):
        """取消静默"""
        self.silence_until = None
        self.status = AlertStatus.NORMAL
    
    def reset(self):
        """重置状态"""
        self.status = AlertStatus.NORMAL
        self.last_check_time = None
        self.last_alert_time = None
        self.alert_count = 0
        self.silence_until = None
        self.value_history.clear()
    
    def format_message(self, value: float) -> str:
        """格式化告警消息"""
        if self.template:
            try:
                return self.template.format(
                    name=self.name,
                    metric=self.metric,
                    value=value,
                    threshold=self.threshold,
                    operator=self.operator,
                    description=self.description
                )
            except Exception as e:
                logger.error(f"Error formatting alert message: {e}")
                
        return f"{self.description} (当前值: {value}, 阈值: {self.threshold})"

class AlertRuleGroup:
    """告警规则组"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.rules: List[AlertRule] = []
        self.enabled = True
    
    def add_rule(self, rule: AlertRule):
        """添加规则"""
        rule.group = self
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
    
    def silence(self, duration: Optional[int] = None):
        """设置规则组静默期"""
        for rule in self.rules:
            rule.silence(duration)
    
    def unsilence(self):
        """取消规则组静默"""
        for rule in self.rules:
            rule.unsilence()
    
    def reset(self):
        """重置规则组状态"""
        for rule in self.rules:
            rule.reset() 