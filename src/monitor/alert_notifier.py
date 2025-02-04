"""告警通知模块

该模块负责告警通知的发送，包括：
1. 通知渠道管理
2. 通知模板管理
3. 通知发送记录
4. 通知重试机制
"""

import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import aiohttp
import jinja2

from .alert_rule import AlertRule, AlertStatus, AlertSeverity

logger = logging.getLogger(__name__)

class NotifyChannel(str, Enum):
    """通知渠道"""
    EMAIL = "email"
    DINGTALK = "dingtalk"
    WECHAT = "wechat"
    SMS = "sms"
    WEBHOOK = "webhook"

@dataclass
class NotifyTemplate:
    """通知模板"""
    name: str
    channel: str
    title_template: str
    content_template: str
    enabled: bool = True

@dataclass
class NotifyConfig:
    """通知配置"""
    channel: str
    config: Dict[str, Any]
    enabled: bool = True
    retry_count: int = 3
    retry_interval: int = 60
    timeout: int = 10

@dataclass
class NotifyRecord:
    """通知记录"""
    id: str
    alert_id: str
    channel: str
    title: str
    content: str
    timestamp: datetime
    status: str
    error: Optional[str] = None
    retry_count: int = 0

class AlertNotifier:
    """告警通知器"""
    
    def __init__(self):
        self.logger = logging.getLogger('AlertNotifier')
        
        # 通知配置
        self.configs: Dict[str, NotifyConfig] = {}
        
        # 通知模板
        self.templates: Dict[str, NotifyTemplate] = {}
        
        # 通知记录
        self.records: List[NotifyRecord] = []
        
        # 通知处理器
        self.handlers: Dict[str, Callable] = {
            NotifyChannel.EMAIL: self._send_email,
            NotifyChannel.DINGTALK: self._send_dingtalk,
            NotifyChannel.WECHAT: self._send_wechat,
            NotifyChannel.SMS: self._send_sms,
            NotifyChannel.WEBHOOK: self._send_webhook
        }
        
        # 模板引擎
        self.jinja_env = jinja2.Environment(
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    def add_config(self, channel: str, config: Dict[str, Any]):
        """添加通知配置"""
        self.configs[channel] = NotifyConfig(
            channel=channel,
            config=config
        )
    
    def add_template(
        self,
        name: str,
        channel: str,
        title_template: str,
        content_template: str
    ):
        """添加通知模板"""
        self.templates[name] = NotifyTemplate(
            name=name,
            channel=channel,
            title_template=title_template,
            content_template=content_template
        )
    
    async def notify(
        self,
        alert_id: str,
        rule: AlertRule,
        value: float,
        template_name: Optional[str] = None,
        channels: Optional[List[str]] = None
    ):
        """发送告警通知"""
        # 获取模板
        template = None
        if template_name:
            template = self.templates.get(template_name)
        
        # 准备通知数据
        data = {
            'alert_id': alert_id,
            'rule_name': rule.name,
            'rule_group': rule.group.name if rule.group else '',
            'metric': rule.metric,
            'value': value,
            'threshold': rule.threshold,
            'operator': rule.operator,
            'severity': rule.severity,
            'description': rule.description,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 发送通知
        tasks = []
        for channel in (channels or self.configs.keys()):
            if channel not in self.configs:
                continue
                
            config = self.configs[channel]
            if not config.enabled:
                continue
                
            # 渲染模板
            if template and template.channel == channel:
                title = self._render_template(template.title_template, data)
                content = self._render_template(template.content_template, data)
            else:
                title = f"[{rule.severity}] {rule.name}"
                content = rule.format_message(value)
            
            # 创建通知记录
            record = NotifyRecord(
                id=f"{alert_id}_{channel}_{len(self.records)}",
                alert_id=alert_id,
                channel=channel,
                title=title,
                content=content,
                timestamp=datetime.now(),
                status='pending'
            )
            self.records.append(record)
            
            # 发送通知
            task = asyncio.create_task(
                self._send_notify(config, record)
            )
            tasks.append(task)
        
        # 等待所有通知发送完成
        if tasks:
            await asyncio.gather(*tasks)
    
    def get_records(
        self,
        alert_id: Optional[str] = None,
        channel: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[NotifyRecord]:
        """查询通知记录"""
        records = self.records
        
        if alert_id:
            records = [r for r in records if r.alert_id == alert_id]
        if channel:
            records = [r for r in records if r.channel == channel]
        if start_time:
            records = [r for r in records if r.timestamp >= start_time]
        if end_time:
            records = [r for r in records if r.timestamp <= end_time]
        if status:
            records = [r for r in records if r.status == status]
            
        return sorted(
            records,
            key=lambda x: x.timestamp,
            reverse=True
        )[offset:offset+limit]
    
    async def _send_notify(
        self,
        config: NotifyConfig,
        record: NotifyRecord
    ):
        """发送通知"""
        handler = self.handlers.get(config.channel)
        if not handler:
            record.status = 'failed'
            record.error = f"Unsupported channel: {config.channel}"
            return
        
        # 重试发送
        for i in range(config.retry_count):
            try:
                await handler(config, record)
                record.status = 'success'
                return
            except Exception as e:
                record.status = 'failed'
                record.error = str(e)
                record.retry_count += 1
                
                if i < config.retry_count - 1:
                    await asyncio.sleep(config.retry_interval)
    
    def _render_template(self, template_str: str, data: Dict[str, Any]) -> str:
        """渲染模板"""
        try:
            template = self.jinja_env.from_string(template_str)
            return template.render(**data)
        except Exception as e:
            self.logger.error(f"Error rendering template: {e}")
            return template_str
    
    async def _send_email(self, config: NotifyConfig, record: NotifyRecord):
        """发送邮件通知"""
        # TODO: 实现邮件发送
        pass
    
    async def _send_dingtalk(self, config: NotifyConfig, record: NotifyRecord):
        """发送钉钉通知"""
        webhook_url = config.config.get('webhook_url')
        if not webhook_url:
            raise ValueError("Missing webhook_url in dingtalk config")
            
        async with aiohttp.ClientSession() as session:
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "title": record.title,
                    "text": record.content
                }
            }
            
            async with session.post(
                webhook_url,
                json=data,
                timeout=config.timeout
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise ValueError(f"Failed to send dingtalk: {text}")
    
    async def _send_wechat(self, config: NotifyConfig, record: NotifyRecord):
        """发送企业微信通知"""
        webhook_url = config.config.get('webhook_url')
        if not webhook_url:
            raise ValueError("Missing webhook_url in wechat config")
            
        async with aiohttp.ClientSession() as session:
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "content": f"### {record.title}\n{record.content}"
                }
            }
            
            async with session.post(
                webhook_url,
                json=data,
                timeout=config.timeout
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise ValueError(f"Failed to send wechat: {text}")
    
    async def _send_sms(self, config: NotifyConfig, record: NotifyRecord):
        """发送短信通知"""
        # TODO: 实现短信发送
        pass
    
    async def _send_webhook(self, config: NotifyConfig, record: NotifyRecord):
        """发送Webhook通知"""
        webhook_url = config.config.get('webhook_url')
        if not webhook_url:
            raise ValueError("Missing webhook_url in webhook config")
            
        async with aiohttp.ClientSession() as session:
            data = {
                "alert_id": record.alert_id,
                "title": record.title,
                "content": record.content,
                "timestamp": record.timestamp.isoformat()
            }
            
            headers = config.config.get('headers', {})
            
            async with session.post(
                webhook_url,
                json=data,
                headers=headers,
                timeout=config.timeout
            ) as resp:
                if resp.status not in (200, 201, 202):
                    text = await resp.text()
                    raise ValueError(f"Failed to send webhook: {text}") 