"""小红书内容处理器"""

import re
import json
import time
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime
from bs4 import BeautifulSoup
from loguru import logger
from .base_processor import BaseProcessor

class XiaoHongShuProcessor(BaseProcessor):
    """小红书内容处理器"""
    
    def __init__(self):
        """初始化处理器"""
        super().__init__()
        self.processed_count = 0
        self.success_count = 0
        self.fail_count = 0
        self.total_process_time = 0.0
        
    async def process(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """处理内容
        
        Args:
            content: 原始内容
            
        Returns:
            处理后的内容
        """
        start_time = time.time()
        self.processed_count += 1
        
        try:
            # 验证内容
            if not await self.validate(content):
                self.logger.warning("Content validation failed")
                self.fail_count += 1
                self.total_process_time += time.time() - start_time
                return content
                
            # 模拟处理延迟
            await asyncio.sleep(0.1)
            
            # 清理内容
            content = await self.clean(content)
            
            # 转换内容
            content = await self.transform(content)
            
            # 丰富内容
            content = await self.enrich(content)
            
            # 更新统计信息
            self.success_count += 1
            self.total_process_time += time.time() - start_time
            
            return content
            
        except Exception as e:
            self.logger.error(f"Content processing failed: {str(e)}")
            self.fail_count += 1
            self.total_process_time += time.time() - start_time
            return content
            
    async def batch_process(self, contents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量处理内容
        
        Args:
            contents: 原始内容列表
            
        Returns:
            处理后的内容列表
        """
        results = []
        for content in contents:
            result = await self.process(content)
            results.append(result)
        return results
        
    async def validate(self, content: Dict[str, Any]) -> bool:
        """验证内容
        
        Args:
            content: 待验证的内容
            
        Returns:
            是否有效
        """
        required_fields = ["id", "title", "content", "created_at", "images", "stats"]
        if not all(field in content for field in required_fields):
            logger.warning("Content validation failed")
            return False
        return True
        
    async def clean(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """清理内容
        
        Args:
            content: 待清理的内容
            
        Returns:
            清理后的内容
        """
        # 保存原始标题用于提取标签
        content['original_title'] = content['title']
        
        # 清理标题中的标签
        content['title'] = re.sub(r'#\w+', '', content['title']).strip()

        # 清理HTML标签
        if isinstance(content['content'], str):
            soup = BeautifulSoup(content['content'], 'html.parser')
            content['content'] = soup.get_text().strip()

        # 清理图片URL
        if 'images' in content:
            content['images'] = [url.strip() for url in content['images'] if url.strip()]

        return content
        
    async def transform(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """转换内容
        
        Args:
            content: 待转换的内容
            
        Returns:
            转换后的内容
        """
        # 转换创建时间为ISO格式
        if isinstance(content.get('created_at'), datetime):
            content['created_at'] = content['created_at'].isoformat()

        # 转换统计数据为整数
        if 'stats' in content:
            for key in ['likes', 'comments', 'shares', 'collects']:
                if key in content['stats']:
                    content['stats'][key] = int(content['stats'][key])

        return content
        
    async def enrich(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """丰富内容
        
        Args:
            content: 待丰富的内容
            
        Returns:
            丰富后的内容
        """
        # 检测内容类型
        if 'images' in content and len(content['images']) > 0:
            content['type'] = 'gallery' if len(content['images']) > 1 else 'image'
        else:
            content['type'] = 'text'

        # 提取标签
        content['tags'] = []
        
        # 从原始标题中提取标签
        if 'title' in content:
            # 如果有原始标题，使用原始标题
            title_text = content.get('original_title', content['title'])
            title_tags = re.findall(r'#(\w+)', title_text)
            content['tags'].extend(title_tags)
        
        # 从内容中提取标签
        if 'content' in content:
            content_tags = re.findall(r'#(\w+)', content['content'])
            content['tags'].extend(content_tags)
        
        # 去重并保持顺序
        seen = set()
        content['tags'] = [tag for tag in content['tags'] if not (tag in seen or seen.add(tag))]

        # 添加处理时间
        content['processed_at'] = datetime.now().isoformat()
        
        return content
        
    def get_stats(self) -> Dict[str, Any]:
        """获取处理器统计信息
        
        Returns:
            统计信息
        """
        avg_time = self.total_process_time / max(self.processed_count, 1)
        return {
            "processed_count": self.processed_count,
            "success_count": self.success_count,
            "fail_count": self.fail_count,
            "avg_process_time": avg_time
        } 