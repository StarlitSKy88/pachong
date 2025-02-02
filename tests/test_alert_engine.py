import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from src.monitor.alert_engine import (
    AlertEngine,
    AlertRule,
    AlertRuleGroup,
    Alert,
    AlertOperator,
    AlertSeverity
)

@pytest.fixture
def metrics_collector():
    """创建MetricsCollector Mock"""
    return Mock()

@pytest.fixture
def alert_engine(metrics_collector):
    """创建AlertEngine实例"""
    engine = AlertEngine(metrics_collector)
    yield engine

def test_alert_rule_group():
    """测试告警规则组"""
    # 创建规则组
    group = AlertRuleGroup("test_group", "Test group description")
    assert group.name == "test_group"
    assert group.description == "Test group description"
    assert group.enabled is True
    
    # 添加规则
    rule = AlertRule(
        name="test_rule",
        metric="test.metric",
        operator=AlertOperator.GT,
        threshold=100
    )
    group.add_rule(rule)
    assert len(group.rules) == 1
    assert group.rules[0] == rule
    
    # 移除规则
    group.remove_rule("test_rule")
    assert len(group.rules) == 0
    
    # 禁用规则组
    group.add_rule(rule)
    group.disable()
    assert group.enabled is False
    assert rule.enabled is False
    
    # 启用规则组
    group.enable()
    assert group.enabled is True
    assert rule.enabled is True

def test_alert_rule():
    """测试告警规则"""
    # 创建规则
    rule = AlertRule(
        name="test_rule",
        metric="test.metric",
        operator=AlertOperator.GT,
        threshold=100,
        severity=AlertSeverity.WARNING,
        description="Test rule",
        recovery_threshold=90,
        template="Value: {value}"
    )
    
    # 检查基本属性
    assert rule.name == "test_rule"
    assert rule.metric == "test.metric"
    assert rule.operator == AlertOperator.GT
    assert rule.threshold == 100
    assert rule.severity == AlertSeverity.WARNING
    assert rule.recovery_threshold == 90
    
    # 测试值检查
    assert rule.check_value(110) is True
    assert rule.check_value(90) is False
    
    # 测试恢复检查
    assert rule.check_recovery(85) is True
    assert rule.check_recovery(95) is False
    
    # 测试消息格式化
    message = rule.format_message(110)
    assert "Value: 110" in message

def test_alert_rule_aggregation():
    """测试告警规则聚合"""
    rule = AlertRule(
        name="test_rule",
        metric="test.metric",
        operator=AlertOperator.GT,
        threshold=100,
        aggregation="avg",
        aggregation_window=300
    )
    
    # 添加历史数据
    now = datetime.now()
    rule.add_history(90, now - timedelta(seconds=200))
    rule.add_history(110, now - timedelta(seconds=100))
    
    # 测试聚合值
    value = rule.get_aggregated_value(now)
    assert value == 100  # (90 + 110) / 2
    
    # 测试数据清理
    rule.add_history(120, now)
    old_value = now - timedelta(seconds=400)
    rule.add_history(50, old_value)
    assert len(rule._history) == 3  # 旧数据应被清理

def test_alert_engine_rule_management(alert_engine):
    """测试告警引擎规则管理"""
    # 创建规则组
    group = AlertRuleGroup("test_group", "Test group")
    rule = AlertRule(
        name="test_rule",
        metric="test.metric",
        operator=AlertOperator.GT,
        threshold=100
    )
    group.add_rule(rule)
    
    # 添加规则组
    alert_engine.add_rule_group(group)
    assert "test_group" in alert_engine.rule_groups
    assert "test_rule" in alert_engine.rules
    
    # 获取规则组
    retrieved_group = alert_engine.get_rule_group("test_group")
    assert retrieved_group == group
    
    # 禁用规则组
    alert_engine.disable_rule_group("test_group")
    assert not group.enabled
    assert not rule.enabled
    
    # 启用规则组
    alert_engine.enable_rule_group("test_group")
    assert group.enabled
    assert rule.enabled
    
    # 移除规则组
    alert_engine.remove_rule_group("test_group")
    assert "test_group" not in alert_engine.rule_groups
    assert "test_rule" not in alert_engine.rules

