import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from metrics import MetricsCollector
from alert import AlertEngine, AlertRule, Alert
from src.monitor.metrics import CrawlerMetrics, metrics_collector
from src.monitor.dashboard import DashboardServer

@pytest.fixture
def metrics_collector():
    return MetricsCollector()

@pytest.fixture
def alert_engine():
    return AlertEngine()

async def test_metrics_collector(metrics_collector):
    """测试指标收集器"""
    # 测试系统指标收集
    system_metrics = await metrics_collector.collect_system_metrics()
    assert "system.cpu.usage" in system_metrics
    assert "system.memory.percent" in system_metrics
    assert "system.disk.percent" in system_metrics
    
    # 测试爬虫指标收集
    crawler_metrics = await metrics_collector.collect_crawler_metrics()
    for platform in ["xhs", "bilibili"]:
        assert f"crawler.{platform}.content.total" in crawler_metrics
        assert f"crawler.{platform}.content.recent" in crawler_metrics
        assert f"crawler.{platform}.content.rate" in crawler_metrics
    
    # 测试所有指标收集
    all_metrics = await metrics_collector.collect_all_metrics()
    assert len(all_metrics) > 0
    
    # 测试指标值格式
    for metric in all_metrics.values():
        assert hasattr(metric, "value")
        assert hasattr(metric, "timestamp")

def test_alert_engine(alert_engine):
    """测试告警引擎"""
    # 添加测试规则
    rule = AlertRule(
        name="高CPU使用率",
        metric="system.cpu.usage",
        operator=">",
        threshold=80,
        severity="critical",
        description="CPU使用率超过80%",
        interval=300,
        enabled=True
    )
    alert_engine.add_rule(rule)
    
    # 测试规则检查
    test_metrics = {
        "system.cpu.usage": type("Metric", (), {"value": 85, "timestamp": datetime.now()})()
    }
    alerts = alert_engine.check_rules(test_metrics)
    assert len(alerts) == 1
    assert alerts[0].rule == rule
    assert alerts[0].value == 85
    
    # 测试告警检索
    alert_engine.add_alert(alerts[0])
    recent_alerts = alert_engine.get_recent_alerts(limit=10)
    assert len(recent_alerts) == 1
    assert recent_alerts[0].rule == rule
    
    # 测试告警清理
    old_alert = Alert(
        rule=rule,
        value=90,
        timestamp=datetime.now() - timedelta(days=8)
    )
    alert_engine.add_alert(old_alert)
    alert_engine.clean_old_alerts(days=7)
    assert len(alert_engine.get_recent_alerts()) == 1

@pytest.mark.asyncio
async def test_dashboard_data():
    """测试监控面板数据"""
    metrics_collector = MetricsCollector()
    alert_engine = AlertEngine()
    
    # 收集指标
    metrics = await metrics_collector.collect_all_metrics()
    assert metrics is not None
    assert len(metrics) > 0
    
    # 检查关键指标
    assert "system.cpu.usage" in metrics
    assert "system.memory.percent" in metrics
    assert "system.disk.percent" in metrics
    assert "task.success_rate" in metrics
    assert "crawler.error.count" in metrics
    
    # 检查健康状态计算
    health_status = all([
        metrics["system.cpu.usage"].value < 80,
        metrics["system.memory.percent"].value < 80,
        metrics["system.disk.percent"].value < 80,
        metrics["task.success_rate"].value > 0.8,
        metrics["crawler.error.count"].value < 50
    ])
    assert isinstance(health_status, bool)
    
    # 检查告警获取
    alerts = alert_engine.get_recent_alerts(limit=10)
    assert isinstance(alerts, list)

class TestCrawlerMetrics:
    """爬虫指标测试"""
    
    def test_add_request(self):
        """测试添加请求记录"""
        metrics = CrawlerMetrics('test_platform')
        
        # 添加成功请求
        metrics.add_request(True, 0.5)
        assert metrics.total_requests == 1
        assert metrics.success_requests == 1
        assert metrics.failed_requests == 0
        assert metrics.response_times == [0.5]
        
        # 添加失败请求
        metrics.add_request(False, 1.0, "Request failed")
        assert metrics.total_requests == 2
        assert metrics.success_requests == 1
        assert metrics.failed_requests == 1
        assert len(metrics.error_messages) == 1
    
    def test_add_item(self):
        """测试添加内容记录"""
        metrics = CrawlerMetrics('test_platform')
        
        # 添加成功内容
        metrics.add_item(True)
        assert metrics.total_items == 1
        assert metrics.success_items == 1
        assert metrics.failed_items == 0
        
        # 添加失败内容
        metrics.add_item(False, "Parse failed")
        assert metrics.total_items == 2
        assert metrics.success_items == 1
        assert metrics.failed_items == 1
        assert len(metrics.error_messages) == 1
    
    def test_metrics_calculation(self):
        """测试指标计算"""
        metrics = CrawlerMetrics('test_platform')
        
        # 添加数据
        metrics.add_request(True, 0.5)
        metrics.add_request(True, 1.0)
        metrics.add_request(False, 2.0)
        metrics.add_item(True)
        metrics.add_item(False)
        
        # 验证计算结果
        assert metrics.success_rate == 2/3
        assert metrics.item_success_rate == 0.5
        assert metrics.average_response_time == (0.5 + 1.0 + 2.0) / 3

