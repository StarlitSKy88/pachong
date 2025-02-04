"""告警历史记录模块

该模块负责告警历史的记录和查询，包括：
1. 告警事件记录
2. 告警状态变更记录
3. 告警处理记录
4. 告警统计分析
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import json
from collections import defaultdict

from .alert_rule import AlertRule, AlertStatus, AlertSeverity

logger = logging.getLogger(__name__)

@dataclass
class AlertEvent:
    """告警事件"""
    id: str
    rule_name: str
    rule_group: str
    metric: str
    value: float
    threshold: float
    operator: str
    severity: str
    status: str
    message: str
    timestamp: datetime
    recovery_time: Optional[datetime] = None
    handle_time: Optional[datetime] = None
    handler: Optional[str] = None
    comment: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class AlertStateChange:
    """告警状态变更记录"""
    alert_id: str
    from_status: str
    to_status: str
    timestamp: datetime
    reason: str

class AlertHistory:
    """告警历史记录管理器"""
    
    def __init__(self, db_url: str = None):
        self.logger = logging.getLogger('AlertHistory')
        self.db_url = db_url
        
        # 内存缓存
        self.events: List[AlertEvent] = []
        self.state_changes: List[AlertStateChange] = []
        self.stats: Dict[str, Dict] = defaultdict(lambda: defaultdict(int))
        
        # 统计时间窗口
        self.windows = [
            ('1h', timedelta(hours=1)),
            ('6h', timedelta(hours=6)),
            ('24h', timedelta(hours=24)),
            ('7d', timedelta(days=7)),
            ('30d', timedelta(days=30))
        ]
    
    def add_event(self, event: AlertEvent):
        """添加告警事件"""
        self.events.append(event)
        self._update_stats(event)
        self._save_event(event)
    
    def add_state_change(self, change: AlertStateChange):
        """添加状态变更记录"""
        self.state_changes.append(change)
        self._save_state_change(change)
    
    def get_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        rule_name: Optional[str] = None,
        rule_group: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AlertEvent]:
        """查询告警事件"""
        events = self.events
        
        if start_time:
            events = [e for e in events if e.timestamp >= start_time]
        if end_time:
            events = [e for e in events if e.timestamp <= end_time]
        if rule_name:
            events = [e for e in events if e.rule_name == rule_name]
        if rule_group:
            events = [e for e in events if e.rule_group == rule_group]
        if severity:
            events = [e for e in events if e.severity == severity]
        if status:
            events = [e for e in events if e.status == status]
            
        return sorted(
            events,
            key=lambda x: x.timestamp,
            reverse=True
        )[offset:offset+limit]
    
    def get_state_changes(
        self,
        alert_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AlertStateChange]:
        """查询状态变更记录"""
        changes = [c for c in self.state_changes if c.alert_id == alert_id]
        
        if start_time:
            changes = [c for c in changes if c.timestamp >= start_time]
        if end_time:
            changes = [c for c in changes if c.timestamp <= end_time]
            
        return sorted(
            changes,
            key=lambda x: x.timestamp,
            reverse=True
        )[offset:offset+limit]
    
    def get_stats(
        self,
        window: str = '24h',
        rule_group: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取统计数据"""
        now = datetime.now()
        stats = defaultdict(int)
        
        for event in self.events:
            # 检查时间窗口
            for w, delta in self.windows:
                if w == window and event.timestamp >= now - delta:
                    if not rule_group or event.rule_group == rule_group:
                        stats['total'] += 1
                        stats[f'severity.{event.severity}'] += 1
                        stats[f'status.{event.status}'] += 1
                        stats[f'group.{event.rule_group}'] += 1
                        
                        if event.handler:
                            stats['handled'] += 1
                            
                        if event.recovery_time:
                            recovery_time = (event.recovery_time - event.timestamp).total_seconds()
                            stats['total_recovery_time'] += recovery_time
                            stats['recovery_count'] += 1
                        
                        if event.handle_time:
                            handle_time = (event.handle_time - event.timestamp).total_seconds()
                            stats['total_handle_time'] += handle_time
                            stats['handle_count'] += 1
        
        # 计算平均值
        if stats['recovery_count'] > 0:
            stats['avg_recovery_time'] = stats['total_recovery_time'] / stats['recovery_count']
        if stats['handle_count'] > 0:
            stats['avg_handle_time'] = stats['total_handle_time'] / stats['handle_count']
            
        return dict(stats)
    
    def _update_stats(self, event: AlertEvent):
        """更新统计数据"""
        now = datetime.now()
        
        for window, delta in self.windows:
            if event.timestamp >= now - delta:
                stats = self.stats[window]
                stats['total'] += 1
                stats[f'severity.{event.severity}'] += 1
                stats[f'status.{event.status}'] += 1
                stats[f'group.{event.rule_group}'] += 1
    
    def _save_event(self, event: AlertEvent):
        """保存告警事件到数据库"""
        if not self.db_url:
            return
            
        # TODO: 实现数据库存储
        pass
    
    def _save_state_change(self, change: AlertStateChange):
        """保存状态变更记录到数据库"""
        if not self.db_url:
            return
            
        # TODO: 实现数据库存储
        pass
    
    def cleanup(self, before_time: datetime):
        """清理历史数据"""
        self.events = [e for e in self.events if e.timestamp >= before_time]
        self.state_changes = [c for c in self.state_changes if c.timestamp >= before_time]
        self._update_all_stats() 