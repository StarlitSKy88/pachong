"""导出基类

该模块定义了导出功能的基础接口，包括：
1. 导出格式管理
2. 模板管理
3. 导出选项
4. 存储管理
5. 通知管理
"""

import logging
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from abc import ABC, abstractmethod
import aiofiles
import aiohttp
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

class ExportError(Exception):
    """导出错误"""
    pass

class ExportFormat(ABC):
    """导出格式基类"""
    
    def __init__(
        self,
        name: str,
        config: Dict[str, Any],
        template_dir: Optional[str] = None
    ):
        self.name = name
        self.config = config
        self.template_dir = template_dir or 'templates'
        
        # 初始化模板引擎
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # 加载模板
        self.templates = {}
        self._load_templates()
    
    def _load_templates(self):
        """加载模板"""
        if 'templates' not in self.config:
            return
            
        for name, template in self.config['templates'].items():
            try:
                template_file = template['file']
                self.templates[name] = self.env.get_template(template_file)
            except Exception as e:
                logger.error(f"Error loading template {name}: {e}")
    
    @abstractmethod
    async def export(
        self,
        data: Dict[str, Any],
        template_name: str,
        output_path: str,
        options: Optional[Dict] = None
    ):
        """导出内容"""
        pass
    
    @abstractmethod
    async def batch_export(
        self,
        items: List[Dict[str, Any]],
        template_name: str,
        output_dir: str,
        options: Optional[Dict] = None
    ):
        """批量导出"""
        pass

class Storage(ABC):
    """存储基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @abstractmethod
    async def save(self, data: bytes, path: str):
        """保存数据"""
        pass
    
    @abstractmethod
    async def load(self, path: str) -> bytes:
        """加载数据"""
        pass
    
    @abstractmethod
    async def delete(self, path: str):
        """删除数据"""
        pass
    
    @abstractmethod
    async def cleanup(self):
        """清理存储"""
        pass

class LocalStorage(Storage):
    """本地存储"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # 创建存储目录
        self.base_path = Path(config.get('path', 'exports'))
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    async def save(self, data: bytes, path: str):
        """保存数据"""
        file_path = self.base_path / path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(data)
    
    async def load(self, path: str) -> bytes:
        """加载数据"""
        file_path = self.base_path / path
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
            
        async with aiofiles.open(file_path, 'rb') as f:
            return await f.read()
    
    async def delete(self, path: str):
        """删除数据"""
        file_path = self.base_path / path
        
        if file_path.exists():
            file_path.unlink()
    
    async def cleanup(self):
        """清理存储"""
        # 获取清理阈值
        threshold = self.config.get('cleanup_threshold', '8GB')
        threshold_bytes = self._parse_size(threshold)
        
        # 获取清理时间
        age = self.config.get('cleanup_age', '30d')
        age_seconds = self._parse_duration(age)
        
        # 获取当前大小
        total_size = sum(f.stat().st_size for f in self.base_path.rglob('*') if f.is_file())
        
        if total_size < threshold_bytes:
            return
            
        # 清理过期文件
        now = datetime.now().timestamp()
        for file_path in self.base_path.rglob('*'):
            if not file_path.is_file():
                continue
                
            # 检查文件年龄
            mtime = file_path.stat().st_mtime
            if now - mtime > age_seconds:
                file_path.unlink()
    
    def _parse_size(self, size: str) -> int:
        """解析大小字符串"""
        units = {
            'B': 1,
            'KB': 1024,
            'MB': 1024 * 1024,
            'GB': 1024 * 1024 * 1024,
            'TB': 1024 * 1024 * 1024 * 1024
        }
        
        size = size.strip().upper()
        for unit, factor in units.items():
            if size.endswith(unit):
                value = float(size[:-len(unit)])
                return int(value * factor)
        
        return int(size)
    
    def _parse_duration(self, duration: str) -> int:
        """解析时间字符串"""
        units = {
            's': 1,
            'm': 60,
            'h': 60 * 60,
            'd': 24 * 60 * 60,
            'w': 7 * 24 * 60 * 60
        }
        
        duration = duration.strip().lower()
        for unit, factor in units.items():
            if duration.endswith(unit):
                value = float(duration[:-len(unit)])
                return int(value * factor)
        
        return int(duration)

