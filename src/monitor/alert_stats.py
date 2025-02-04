"""告警统计分析模块

该模块负责告警数据的统计和分析，包括：
1. 告警趋势分析
2. 告警分布统计
3. 告警关联分析
4. 告警性能分析
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import pandas as pd
import numpy as np
from scipy import stats

from .alert_history import AlertHistory, AlertEvent
from .alert_rule import AlertRule, AlertStatus, AlertSeverity

logger = logging.getLogger(__name__)

class AlertStats:
    """告警统计分析器"""
    
    def __init__(self, history: AlertHistory):
        self.logger = logging.getLogger('AlertStats')
        self.history = history
        
        # 统计时间窗口
        self.windows = [
            ('1h', timedelta(hours=1)),
            ('6h', timedelta(hours=6)),
            ('24h', timedelta(hours=24)),
            ('7d', timedelta(days=7)),
            ('30d', timedelta(days=30))
        ]
    
    def get_trend(
        self,
        start_time: datetime,
        end_time: datetime,
        interval: str = '1h',
        rule_group: Optional[str] = None,
        severity: Optional[str] = None
    ) -> pd.DataFrame:
        """获取告警趋势"""
        # 获取告警事件
        events = self.history.get_events(
            start_time=start_time,
            end_time=end_time,
            rule_group=rule_group,
            severity=severity
        )
        
        if not events:
            return pd.DataFrame()
        
        # 转换为DataFrame
        df = pd.DataFrame([
            {
                'timestamp': e.timestamp,
                'rule_name': e.rule_name,
                'rule_group': e.rule_group,
                'severity': e.severity,
                'value': e.value
            }
            for e in events
        ])
        
        # 设置时间索引
        df.set_index('timestamp', inplace=True)
        
        # 按时间间隔重采样
        result = df.resample(interval).agg({
            'rule_name': 'count',
            'value': ['mean', 'min', 'max']
        })
        
        # 重命名列
        result.columns = [
            'count',
            'value_mean',
            'value_min',
            'value_max'
        ]
        
        return result
    
    def get_distribution(
        self,
        window: str = '24h',
        group_by: str = 'severity'
    ) -> Dict[str, int]:
        """获取告警分布"""
        stats = self.history.get_stats(window)
        
        if group_by == 'severity':
            return {
                k.replace('severity.', ''): v
                for k, v in stats.items()
                if k.startswith('severity.')
            }
        elif group_by == 'status':
            return {
                k.replace('status.', ''): v
                for k, v in stats.items()
                if k.startswith('status.')
            }
        elif group_by == 'group':
            return {
                k.replace('group.', ''): v
                for k, v in stats.items()
                if k.startswith('group.')
            }
        else:
            return {}
    
    def get_correlation(
        self,
        start_time: datetime,
        end_time: datetime,
        rule_names: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """获取告警关联性"""
        # 获取告警事件
        events = self.history.get_events(
            start_time=start_time,
            end_time=end_time,
            rule_name=rule_names[0] if rule_names else None
        )
        
        if not events:
            return pd.DataFrame()
        
        # 转换为DataFrame
        df = pd.DataFrame([
            {
                'timestamp': e.timestamp,
                'rule_name': e.rule_name,
                'value': e.value
            }
            for e in events
        ])
        
        # 数据透视
        pivot = pd.pivot_table(
            df,
            values='value',
            index='timestamp',
            columns='rule_name',
            aggfunc='first'
        )
        
        # 计算相关系数
        corr = pivot.corr()
        
        return corr
    
    def get_performance(
        self,
        window: str = '24h',
        rule_group: Optional[str] = None
    ) -> Dict[str, float]:
        """获取告警性能指标"""
        stats = self.history.get_stats(window, rule_group)
        
        metrics = {
            'total': stats.get('total', 0),
            'handled': stats.get('handled', 0),
            'recovery_count': stats.get('recovery_count', 0),
            'handle_count': stats.get('handle_count', 0),
            'avg_recovery_time': stats.get('avg_recovery_time', 0),
            'avg_handle_time': stats.get('avg_handle_time', 0)
        }
        
        # 计算处理率
        if metrics['total'] > 0:
            metrics['handle_rate'] = metrics['handled'] / metrics['total'] * 100
        else:
            metrics['handle_rate'] = 0
            
        # 计算恢复率
        if metrics['total'] > 0:
            metrics['recovery_rate'] = metrics['recovery_count'] / metrics['total'] * 100
        else:
            metrics['recovery_rate'] = 0
        
        return metrics
    
    def get_anomaly_rules(
        self,
        window: str = '24h',
        threshold: float = 2.0
    ) -> List[Tuple[str, float]]:
        """获取异常规则"""
        # 获取告警事件
        now = datetime.now()
        delta = None
        for w, d in self.windows:
            if w == window:
                delta = d
                break
                
        if not delta:
            return []
            
        events = self.history.get_events(
            start_time=now - delta,
            end_time=now
        )
        
        if not events:
            return []
        
        # 统计规则告警次数
        rule_counts = defaultdict(int)
        for event in events:
            rule_counts[event.rule_name] += 1
        
        # 计算Z分数
        counts = list(rule_counts.values())
        if len(counts) < 2:
            return []
            
        z_scores = stats.zscore(counts)
        
        # 找出异常规则
        anomalies = []
        for (rule_name, count), z_score in zip(rule_counts.items(), z_scores):
            if abs(z_score) > threshold:
                anomalies.append((rule_name, z_score))
        
        return sorted(anomalies, key=lambda x: abs(x[1]), reverse=True)
    
    def get_summary(self, window: str = '24h') -> Dict[str, Any]:
        """获取告警摘要"""
        # 获取基础统计
        stats = self.history.get_stats(window)
        
        # 获取分布统计
        severity_dist = self.get_distribution(window, 'severity')
        status_dist = self.get_distribution(window, 'status')
        group_dist = self.get_distribution(window, 'group')
        
        # 获取性能指标
        performance = self.get_performance(window)
        
        # 获取异常规则
        anomalies = self.get_anomaly_rules(window)
        
        return {
            'total': stats.get('total', 0),
            'severity_distribution': severity_dist,
            'status_distribution': status_dist,
            'group_distribution': group_dist,
            'performance': performance,
            'anomaly_rules': anomalies
        } 