class TestAlertEngine:
    """告警引擎测试"""
    
    def test_add_rule(self):
        """测试添加规则"""
        engine = alert_engine
        
        rule = AlertRule(
            name='test_rule',
            description='Test Rule',
            check_interval=300,
            severity='warning',
            condition=lambda x: True,
            message_template='Test message'
        )
        
        engine.add_rule(rule)
        assert 'test_rule' in engine.rules
    
    def test_remove_rule(self):
        """测试移除规则"""
        engine = alert_engine
        
        rule = AlertRule(
            name='test_rule',
            description='Test Rule',
            check_interval=300,
            severity='warning',
            condition=lambda x: True,
            message_template='Test message'
        )
        
        engine.add_rule(rule)
        engine.remove_rule('test_rule')
        assert 'test_rule' not in engine.rules
    
    @pytest.mark.asyncio
    async def test_check_rule(self):
        """测试检查规则"""
        engine = alert_engine
        
        # 添加测试规则
        rule = AlertRule(
            name='test_rule',
            description='Test Rule',
            check_interval=300,
            severity='warning',
            condition=lambda metrics: any(
                m.success_rate < 0.9 for m in metrics.values()
            ),
            message_template='Success rate is low'
        )
        
        engine.add_rule(rule)
        
        # 添加测试数据
        metrics = CrawlerMetrics('test_platform')
        metrics.add_request(True, 0.5)
        metrics.add_request(False, 1.0)
        metrics_collector.metrics['test_platform'] = metrics
        
        # 检查规则
        alert = await engine.check_rule(rule)
        assert alert is not None
        assert alert['rule'] == 'test_rule'
        assert alert['severity'] == 'warning'
    
    @pytest.mark.asyncio
    async def test_send_alert(self):
        """测试发送告警"""
        engine = alert_engine
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.status = 200
            
            alert = {
                'rule': 'test_rule',
                'severity': 'warning',
                'message': 'Test message',
                'time': datetime.now().isoformat()
            }
            
            success = await engine.send_alert(alert)
            assert success
            mock_post.assert_called_once()

class TestDashboardServer:
    """监控面板测试"""
    
    @pytest.mark.asyncio
    async def test_metrics_api(self, aiohttp_client):
        """测试指标API"""
        server = DashboardServer()
        client = await aiohttp_client(server.app)
        
        # 添加测试数据
        metrics = CrawlerMetrics('test_platform')
        metrics.add_request(True, 0.5)
        metrics.add_item(True)
        metrics_collector.metrics['test_platform'] = metrics
        
        # 请求API
        response = await client.get('/api/metrics')
        assert response.status == 200
        
        data = await response.json()
        assert 'test_platform' in data
        assert data['test_platform']['total_requests'] == 1
    
    @pytest.mark.asyncio
    async def test_alerts_api(self, aiohttp_client):
        """测试告警API"""
        server = DashboardServer()
        client = await aiohttp_client(server.app)
        
        # 添加测试数据
        alert = {
            'rule': 'test_rule',
            'severity': 'warning',
            'message': 'Test message',
            'time': datetime.now().isoformat()
        }
        alert_engine.add_history(alert)
        
        # 请求API
        response = await client.get('/api/alerts')
        assert response.status == 200
        
        data = await response.json()
        assert len(data) > 0
        assert data[0]['rule'] == 'test_rule'
    
    @pytest.mark.asyncio
    async def test_platform_stats_api(self, aiohttp_client, db_session, sample_platform, sample_content):
        """测试平台统计API"""
        server = DashboardServer()
        client = await aiohttp_client(server.app)
        
        # 请求API
        response = await client.get('/api/platform_stats')
        assert response.status == 200
        
        data = await response.json()
        assert sample_platform.name in data
        assert data[sample_platform.name]['content_stats']['total'] == 1

if __name__ == "__main__":
    pytest.main(["-v", "test_monitor.py"]) 