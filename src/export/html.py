"""HTML格式导出实现

该模块实现了HTML格式的导出功能，包括：
1. 单页面导出
2. 多页面导出
3. 资源文件处理
4. 样式优化
"""

import os
import logging
import asyncio
import shutil
from typing import Dict, List, Any, Optional
from pathlib import Path
import aiofiles
import aiohttp
from bs4 import BeautifulSoup
from PIL import Image
from .base import ExportFormat, ExportError

logger = logging.getLogger(__name__)

class HTMLExport(ExportFormat):
    """HTML格式导出"""
    
    def __init__(self, name: str, config: Dict[str, Any], template_dir: Optional[str] = None):
        super().__init__(name, config, template_dir)
        
        # 创建资源目录
        self.resource_dir = Path(config.get('resource_dir', 'resources'))
        self.resource_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载默认样式
        self.default_style = self._load_default_style()
        
        # 创建HTTP会话
        self.session = None
    
    def _load_default_style(self) -> str:
        """加载默认样式"""
        style_file = self.config.get('default_style')
        if not style_file:
            return ''
            
        try:
            style_path = Path(self.template_dir) / style_file
            with open(style_path) as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error loading default style: {e}")
            return ''
    
    async def _ensure_session(self):
        """确保HTTP会话存在"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
    
    async def _download_resource(
        self,
        url: str,
        resource_type: str,
        output_dir: Path
    ) -> Optional[str]:
        """下载资源文件"""
        try:
            await self._ensure_session()
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.error(f"Failed to download resource: {url}")
                    return None
                    
                # 生成文件名
                ext = url.split('.')[-1].lower()
                filename = f"{hash(url)}.{ext}"
                filepath = output_dir / resource_type / filename
                
                # 创建目录
                filepath.parent.mkdir(parents=True, exist_ok=True)
                
                # 保存文件
                data = await response.read()
                async with aiofiles.open(filepath, 'wb') as f:
                    await f.write(data)
                
                # 如果是图片，进行优化
                if resource_type == 'images':
                    await self._optimize_image(filepath)
                
                return f"{resource_type}/{filename}"
                
        except Exception as e:
            logger.error(f"Error downloading resource: {url} - {e}")
            return None
    
    async def _optimize_image(self, filepath: Path):
        """优化图片"""
        try:
            # 获取配置
            quality = self.config.get('image_quality', 85)
            max_size = self.config.get('max_image_size', 1920)
            
            # 打开图片
            with Image.open(filepath) as img:
                # 调整大小
                if img.width > max_size or img.height > max_size:
                    ratio = min(max_size / img.width, max_size / img.height)
                    new_size = (
                        int(img.width * ratio),
                        int(img.height * ratio)
                    )
                    img = img.resize(new_size, Image.LANCZOS)
                
                # 保存优化后的图片
                img.save(filepath, quality=quality, optimize=True)
                
        except Exception as e:
            logger.error(f"Error optimizing image: {filepath} - {e}")
    
    async def _process_content(
        self,
        content: str,
        output_dir: Path
    ) -> str:
        """处理内容"""
        soup = BeautifulSoup(content, 'html.parser')
        
        # 处理图片
        tasks = []
        for img in soup.find_all('img'):
            if not img.get('src'):
                continue
                
            url = img['src']
            if not url.startswith(('http://', 'https://')):
                continue
                
            task = asyncio.create_task(
                self._download_resource(url, 'images', output_dir)
            )
            tasks.append((img, task))
        
        # 等待所有下载完成
        for img, task in tasks:
            try:
                path = await task
                if path:
                    img['src'] = path
            except Exception as e:
                logger.error(f"Error processing image: {e}")
        
        # 处理样式
        style = soup.new_tag('style')
        style.string = self.default_style
        soup.head.append(style)
        
        return str(soup)
    
    async def export(
        self,
        data: Dict[str, Any],
        template_name: str,
        output_path: str,
        options: Optional[Dict] = None
    ):
        """导出内容"""
        try:
            # 获取模板
            template = self.templates.get(template_name)
            if not template:
                raise ExportError(f"Template not found: {template_name}")
            
            # 渲染内容
            content = template.render(**data)
            
            # 创建输出目录
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 处理内容
            content = await self._process_content(content, output_dir)
            
            # 保存文件
            async with aiofiles.open(output_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            
        except Exception as e:
            raise ExportError(f"Export failed: {e}")
    
    async def batch_export(
        self,
        items: List[Dict[str, Any]],
        template_name: str,
        output_dir: str,
        options: Optional[Dict] = None
    ):
        """批量导出"""
        try:
            # 创建输出目录
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 获取并发数
            concurrency = self.config.get('batch_concurrency', 5)
            
            # 创建任务
            tasks = []
            for i, item in enumerate(items):
                output_path = output_dir / f"{i + 1}.html"
                task = self.export(
                    item,
                    template_name,
                    str(output_path),
                    options
                )
                tasks.append(task)
            
            # 分批执行
            for i in range(0, len(tasks), concurrency):
                batch = tasks[i:i + concurrency]
                await asyncio.gather(*batch)
            
            # 如果需要，创建索引页
            if self.config.get('create_index', True):
                await self._create_index(items, output_dir)
            
        except Exception as e:
            raise ExportError(f"Batch export failed: {e}")
        
        finally:
            # 关闭会话
            if self.session:
                await self.session.close()
                self.session = None
    
    async def _create_index(
        self,
        items: List[Dict[str, Any]],
        output_dir: Path
    ):
        """创建索引页"""
        try:
            # 获取模板
            template = self.templates.get('index')
            if not template:
                logger.warning("Index template not found")
                return
            
            # 准备数据
            data = {
                'items': [
                    {
                        'title': item.get('title', f'Item {i + 1}'),
                        'path': f"{i + 1}.html"
                    }
                    for i, item in enumerate(items)
                ]
            }
            
            # 渲染内容
            content = template.render(**data)
            
            # 处理内容
            content = await self._process_content(content, output_dir)
            
            # 保存文件
            output_path = output_dir / 'index.html'
            async with aiofiles.open(output_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            
        except Exception as e:
            logger.error(f"Error creating index: {e}") 