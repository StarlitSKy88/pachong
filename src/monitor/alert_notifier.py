from typing import Dict, List, Any, Optional
import json
import logging
import smtplib
import aiohttp
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from jinja2 import Template, Environment, FileSystemLoader
from pathlib import Path
from .alert_engine import Alert, AlertRule

class AlertTemplate:
    """告警通知模板"""
    
    def __init__(self, template_dir: str = None):
        self.template_dir = template_dir or str(Path(__file__).parent / 'templates')
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )
        self._load_default_templates()
    
    def _load_default_templates(self):
        """加载默认模板"""
        # 创建模板目录
        template_dir = Path(self.template_dir)
        template_dir.mkdir(parents=True, exist_ok=True)
        
        # 邮件模板
        email_template = """
{% macro render_alert(alert) %}
<div style="margin-bottom: 20px; padding: 15px; border-radius: 5px; background-color: {{ severity_colors[alert.rule.severity] }};">
    <h3 style="color: white; margin: 0;">{{ alert.rule.name }}</h3>
    <div style="background-color: white; margin-top: 10px; padding: 15px; border-radius: 3px;">
        <p><strong>告警级别:</strong> {{ alert.rule.severity }}</p>
        <p><strong>告警描述:</strong> {{ alert.rule.description }}</p>
        <p><strong>触发时间:</strong> {{ alert.timestamp.strftime('%Y-%m-%d %H:%M:%S') }}</p>
        <p><strong>触发值:</strong> {{ alert.value }}</p>
        <p><strong>阈值:</strong> {{ alert.rule.operator }} {{ alert.rule.threshold }}</p>
        {% if alert.rule.group %}
        <p><strong>规则组:</strong> {{ alert.rule.group.name }}</p>
        {% endif %}
        {% if alert.status == 'recovered' %}
        <p style="color: #27ae60;"><strong>状态:</strong> 已恢复</p>
        {% endif %}
    </div>
</div>
{% endmacro %}

<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>监控告警通知</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px;">
    <h2 style="color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 10px;">监控系统告警通知</h2>
    
    {% if summary %}
    <div style="margin: 20px 0; padding: 15px; background-color: #f8f9fa; border-radius: 5px;">
        <h3 style="margin-top: 0;">告警概要</h3>
        <p><strong>总告警数:</strong> {{ alerts|length }}</p>
        <p><strong>告警级别分布:</strong></p>
        <ul>
            {% for severity, count in summary.severity_counts.items() %}
            <li>{{ severity }}: {{ count }}</li>
            {% endfor %}
        </ul>
    </div>
    {% endif %}
    
    {% for alert in alerts %}
        {{ render_alert(alert) }}
    {% endfor %}
    
    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; color: #666; font-size: 12px;">
        <p>此邮件由监控系统自动发送，请勿回复。</p>
        <p>发送时间: {{ now.strftime('%Y-%m-%d %H:%M:%S') }}</p>
    </div>
</body>
</html>
"""
        
        # 钉钉模板
        dingtalk_template = """
# 监控系统告警通知

{% for alert in alerts %}
## {{ alert.rule.name }}

**告警级别:** {{ alert.rule.severity }}  
**告警描述:** {{ alert.rule.description }}  
**触发时间:** {{ alert.timestamp.strftime('%Y-%m-%d %H:%M:%S') }}  
**触发值:** {{ alert.value }}  
**阈值:** {{ alert.rule.operator }} {{ alert.rule.threshold }}  
{% if alert.rule.group %}
**规则组:** {{ alert.rule.group.name }}  
{% endif %}
{% if alert.status == 'recovered' %}
**状态:** 已恢复  
{% endif %}

{% endfor %}

{% if summary %}
## 告警概要

**总告警数:** {{ alerts|length }}  
**告警级别分布:**  
{% for severity, count in summary.severity_counts.items() %}
- {{ severity }}: {{ count }}  
{% endfor %}
{% endif %}

> 发送时间: {{ now.strftime('%Y-%m-%d %H:%M:%S') }}
"""
        
        # 企业微信模板
        wechat_template = """
# 监控系统告警通知

{% for alert in alerts %}
## {{ alert.rule.name }}

告警级别: <font color="{{ severity_colors[alert.rule.severity] }}">{{ alert.rule.severity }}</font>
告警描述: {{ alert.rule.description }}
触发时间: {{ alert.timestamp.strftime('%Y-%m-%d %H:%M:%S') }}
触发值: {{ alert.value }}
阈值: {{ alert.rule.operator }} {{ alert.rule.threshold }}
{% if alert.rule.group %}
规则组: {{ alert.rule.group.name }}
{% endif %}
{% if alert.status == 'recovered' %}
状态: <font color="#27ae60">已恢复</font>
{% endif %}

{% endfor %}

{% if summary %}
## 告警概要

总告警数: {{ alerts|length }}
告警级别分布:
{% for severity, count in summary.severity_counts.items() %}
- {{ severity }}: {{ count }}
{% endfor %}
{% endif %}

> 发送时间: {{ now.strftime('%Y-%m-%d %H:%M:%S') }}
"""
        
        # 保存默认模板
        templates = {
            'email.html': email_template,
            'dingtalk.md': dingtalk_template,
            'wechat.md': wechat_template
        }
        
        for name, content in templates.items():
            template_file = template_dir / name
            if not template_file.exists():
                template_file.write_text(content, encoding='utf-8')
    
    def render(self, template_name: str, **kwargs) -> str:
        """渲染模板"""
        template = self.env.get_template(template_name)
        return template.render(
            severity_colors={
                'info': '#3498db',
                'warning': '#f1c40f',
                'error': '#e74c3c',
                'critical': '#c0392b'
            },
            now=datetime.now(),
            **kwargs
        )