def test_alert_engine_rule_checking(alert_engine):
    """测试告警引擎规则检查"""
    # 创建规则
    rule = AlertRule(
        name="test_rule",
        metric="test.metric",
        operator=AlertOperator.GT,
        threshold=100,
        conditions=[{
            "metric": "other.metric",
            "operator": AlertOperator.GT,
            "threshold": 50
        }]
    )
    alert_engine.add_rule(rule)
    
    # 创建测试指标
    metrics = {
        "test.metric": Mock(value=110),
        "other.metric": Mock(value=60)
    }
    
    # 检查规则
    alerts = alert_engine.check_rules(metrics)
    assert len(alerts) == 1
    assert alerts[0].rule == rule
    assert alerts[0].value == 110
    assert alerts[0].status == "alerting"
    
    # 测试恢复
    metrics["test.metric"].value = 90
    alerts = alert_engine.check_rules(metrics)
    assert len(alerts) == 1
    assert alerts[0].status == "recovered"

def test_alert_engine_handlers(alert_engine):
    """测试告警引擎处理器"""
    # 创建处理器
    handler_calls = []
    def test_handler(alert):
        handler_calls.append(alert)
    
    # 添加处理器
    alert_engine.add_handler(AlertSeverity.WARNING, test_handler)
    
    # 创建并触发告警
    rule = AlertRule(
        name="test_rule",
        metric="test.metric",
        operator=AlertOperator.GT,
        threshold=100,
        severity=AlertSeverity.WARNING
    )
    alert_engine.add_rule(rule)
    
    metrics = {"test.metric": Mock(value=110)}
    alert_engine.check_rules(metrics)
    
    # 验证处理器被调用
    assert len(handler_calls) == 1
    assert handler_calls[0].rule == rule
    
    # 移除处理器
    alert_engine.remove_handler(AlertSeverity.WARNING, test_handler)
    handler_calls.clear()
    
    alert_engine.check_rules(metrics)
    assert len(handler_calls) == 0

def test_alert_engine_alert_management(alert_engine):
    """测试告警引擎告警管理"""
    # 创建测试告警
    rule = AlertRule(
        name="test_rule",
        metric="test.metric",
        operator=AlertOperator.GT,
        threshold=100
    )
    
    old_time = datetime.now() - timedelta(days=10)
    recent_time = datetime.now() - timedelta(hours=1)
    
    alert1 = Alert(rule, 110, old_time)
    alert2 = Alert(rule, 120, recent_time)
    
    alert_engine.alerts.extend([alert1, alert2])
    
    # 测试告警查询
    alerts = alert_engine.get_alerts(
        severity=AlertSeverity.WARNING,
        status="alerting",
        start_time=datetime.now() - timedelta(days=1)
    )
    assert len(alerts) == 1
    assert alerts[0] == alert2
    
    # 测试活动告警
    active_alerts = alert_engine.get_active_alerts()
    assert len(active_alerts) == 2
    
    # 测试最近告警
    recent_alerts = alert_engine.get_recent_alerts(hours=2)
    assert len(recent_alerts) == 1
    assert recent_alerts[0] == alert2
    
    # 测试清理旧告警
    alert_engine.clean_old_alerts(days=7)
    assert len(alert_engine.alerts) == 1
    assert alert_engine.alerts[0] == alert2

def test_alert_engine_rule_import_export(alert_engine, tmp_path):
    """测试告警规则导入导出"""
    # 创建测试规则组
    group = AlertRuleGroup("test_group", "Test group")
    rule = AlertRule(
        name="test_rule",
        metric="test.metric",
        operator=AlertOperator.GT,
        threshold=100,
        severity=AlertSeverity.WARNING,
        description="Test rule",
        recovery_threshold=90,
        template="Value: {value}",
        conditions=[{
            "metric": "other.metric",
            "operator": AlertOperator.GT,
            "threshold": 50
        }]
    )
    group.add_rule(rule)
    alert_engine.add_rule_group(group)
    
    # 导出规则
    export_file = tmp_path / "rules.json"
    alert_engine.export_rules(str(export_file))
    
    # 清除现有规则
    alert_engine.remove_rule_group("test_group")
    assert len(alert_engine.rules) == 0
    
    # 导入规则
    alert_engine.import_rules(str(export_file))
    
    # 验证规则
    assert "test_group" in alert_engine.rule_groups
    imported_group = alert_engine.rule_groups["test_group"]
    assert imported_group.name == group.name
    assert imported_group.description == group.description
    
    imported_rule = imported_group.rules[0]
    assert imported_rule.name == rule.name
    assert imported_rule.metric == rule.metric
    assert imported_rule.threshold == rule.threshold
    assert imported_rule.conditions == rule.conditions 