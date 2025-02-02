"""爬虫系统监控告警测试"""

import pytest
import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional
from src.crawlers.bilibili_crawler import BiliBiliCrawler
from src.crawlers.xiaohongshu_crawler import XiaoHongShuCrawler
from src.monitor.alert import AlertManager, AlertRule, AlertLevel, Alert
from src.monitor.metrics import MetricsManager

class TestAlertRule(AlertRule):
    """测试告警规则"""
    
    def __init__(
        self,
        name: str,
        threshold: float,
        window: int = 60,
        level: AlertLevel = AlertLevel.WARNING
    ):
        """初始化告警规则
        
        Args:
            name: 规则名称
            threshold: 阈值
            window: 时间窗口（秒）
            level: 告警级别
        """
        self.name = name
        self.threshold = threshold
        self.window = window
        self.level = level
        self.values: List[float] = []
        self.timestamps: List[float] = []
        
    def add_value(self, value: float):
        """添加指标值
        
        Args:
            value: 指标值
        """
        now = time.time()
        self.values.append(value)
        self.timestamps.append(now)
        
        # 清理过期数据
        while self.timestamps and now - self.timestamps[0] > self.window:
            self.values.pop(0)
            self.timestamps.pop(0)
            
    def check(self) -> Optional[Alert]:
        """检查是否需要告警
        
        Returns:
            Optional[Alert]: 告警信息
        """
        if not self.values:
            return None
            
        avg_value = sum(self.values) / len(self.values)
        if avg_value > self.threshold:
            return Alert(
                rule_name=self.name,
                level=self.level,
                message=f"Average value {avg_value:.2f} exceeds threshold {self.threshold}",
                timestamp=datetime.now()
            )
        return None

@pytest.fixture
async def monitoring_system():
    """创建监控系统"""
    metrics = MetricsManager()
    alerts = AlertManager()
    
    # 添加告警规则
    alerts.add_rule(
        TestAlertRule(
            name="high_error_rate",
            threshold=0.2,  # 错误率超过20%
            window=60,
            level=AlertLevel.ERROR
        )
    )
    alerts.add_rule(
        TestAlertRule(
            name="high_latency",
            threshold=5.0,  # 平均延迟超过5秒
            window=60,
            level=AlertLevel.WARNING
        )
    )
    alerts.add_rule(
        TestAlertRule(
            name="high_cpu_usage",
            threshold=80.0,  # CPU使用率超过80%
            window=60,
            level=AlertLevel.WARNING
        )
    )
    
    yield {
        "metrics": metrics,
        "alerts": alerts
    }
    
    # 清理资源
    await metrics.close()
    await alerts.close()

@pytest.fixture
async def crawlers(monitoring_system):
    """创建爬虫实例"""
    metrics = monitoring_system["metrics"]
    
    bilibili = BiliBiliCrawler(
        concurrent_limit=5,
        retry_limit=3,
        timeout=10,
        metrics=metrics
    )
    xiaohongshu = XiaoHongShuCrawler(
        concurrent_limit=5,
        retry_limit=3,
        timeout=10,
        metrics=metrics
    )
    
    async with bilibili, xiaohongshu:
        yield {
            "bilibili": bilibili,
            "xiaohongshu": xiaohongshu
        }

@pytest.mark.asyncio
async def test_error_rate_alert(crawlers, monitoring_system):
    """测试错误率告警"""
    alerts = monitoring_system["alerts"]
    rule = alerts.get_rule("high_error_rate")
    
    # 模拟高错误率
    for _ in range(10):
        rule.add_value(0.3)  # 30%错误率
        
    # 检查告警
    alert = rule.check()
    assert alert is not None
    assert alert.level == AlertLevel.ERROR
    assert "0.30" in alert.message
    
@pytest.mark.asyncio
async def test_latency_alert(crawlers, monitoring_system):
    """测试延迟告警"""
    alerts = monitoring_system["alerts"]
    rule = alerts.get_rule("high_latency")
    
    # 模拟高延迟
    for _ in range(10):
        rule.add_value(6.0)  # 6秒延迟
        
    # 检查告警
    alert = rule.check()
    assert alert is not None
    assert alert.level == AlertLevel.WARNING
    assert "6.00" in alert.message
    
@pytest.mark.asyncio
async def test_cpu_usage_alert(crawlers, monitoring_system):
    """测试CPU使用率告警"""
    alerts = monitoring_system["alerts"]
    rule = alerts.get_rule("high_cpu_usage")
    
    # 模拟高CPU使用率
    for _ in range(10):
        rule.add_value(85.0)  # 85% CPU使用率
        
    # 检查告警
    alert = rule.check()
    assert alert is not None
    assert alert.level == AlertLevel.WARNING
    assert "85.00" in alert.message
    
@pytest.mark.asyncio
async def test_alert_recovery(crawlers, monitoring_system):
    """测试告警恢复"""
    alerts = monitoring_system["alerts"]
    rule = alerts.get_rule("high_error_rate")
    
    # 先触发告警
    for _ in range(10):
        rule.add_value(0.3)
        
    alert = rule.check()
    assert alert is not None
    
    # 等待数据过期
    await asyncio.sleep(rule.window + 1)
    
    # 添加正常数据
    for _ in range(10):
        rule.add_value(0.1)
        
    # 检查告警恢复
    alert = rule.check()
    assert alert is None
    
@pytest.mark.asyncio
async def test_multiple_alerts(crawlers, monitoring_system):
    """测试多个告警"""
    alerts = monitoring_system["alerts"]
    
    # 触发多个告警
    for rule in alerts.rules:
        for _ in range(10):
            if rule.name == "high_error_rate":
                rule.add_value(0.3)
            elif rule.name == "high_latency":
                rule.add_value(6.0)
            elif rule.name == "high_cpu_usage":
                rule.add_value(85.0)
                
    # 检查所有告警
    active_alerts = []
    for rule in alerts.rules:
        alert = rule.check()
        if alert:
            active_alerts.append(alert)
            
    assert len(active_alerts) == 3
    assert any(a.level == AlertLevel.ERROR for a in active_alerts)
    assert any(a.level == AlertLevel.WARNING for a in active_alerts)
    
@pytest.mark.asyncio
async def test_alert_persistence(crawlers, monitoring_system):
    """测试告警持久化"""
    alerts = monitoring_system["alerts"]
    
    # 触发告警
    rule = alerts.get_rule("high_error_rate")
    for _ in range(10):
        rule.add_value(0.3)
        
    # 保存告警历史
    alert = rule.check()
    if alert:
        await alerts.save_alert(alert)
        
    # 查询告警历史
    history = await alerts.get_alert_history(
        start_time=datetime.now() - timedelta(hours=1)
    )
    
    assert len(history) > 0
    assert history[0].rule_name == "high_error_rate"
    assert history[0].level == AlertLevel.ERROR 