class AlertNotifier:
    """告警通知器"""
    
    def __init__(self, template_dir: str = None):
        self.logger = logging.getLogger('AlertNotifier')
        self.email_config: Optional[Dict] = None
        self.webhook_config: Optional[Dict] = None
        self.dingtalk_config: Optional[Dict] = None
        self.wechat_config: Optional[Dict] = None
        self.template = AlertTemplate(template_dir)
    
    def configure_email(self, host: str, port: int, username: str, password: str,
                       use_tls: bool = True, recipients: List[str] = None):
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
    
    def configure_wechat(self, corp_id: str, corp_secret: str, agent_id: str,
                        to_user: str = '@all'):
        """配置企业微信通知"""
        self.wechat_config = {
            'corp_id': corp_id,
            'corp_secret': corp_secret,
            'agent_id': agent_id,
            'to_user': to_user
        }
        self.logger.info("WeChat notification configured")
    
    def _get_alert_summary(self, alerts: List[Alert]) -> Dict:
        """获取告警概要"""
        severity_counts = {}
        for alert in alerts:
            severity = alert.rule.severity
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            'severity_counts': severity_counts
        }
    
    async def send_email(self, alerts: List[Alert]):
        """发送邮件通知"""
        if not self.email_config:
            self.logger.error("Email not configured")
            return
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[监控告警] {len(alerts)}条新告警"
            msg['From'] = self.email_config['username']
            msg['To'] = ', '.join(self.email_config['recipients'])
            
            # 渲染HTML内容
            html_content = self.template.render(
                'email.html',
                alerts=alerts,
                summary=self._get_alert_summary(alerts)
            )
            
            msg.attach(MIMEText(html_content, 'html'))
            
            server = smtplib.SMTP(self.email_config['host'], self.email_config['port'])
            if self.email_config['use_tls']:
                server.starttls()
            server.login(self.email_config['username'], self.email_config['password'])
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"Email alert sent: {len(alerts)} alerts")
            
        except Exception as e:
            self.logger.error(f"Error sending email alert: {str(e)}")
    
    async def send_webhook(self, alerts: List[Alert]):
        """发送Webhook通知"""
        if not self.webhook_config:
            self.logger.error("Webhook not configured")
            return
        
        try:
            data = {
                'alerts': [{
                    'rule_name': alert.rule.name,
                    'severity': alert.rule.severity,
                    'description': alert.rule.description,
                    'timestamp': alert.timestamp.isoformat(),
                    'value': alert.value,
                    'threshold': alert.rule.threshold,
                    'operator': alert.rule.operator,
                    'status': alert.status
                } for alert in alerts],
                'summary': self._get_alert_summary(alerts)
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_config['url'],
                    json=data,
                    headers=self.webhook_config['headers']
                ) as response:
                    if response.status == 200:
                        self.logger.info(f"Webhook alert sent: {len(alerts)} alerts")
                    else:
                        self.logger.error(f"Error sending webhook alert: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Error sending webhook alert: {str(e)}")
    
    async def send_dingtalk(self, alerts: List[Alert]):
        """发送钉钉通知"""
        if not self.dingtalk_config:
            self.logger.error("DingTalk not configured")
            return
        
        try:
            url = f"https://oapi.dingtalk.com/robot/send?access_token={self.dingtalk_config['access_token']}"
            
            # 渲染消息内容
            content = self.template.render(
                'dingtalk.md',
                alerts=alerts,
                summary=self._get_alert_summary(alerts)
            )
            
            data = {
                'msgtype': 'markdown',
                'markdown': {
                    'title': f"监控告警: {len(alerts)}条新告警",
                    'text': content
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        self.logger.info(f"DingTalk alert sent: {len(alerts)} alerts")
                    else:
                        self.logger.error(f"Error sending DingTalk alert: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Error sending DingTalk alert: {str(e)}")
    
    async def send_wechat(self, alerts: List[Alert]):
        """发送企业微信通知"""
        if not self.wechat_config:
            self.logger.error("WeChat not configured")
            return
        
        try:
            # 获取访问令牌
            token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={self.wechat_config['corp_id']}&corpsecret={self.wechat_config['corp_secret']}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(token_url) as response:
                    if response.status != 200:
                        self.logger.error("Error getting WeChat access token")
                        return
                    
                    token_data = await response.json()
                    access_token = token_data.get('access_token')
                    
                    if not access_token:
                        self.logger.error("Invalid WeChat access token")
                        return
                    
                    # 渲染消息内容
                    content = self.template.render(
                        'wechat.md',
                        alerts=alerts,
                        summary=self._get_alert_summary(alerts)
                    )
                    
                    # 发送消息
                    send_url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"
                    
                    data = {
                        'touser': self.wechat_config['to_user'],
                        'msgtype': 'markdown',
                        'agentid': self.wechat_config['agent_id'],
                        'markdown': {
                            'content': content
                        }
                    }
                    
                    async with session.post(send_url, json=data) as send_response:
                        if send_response.status == 200:
                            self.logger.info(f"WeChat alert sent: {len(alerts)} alerts")
                        else:
                            self.logger.error(f"Error sending WeChat alert: {send_response.status}")
                            
        except Exception as e:
            self.logger.error(f"Error sending WeChat alert: {str(e)}")
    
    async def send_all(self, alerts: List[Alert]):
        """发送所有配置的通知"""
        if not alerts:
            return
            
        if self.email_config:
            await self.send_email(alerts)
        
        if self.webhook_config:
            await self.send_webhook(alerts)
        
        if self.dingtalk_config:
            await self.send_dingtalk(alerts)
        
        if self.wechat_config:
            await self.send_wechat(alerts) 