"""告警通知器模块

该模块负责告警通知的发送，支持多种通知渠道：
1. 邮件通知
2. Webhook通知
3. 钉钉通知
4. 企业微信通知
5. 自定义通知
"""

import asyncio
import logging
import json
import hmac
import hashlib
import base64
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib
import aiohttp
from jinja2 import Template, Environment, FileSystemLoader
from pathlib import Path

from .alert_rule import AlertStatus, AlertSeverity

logger = logging.getLogger(__name__)

class AlertTemplate:
    """告警模板"""
    
    def __init__(self, template_dir: Optional[str] = None):
        if template_dir:
            self.env = Environment(
                loader=FileSystemLoader(template_dir),
                autoescape=True
            )
        else:
            self.env = Environment(autoescape=True)
            self._init_default_templates()
    
    def _init_default_templates(self):
        """初始化默认模板"""
        # 邮件模板
        self.env.from_string("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>告警通知</title>
    <style>
        body { font-family: Arial, sans-serif; }
        .alert { padding: 15px; margin-bottom: 20px; border: 1px solid transparent; border-radius: 4px; }
        .alert-info { color: #31708f; background-color: #d9edf7; border-color: #bce8f1; }
        .alert-warning { color: #8a6d3b; background-color: #fcf8e3; border-color: #faebcc; }
        .alert-error { color: #a94442; background-color: #f2dede; border-color: #ebccd1; }
        .alert-critical { color: #ffffff; background-color: #d9534f; border-color: #d43f3a; }
    </style>
</head>
<body>
    <div class="alert alert-{{ alert.rule.severity }}">
        <h3>{{ alert.rule.name }}</h3>
        <p>{{ alert.rule.description }}</p>
        <ul>
            <li>指标: {{ alert.rule.metric }}</li>
            <li>当前值: {{ alert.value }}</li>
            <li>阈值: {{ alert.rule.operator }} {{ alert.rule.threshold }}</li>
            <li>时间: {{ alert.timestamp.strftime('%Y-%m-%d %H:%M:%S') }}</li>
            <li>状态: {{ alert.status }}</li>
        </ul>
    </div>
</body>
</html>
""", name="email.html")
        
        # 钉钉模板
        self.env.from_string("""
{
    "msgtype": "markdown",
    "markdown": {
        "title": "{{ alert.rule.name }}",
        "text": "### {{ alert.rule.name }}\n\n{{ alert.rule.description }}\n\n> 指标: {{ alert.rule.metric }}\n> 当前值: {{ alert.value }}\n> 阈值: {{ alert.rule.operator }} {{ alert.rule.threshold }}\n> 时间: {{ alert.timestamp.strftime('%Y-%m-%d %H:%M:%S') }}\n> 状态: {{ alert.status }}"
    }
}
""", name="dingtalk.json")
        
        # 企业微信模板
        self.env.from_string("""
{
    "msgtype": "markdown",
    "markdown": {
        "content": "### {{ alert.rule.name }}\n\n{{ alert.rule.description }}\n\n> 指标: {{ alert.rule.metric }}\n> 当前值: {{ alert.value }}\n> 阈值: {{ alert.rule.operator }} {{ alert.rule.threshold }}\n> 时间: {{ alert.timestamp.strftime('%Y-%m-%d %H:%M:%S') }}\n> 状态: {{ alert.status }}"
    }
}
""", name="wechat.json")
    
    def render(self, template_name: str, **kwargs) -> str:
        """渲染模板"""
        template = self.env.get_template(template_name)
        return template.render(**kwargs)

class AlertNotifier:
    """告警通知器"""
    
    def __init__(self, template_dir: Optional[str] = None):
        self.logger = logging.getLogger('AlertNotifier')
        self.template = AlertTemplate(template_dir)
        
        # 通知配置
        self.email_config: Optional[Dict] = None
        self.webhook_config: Optional[Dict] = None
        self.dingtalk_config: Optional[Dict] = None
        self.wechat_config: Optional[Dict] = None
        
        # 自定义处理器
        self.handlers: Dict[str, List[callable]] = {
            AlertSeverity.INFO: [],
            AlertSeverity.WARNING: [],
            AlertSeverity.ERROR: [],
            AlertSeverity.CRITICAL: []
        }
    
    def configure_email(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        use_tls: bool = True,
        recipients: List[str] = None
    ):
        """配置邮件通知"""
        self.email_config = {
            'host': host,
            'port': port,
            'username': username,
            'password': password,
            'use_tls': use_tls,
            'recipients': recipients or []
        }
        self.logger.info("Email notification configured")
    
    def configure_webhook(self, url: str, headers: Optional[Dict] = None):
        """配置Webhook通知"""
        self.webhook_config = {
            'url': url,
            'headers': headers or {}
        }
        self.logger.info("Webhook notification configured")
    
    def configure_dingtalk(self, access_token: str, secret: str = None):
        """配置钉钉通知"""
        self.dingtalk_config = {
            'access_token': access_token,
            'secret': secret
        }
        self.logger.info("DingTalk notification configured")
    
    def configure_wechat(
        self,
        corp_id: str,
        corp_secret: str,
        agent_id: str,
        to_user: str = "@all"
    ):
        """配置企业微信通知"""
        self.wechat_config = {
            'corp_id': corp_id,
            'corp_secret': corp_secret,
            'agent_id': agent_id,
            'to_user': to_user,
            'access_token': None,
            'token_expires': 0
        }
        self.logger.info("WeChat notification configured")
    
    def add_handler(self, severity: str, handler: callable):
        """添加自定义处理器"""
        if severity in self.handlers:
            self.handlers[severity].append(handler)
    
    def remove_handler(self, severity: str, handler: callable):
        """移除自定义处理器"""
        if severity in self.handlers and handler in self.handlers[severity]:
            self.handlers[severity].remove(handler)
    
    async def send_alert(self, alert: 'Alert'):
        """发送告警通知"""
        try:
            # 调用自定义处理器
            for handler in self.handlers.get(alert.rule.severity, []):
                try:
                    await handler(alert)
                except Exception as e:
                    self.logger.error(f"Error in custom handler: {e}")
            
            # 发送邮件通知
            if self.email_config:
                await self._send_email(alert)
            
            # 发送Webhook通知
            if self.webhook_config:
                await self._send_webhook(alert)
            
            # 发送钉钉通知
            if self.dingtalk_config:
                await self._send_dingtalk(alert)
            
            # 发送企业微信通知
            if self.wechat_config:
                await self._send_wechat(alert)
            
        except Exception as e:
            self.logger.error(f"Error sending alert notification: {e}")
            raise
    
    async def _send_email(self, alert: 'Alert'):
        """发送邮件通知"""
        try:
            # 渲染邮件内容
            html_content = self.template.render('email.html', alert=alert)
            
            # 创建邮件
            msg = MIMEMultipart()
            msg['Subject'] = f"[{alert.rule.severity.upper()}] {alert.rule.name}"
            msg['From'] = self.email_config['username']
            msg['To'] = ', '.join(self.email_config['recipients'])
            
            # 添加HTML内容
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # 发送邮件
            await aiosmtplib.send(
                msg,
                hostname=self.email_config['host'],
                port=self.email_config['port'],
                username=self.email_config['username'],
                password=self.email_config['password'],
                use_tls=self.email_config['use_tls']
            )
            
            self.logger.info(f"Email alert sent: {alert.rule.name}")
            
        except Exception as e:
            self.logger.error(f"Error sending email alert: {e}")
            raise
    
    async def _send_webhook(self, alert: 'Alert'):
        """发送Webhook通知"""
        try:
            # 准备请求数据
            data = {
                'alert': {
                    'name': alert.rule.name,
                    'description': alert.rule.description,
                    'metric': alert.rule.metric,
                    'value': alert.value,
                    'threshold': alert.rule.threshold,
                    'operator': alert.rule.operator,
                    'severity': alert.rule.severity,
                    'status': alert.status,
                    'timestamp': alert.timestamp.isoformat()
                }
            }
            
            # 发送请求
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_config['url'],
                    json=data,
                    headers=self.webhook_config['headers']
                ) as resp:
                    if resp.status != 200:
                        raise Exception(f"Webhook request failed: {resp.status}")
            
            self.logger.info(f"Webhook alert sent: {alert.rule.name}")
            
        except Exception as e:
            self.logger.error(f"Error sending webhook alert: {e}")
            raise
    
    async def _send_dingtalk(self, alert: 'Alert'):
        """发送钉钉通知"""
        try:
            # 准备URL
            url = f"https://oapi.dingtalk.com/robot/send?access_token={self.dingtalk_config['access_token']}"
            
            # 添加签名
            if self.dingtalk_config['secret']:
                timestamp = str(round(time.time() * 1000))
                secret = self.dingtalk_config['secret']
                string_to_sign = f"{timestamp}\n{secret}"
                hmac_code = hmac.new(
                    secret.encode('utf-8'),
                    string_to_sign.encode('utf-8'),
                    digestmod=hashlib.sha256
                ).digest()
                sign = base64.b64encode(hmac_code).decode('utf-8')
                url += f"&timestamp={timestamp}&sign={sign}"
            
            # 渲染消息内容
            content = self.template.render('dingtalk.json', alert=alert)
            data = json.loads(content)
            
            # 发送请求
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as resp:
                    if resp.status != 200:
                        raise Exception(f"DingTalk request failed: {resp.status}")
                    result = await resp.json()
                    if result['errcode'] != 0:
                        raise Exception(f"DingTalk API error: {result['errmsg']}")
            
            self.logger.info(f"DingTalk alert sent: {alert.rule.name}")
            
        except Exception as e:
            self.logger.error(f"Error sending DingTalk alert: {e}")
            raise
    
    async def _get_wechat_token(self):
        """获取企业微信访问令牌"""
        try:
            now = time.time()
            
            # 检查是否需要更新token
            if (self.wechat_config['access_token'] and 
                now < self.wechat_config['token_expires']):
                return self.wechat_config['access_token']
            
            # 获取新token
            url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
            params = {
                'corpid': self.wechat_config['corp_id'],
                'corpsecret': self.wechat_config['corp_secret']
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    if resp.status != 200:
                        raise Exception(f"WeChat request failed: {resp.status}")
                    result = await resp.json()
                    if result['errcode'] != 0:
                        raise Exception(f"WeChat API error: {result['errmsg']}")
                    
                    self.wechat_config['access_token'] = result['access_token']
                    self.wechat_config['token_expires'] = now + result['expires_in'] - 60
                    return result['access_token']
                    
        except Exception as e:
            self.logger.error(f"Error getting WeChat token: {e}")
            raise
    
    async def _send_wechat(self, alert: 'Alert'):
        """发送企业微信通知"""
        try:
            # 获取访问令牌
            access_token = await self._get_wechat_token()
            
            # 准备URL
            url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"
            
            # 渲染消息内容
            content = self.template.render('wechat.json', alert=alert)
            data = json.loads(content)
            data.update({
                'touser': self.wechat_config['to_user'],
                'agentid': self.wechat_config['agent_id'],
                'safe': 0
            })
            
            # 发送请求
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as resp:
                    if resp.status != 200:
                        raise Exception(f"WeChat request failed: {resp.status}")
                    result = await resp.json()
                    if result['errcode'] != 0:
                        raise Exception(f"WeChat API error: {result['errmsg']}")
            
            self.logger.info(f"WeChat alert sent: {alert.rule.name}")
            
        except Exception as e:
            self.logger.error(f"Error sending WeChat alert: {e}")
            raise 