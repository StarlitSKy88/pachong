import pytest
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from src.monitor.alert_notifier import AlertNotifier, AlertTemplate
from src.monitor.alert_engine import Alert, AlertRule, AlertSeverity

@pytest.fixture
def template_dir(tmp_path):
    """创建临时模板目录"""
    return str(tmp_path / "templates")

@pytest.fixture
def alert_notifier(template_dir):
    """创建AlertNotifier实例"""
    return AlertNotifier(template_dir)

@pytest.fixture
def test_alerts():
    """创建测试告警"""
    rule1 = AlertRule(
        name="test_rule_1",
        metric="test.metric",
        operator=">",
        threshold=100,
        severity=AlertSeverity.WARNING,
        description="Test rule 1"
    )
    
    rule2 = AlertRule(
        name="test_rule_2",
        metric="test.metric",
        operator="<",
        threshold=50,
        severity=AlertSeverity.ERROR,
        description="Test rule 2"
    )
    
    return [
        Alert(rule1, 110, datetime.now(), "alerting"),
        Alert(rule2, 40, datetime.now(), "recovered")
    ]

def test_alert_template_initialization(template_dir):
    """测试告警模板初始化"""
    template = AlertTemplate(template_dir)
    
    # 验证模板目录创建
    template_dir = Path(template_dir)
    assert template_dir.exists()
    assert template_dir.is_dir()
    
    # 验证默认模板文件创建
    assert (template_dir / "email.html").exists()
    assert (template_dir / "dingtalk.md").exists()
    assert (template_dir / "wechat.md").exists()

def test_alert_template_rendering(template_dir, test_alerts):
    """测试告警模板渲染"""
    template = AlertTemplate(template_dir)
    
    # 渲染邮件模板
    html_content = template.render(
        'email.html',
        alerts=test_alerts,
        summary={'severity_counts': {'warning': 1, 'error': 1}}
    )
    
    # 验证渲染结果
    assert "监控系统告警通知" in html_content
    assert "test_rule_1" in html_content
    assert "test_rule_2" in html_content
    assert "已恢复" in html_content
    assert "warning: 1" in html_content
    assert "error: 1" in html_content

@pytest.mark.asyncio
async def test_email_notification(alert_notifier, test_alerts):
    """测试邮件通知"""
    # 配置邮件
    alert_notifier.configure_email(
        host="smtp.example.com",
        port=587,
        username="test@example.com",
        password="password",
        recipients=["admin@example.com"]
    )
    
    # 模拟SMTP服务器
    with patch('smtplib.SMTP') as mock_smtp:
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        # 发送通知
        await alert_notifier.send_email(test_alerts)
        
        # 验证SMTP调用
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("test@example.com", "password")
        mock_server.send_message.assert_called_once()
        
        # 验证邮件内容
        msg = mock_server.send_message.call_args[0][0]
        assert msg['Subject'] == "[监控告警] 2条新告警"
        assert msg['From'] == "test@example.com"
        assert msg['To'] == "admin@example.com"

@pytest.mark.asyncio
async def test_webhook_notification(alert_notifier, test_alerts):
    """测试Webhook通知"""
    # 配置Webhook
    alert_notifier.configure_webhook(
        url="https://webhook.example.com",
        headers={"Authorization": "Bearer token"}
    )
    
    # 模拟HTTP请求
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # 发送通知
        await alert_notifier.send_webhook(test_alerts)
        
        # 验证HTTP调用
        mock_post.assert_called_once()
        args = mock_post.call_args
        
        # 验证请求URL和头部
        assert args[0][0] == "https://webhook.example.com"
        assert args[1]['headers'] == {"Authorization": "Bearer token"}
        
        # 验证请求数据
        data = json.loads(args[1]['json'])
        assert len(data['alerts']) == 2
        assert data['alerts'][0]['rule_name'] == "test_rule_1"
        assert data['alerts'][1]['rule_name'] == "test_rule_2"
        assert data['summary']['severity_counts'] == {'warning': 1, 'error': 1}

@pytest.mark.asyncio
async def test_dingtalk_notification(alert_notifier, test_alerts):
    """测试钉钉通知"""
    # 配置钉钉
    alert_notifier.configure_dingtalk(
        access_token="test_token",
        secret="test_secret"
    )
    
    # 模拟HTTP请求
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # 发送通知
        await alert_notifier.send_dingtalk(test_alerts)
        
        # 验证HTTP调用
        mock_post.assert_called_once()
        args = mock_post.call_args
        
        # 验证请求URL
        assert "access_token=test_token" in args[0][0]
        
        # 验证请求数据
        data = args[1]['json']
        assert data['msgtype'] == 'markdown'
        assert "监控告警: 2条新告警" in data['markdown']['title']
        assert "test_rule_1" in data['markdown']['text']
        assert "test_rule_2" in data['markdown']['text']
        assert "已恢复" in data['markdown']['text']

