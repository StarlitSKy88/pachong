import pytest
import aiohttp
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from src.monitor.crawler_monitor import CrawlerMonitor

@pytest.fixture
def monitor():
    """创建监控器实例"""
    return CrawlerMonitor()

@pytest.mark.asyncio
async def test_collect_metrics(monitor):
    """测试收集指标"""
    metrics = await monitor.collect_metrics()
    
    assert isinstance(metrics, dict)
    assert "proxy" in metrics
    assert "cookie" in metrics
    assert "content" in metrics
    assert "timestamp" in metrics
    
    # 检查代理指标
    assert isinstance(metrics["proxy"], dict)
    assert "total" in metrics["proxy"]
    assert "available" in metrics["proxy"]
    assert "score_avg" in metrics["proxy"]
    
    # 检查Cookie指标
    assert isinstance(metrics["cookie"], dict)
    assert "total" in metrics["cookie"]
    assert "valid" in metrics["cookie"]
    assert "score_avg" in metrics["cookie"]
    
    # 检查内容指标
    assert isinstance(metrics["content"], dict)
    assert "total" in metrics["content"]
    assert "success" in metrics["content"]
    assert "failed" in metrics["content"]
    assert "retry" in metrics["content"]

@pytest.mark.asyncio
async def test_check_alerts(monitor):
    """测试检查告警"""
    # 设置一些触发告警的指标
    monitor.proxy_metrics = {
        "total": 10,
        "available": 3,  # 低于阈值5
        "score_avg": 50  # 低于阈值60
    }
    
    monitor.cookie_metrics = {
        "total": 5,
        "valid": 2,  # 低于阈值3
        "score_avg": 55  # 低于阈值60
    }
    
    monitor.content_metrics = {
        "total": 1000,
        "success": 900,
        "failed": 15,  # 高于阈值10
        "retry": 25  # 高于阈值20
    }
    
    alerts = await monitor.check_alerts()
    
    assert isinstance(alerts, list)
    assert len(alerts) == 5  # 应该有5个告警
    
    # 检查告警格式
    for alert in alerts:
        assert isinstance(alert, dict)
        assert "level" in alert
        assert "type" in alert
        assert "message" in alert
        assert alert["level"] in ["warning", "error"]
        assert alert["type"] in ["proxy", "cookie", "content"]

@pytest.mark.asyncio
async def test_handle_alerts(monitor):
    """测试处理告警"""
    # 创建测试告警
    test_alerts = [
        {
            "level": "warning",
            "type": "proxy",
            "message": "测试告警"
        }
    ]
    
    # 设置告警Webhook
    monitor.alert_webhook = "http://test.webhook/alert"
    
    # Mock aiohttp.ClientSession
    mock_response = AsyncMock()
    mock_response.status = 200
    
    mock_session = AsyncMock()
    mock_session.post.return_value.__aenter__.return_value = mock_response
    
    with patch("aiohttp.ClientSession", return_value=mock_session):
        await monitor.handle_alerts(test_alerts)
        
        # 验证是否调用了Webhook
        mock_session.post.assert_called_once()
        args, kwargs = mock_session.post.call_args
        
        assert args[0] == monitor.alert_webhook
        assert "json" in kwargs
        assert isinstance(kwargs["json"], dict)
        assert kwargs["json"]["level"] == "warning"
        assert kwargs["json"]["type"] == "proxy"
        assert kwargs["json"]["message"] == "测试告警"

@pytest.mark.asyncio
async def test_handle_alerts_no_webhook(monitor):
    """测试没有Webhook时的告警处理"""
    test_alerts = [
        {
            "level": "warning",
            "type": "proxy",
            "message": "测试告警"
        }
    ]
    
    # 确保没有设置Webhook
    monitor.alert_webhook = None
    
    # 不应该抛出异常
    await monitor.handle_alerts(test_alerts)

@pytest.mark.asyncio
async def test_handle_alerts_webhook_error(monitor):
    """测试Webhook错误时的告警处理"""
    test_alerts = [
        {
            "level": "warning",
            "type": "proxy",
            "message": "测试告警"
        }
    ]
    
    monitor.alert_webhook = "http://test.webhook/alert"
    
    # Mock aiohttp.ClientSession抛出异常
    mock_session = AsyncMock()
    mock_session.post.side_effect = aiohttp.ClientError()
    
    with patch("aiohttp.ClientSession", return_value=mock_session):
        # 不应该抛出异常
        await monitor.handle_alerts(test_alerts)

@pytest.mark.asyncio
async def test_export_metrics(monitor):
    """测试导出指标"""
    test_metrics = {
        "proxy": {
            "total": 100,
            "available": 80,
            "score_avg": 85
        },
        "cookie": {
            "total": 50,
            "valid": 40,
            "score_avg": 75
        },
        "content": {
            "total": 1000,
            "success": 950,
            "failed": 30,
            "retry": 20
        },
        "timestamp": datetime.now().isoformat()
    }
    
    # 不应该抛出异常
    await monitor.export_metrics(test_metrics) 