class S3Storage(Storage):
    """S3存储"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        try:
            import boto3
            self.s3 = boto3.client(
                's3',
                endpoint_url=config.get('endpoint'),
                region_name=config.get('region'),
                aws_access_key_id=config.get('access_key'),
                aws_secret_access_key=config.get('secret_key')
            )
        except ImportError:
            logger.error("boto3 not installed")
            raise
    
    async def save(self, data: bytes, path: str):
        """保存数据"""
        key = f"{self.config['prefix']}/{path}".lstrip('/')
        
        try:
            self.s3.put_object(
                Bucket=self.config['bucket'],
                Key=key,
                Body=data
            )
        except Exception as e:
            logger.error(f"Error saving to S3: {e}")
            raise
    
    async def load(self, path: str) -> bytes:
        """加载数据"""
        key = f"{self.config['prefix']}/{path}".lstrip('/')
        
        try:
            response = self.s3.get_object(
                Bucket=self.config['bucket'],
                Key=key
            )
            return response['Body'].read()
        except Exception as e:
            logger.error(f"Error loading from S3: {e}")
            raise
    
    async def delete(self, path: str):
        """删除数据"""
        key = f"{self.config['prefix']}/{path}".lstrip('/')
        
        try:
            self.s3.delete_object(
                Bucket=self.config['bucket'],
                Key=key
            )
        except Exception as e:
            logger.error(f"Error deleting from S3: {e}")
            raise
    
    async def cleanup(self):
        """清理存储"""
        # S3存储不需要清理
        pass

class Notifier:
    """通知管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.env = Environment(
            loader=FileSystemLoader('templates'),
            autoescape=True
        )
    
    async def notify(
        self,
        event: str,
        data: Dict[str, Any],
        channels: Optional[List[str]] = None
    ):
        """发送通知"""
        if not self.config.get('enabled', False):
            return
            
        if event not in self.config.get('events', []):
            return
            
        tasks = []
        for channel, config in self.config.get('channels', {}).items():
            if not config.get('enabled', False):
                continue
                
            if channels and channel not in channels:
                continue
                
            if channel == 'email':
                task = self._send_email(event, data, config)
            elif channel == 'webhook':
                task = self._send_webhook(event, data, config)
            else:
                continue
                
            tasks.append(asyncio.create_task(task))
        
        if tasks:
            await asyncio.gather(*tasks)
    
    async def _send_email(
        self,
        event: str,
        data: Dict[str, Any],
        config: Dict[str, Any]
    ):
        """发送邮件通知"""
        try:
            # 渲染模板
            template = self.env.get_template(config['template'])
            content = template.render(event=event, **data)
            
            # TODO: 实现邮件发送
            logger.info(f"Email notification: {event}")
            
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
    
    async def _send_webhook(
        self,
        event: str,
        data: Dict[str, Any],
        config: Dict[str, Any]
    ):
        """发送Webhook通知"""
        if not config.get('url'):
            return
            
        try:
            payload = {
                'event': event,
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            
            headers = config.get('headers', {})
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    config['url'],
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status not in (200, 201, 202):
                        text = await response.text()
                        raise ExportError(f"Webhook failed: {text}")
                        
            logger.info(f"Webhook notification: {event}")
            
        except Exception as e:
            logger.error(f"Error sending webhook notification: {e}")

class ExportManager:
    """导出管理器"""
    
    def __init__(self, config_file: str = 'config/export.json'):
        # 加载配置
        with open(config_file) as f:
            self.config = json.load(f)
        
        # 初始化格式
        self.formats: Dict[str, ExportFormat] = {}
        
        # 初始化存储
        self.storage = self._init_storage()
        
        # 初始化通知
        self.notifier = Notifier(self.config.get('notification', {}))
    
    def _init_storage(self) -> Storage:
        """初始化存储"""
        storage_config = self.config.get('storage', {})
        
        # 优先使用S3存储
        if storage_config.get('s3', {}).get('enabled', False):
            return S3Storage(storage_config['s3'])
        
        # 默认使用本地存储
        return LocalStorage(storage_config.get('local', {}))
    
    def register_format(self, name: str, format_class: type):
        """注册导出格式"""
        if name not in self.config['formats']:
            raise ValueError(f"Unknown format: {name}")
            
        format_config = self.config['formats'][name]
        if not format_config.get('enabled', False):
            return
            
        self.formats[name] = format_class(
            name=name,
            config=format_config
        )
    
    async def export(
        self,
        data: Dict[str, Any],
        format: str,
        template_name: str,
        output_path: str,
        options: Optional[Dict] = None
    ):
        """导出内容"""
        if format not in self.formats:
            raise ValueError(f"Unsupported format: {format}")
            
        try:
            # 发送开始通知
            await self.notifier.notify('export.start', {
                'format': format,
                'template': template_name,
                'output': output_path
            })
            
            # 执行导出
            await self.formats[format].export(
                data,
                template_name,
                output_path,
                options
            )
            
            # 发送完成通知
            await self.notifier.notify('export.complete', {
                'format': format,
                'template': template_name,
                'output': output_path
            })
            
        except Exception as e:
            # 发送错误通知
            await self.notifier.notify('export.error', {
                'format': format,
                'template': template_name,
                'output': output_path,
                'error': str(e)
            })
            raise
    
    async def batch_export(
        self,
        items: List[Dict[str, Any]],
        format: str,
        template_name: str,
        output_dir: str,
        options: Optional[Dict] = None
    ):
        """批量导出"""
        if format not in self.formats:
            raise ValueError(f"Unsupported format: {format}")
            
        try:
            # 发送开始通知
            await self.notifier.notify('batch.start', {
                'format': format,
                'template': template_name,
                'output_dir': output_dir,
                'count': len(items)
            })
            
            # 执行批量导出
            await self.formats[format].batch_export(
                items,
                template_name,
                output_dir,
                options
            )
            
            # 发送完成通知
            await self.notifier.notify('batch.complete', {
                'format': format,
                'template': template_name,
                'output_dir': output_dir,
                'count': len(items)
            })
            
        except Exception as e:
            # 发送错误通知
            await self.notifier.notify('batch.error', {
                'format': format,
                'template': template_name,
                'output_dir': output_dir,
                'count': len(items),
                'error': str(e)
            })
            raise 