@pytest.mark.asyncio
async def test_wechat_notification(alert_notifier, test_alerts):
    """测试企业微信通知"""
    # 配置企业微信
    alert_notifier.configure_wechat(
        corp_id="test_corp_id",
        corp_secret="test_corp_secret",
        agent_id="test_agent_id"
    )
    
    # 模拟HTTP请求
    with patch('aiohttp.ClientSession.get') as mock_get, \
         patch('aiohttp.ClientSession.post') as mock_post:
        # 模拟获取token
        mock_token_response = AsyncMock()
        mock_token_response.status = 200
        mock_token_response.json = AsyncMock(return_value={'access_token': 'test_token'})
        mock_get.return_value.__aenter__.return_value = mock_token_response
        
        # 模拟发送消息
        mock_send_response = AsyncMock()
        mock_send_response.status = 200
        mock_post.return_value.__aenter__.return_value = mock_send_response
        
        # 发送通知
        await alert_notifier.send_wechat(test_alerts)
        
        # 验证获取token请求
        mock_get.assert_called_once()
        assert "corpid=test_corp_id" in mock_get.call_args[0][0]
        assert "corpsecret=test_corp_secret" in mock_get.call_args[0][0]
        
        # 验证发送消息请求
        mock_post.assert_called_once()
        args = mock_post.call_args
        assert "access_token=test_token" in args[0][0]
        
        # 验证请求数据
        data = args[1]['json']
        assert data['msgtype'] == 'markdown'
        assert data['agentid'] == 'test_agent_id'
        assert "test_rule_1" in data['markdown']['content']
        assert "test_rule_2" in data['markdown']['content']
        assert "已恢复" in data['markdown']['content']

@pytest.mark.asyncio
async def test_send_all(alert_notifier, test_alerts):
    """测试发送所有通知"""
    # 配置所有通知方式
    alert_notifier.configure_email(
        host="smtp.example.com",
        port=587,
        username="test@example.com",
        password="password",
        recipients=["admin@example.com"]
    )
    
    alert_notifier.configure_webhook(
        url="https://webhook.example.com",
        headers={"Authorization": "Bearer token"}
    )
    
    alert_notifier.configure_dingtalk(
        access_token="test_token",
        secret="test_secret"
    )
    
    alert_notifier.configure_wechat(
        corp_id="test_corp_id",
        corp_secret="test_corp_secret",
        agent_id="test_agent_id"
    )
    
    # 模拟所有通知方式
    with patch('smtplib.SMTP') as mock_smtp, \
         patch('aiohttp.ClientSession.post') as mock_post, \
         patch('aiohttp.ClientSession.get') as mock_get:
        # 模拟SMTP
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        # 模拟HTTP请求
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # 模拟获取微信token
        mock_token_response = AsyncMock()
        mock_token_response.status = 200
        mock_token_response.json = AsyncMock(return_value={'access_token': 'test_token'})
        mock_get.return_value.__aenter__.return_value = mock_token_response
        
        # 发送所有通知
        await alert_notifier.send_all(test_alerts)
        
        # 验证所有通知方式都被调用
        assert mock_server.send_message.called
        assert mock_post.call_count == 3  # webhook + dingtalk + wechat
        assert mock_get.called

@pytest.mark.asyncio
async def test_empty_alerts(alert_notifier):
    """测试空告警列表"""
    # 配置所有通知方式
    alert_notifier.configure_email(
        host="smtp.example.com",
        port=587,
        username="test@example.com",
        password="password"
    )
    
    # 模拟通知方式
    with patch('smtplib.SMTP') as mock_smtp:
        # 发送空告警列表
        await alert_notifier.send_all([])
        
        # 验证没有发送通知
        assert not mock_smtp.called

@pytest.mark.asyncio
async def test_notification_error_handling(alert_notifier, test_alerts):
    """测试通知错误处理"""
    # 配置所有通知方式
    alert_notifier.configure_email(
        host="smtp.example.com",
        port=587,
        username="test@example.com",
        password="password"
    )
    
    alert_notifier.configure_webhook(
        url="https://webhook.example.com"
    )
    
    # 模拟通知失败
    with patch('smtplib.SMTP') as mock_smtp, \
         patch('aiohttp.ClientSession.post') as mock_post:
        # SMTP失败
        mock_smtp.side_effect = Exception("SMTP error")
        
        # HTTP请求失败
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # 发送通知
        await alert_notifier.send_all(test_alerts)
        
        # 验证错误被正确处理
        assert mock_smtp.called
        assert mock_post.called 