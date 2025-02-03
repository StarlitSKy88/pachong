"""告警聚合器测试模块"""

import pytest
from datetime import datetime, timedelta
from monitor.alert_aggregator import AlertAggregator
from monitor.alert_rule import AlertRule, AlertStatus, AlertSeverity
from monitor.alert_engine import Alert

@pytest.fixture
def alert_rule():
    """创建测试告警规则"""
    return AlertRule(
        name="test_rule",
        metric="test_metric",
        operator=">",
        threshold=90,
        severity=AlertSeverity.WARNING,
        description="Test alert rule"
    )

@pytest.fixture
def aggregator():
    """创建测试聚合器"""
    return AlertAggregator(
        window_size=300,
        max_alerts=5,
        min_interval=60
    )

def test_should_alert(aggregator, alert_rule):
    """测试告警判断"""
    # 创建告警
    alert = Alert(
        rule=alert_rule,
        value=95,
        timestamp=datetime.now()
    )
    
    # 第一次告警应该发送
    assert aggregator.should_alert(alert) is True
    
    # 添加告警
    aggregator.add_alert(alert)
    
    # 间隔太短的告警不应该发送
    assert aggregator.should_alert(alert) is False
    
    # 超过最大告警数的告警不应该发送
    for _ in range(5):
        alert = Alert(
            rule=alert_rule,
            value=95,
            timestamp=datetime.now()
        )
        aggregator.add_alert(alert)
    assert aggregator.should_alert(alert) is False

def test_add_alert(aggregator, alert_rule):
    """测试添加告警"""
    # 创建第一个告警
    alert1 = Alert(
        rule=alert_rule,
        value=95,
        timestamp=datetime.now()
    )
    
    # 第一个告警应该直接返回
    result = aggregator.add_alert(alert1)
    assert result == alert1
    
    # 等待足够的时间间隔
    alert1.timestamp -= timedelta(seconds=61)
    
    # 创建第二个告警
    alert2 = Alert(
        rule=alert_rule,
        value=96,
        timestamp=datetime.now()
    )
    
    # 第二个告警应该返回聚合告警
    result = aggregator.add_alert(alert2)
    assert result is not None
    assert result != alert2
    assert "2条相关告警" in result.rule.description

def test_clean_old_alerts(aggregator, alert_rule):
    """测试清理过期告警"""
    # 创建过期告警
    old_alert = Alert(
        rule=alert_rule,
        value=95,
        timestamp=datetime.now() - timedelta(seconds=301)
    )
    aggregator.add_alert(old_alert)
    
    # 创建新告警
    new_alert = Alert(
        rule=alert_rule,
        value=96,
        timestamp=datetime.now()
    )
    aggregator.add_alert(new_alert)
    
    # 获取活动告警组
    groups = aggregator.get_active_groups()
    assert len(groups[alert_rule.name]) == 1
    assert groups[alert_rule.name][0] == new_alert

def test_get_group_stats(aggregator, alert_rule):
    """测试获取告警组统计"""
    # 创建多个告警
    alerts = []
    for i in range(3):
        alert = Alert(
            rule=alert_rule,
            value=95 + i,
            timestamp=datetime.now() - timedelta(seconds=i * 30)
        )
        alerts.append(alert)
        aggregator.add_alert(alert)
    
    # 获取统计信息
    stats = aggregator.get_group_stats()
    assert alert_rule.name in stats
    
    group_stats = stats[alert_rule.name]
    assert group_stats['count'] == 3
    assert group_stats['first_time'] == alerts[-1].timestamp
    assert group_stats['last_time'] == alerts[0].timestamp
    assert group_stats['severity'] == AlertSeverity.WARNING
    assert group_stats['frequency'] > 0

def test_reset(aggregator, alert_rule):
    """测试重置聚合器"""
    # 添加告警
    alert = Alert(
        rule=alert_rule,
        value=95,
        timestamp=datetime.now()
    )
    aggregator.add_alert(alert)
    
    # 验证状态
    assert len(aggregator.alert_groups) > 0
    assert len(aggregator.alert_counts) > 0
    assert len(aggregator.last_alert_time) > 0
    
    # 重置
    aggregator.reset()
    
    # 验证状态已清空
    assert len(aggregator.alert_groups) == 0
    assert len(aggregator.alert_counts) == 0
    assert len(aggregator.last_alert_time) == 0 