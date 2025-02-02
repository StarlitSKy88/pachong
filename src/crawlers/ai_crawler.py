"""AI辅助的爬虫基类"""

import os
import json
import logging
import aiohttp
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from abc import ABC, abstractmethod

from ..models.content import Content
from ..models.platform import Platform
from ..utils.logger import get_logger
from .base import BaseCrawler

logger = logging.getLogger(__name__)

class AICrawler(BaseCrawler):
    """AI辅助的爬虫基类"""
    
    def __init__(self, config: dict = None):
        """初始化
        
        Args:
            config: 配置
        """
        super().__init__(config)
        self.api_key = os.getenv('DEEPSEEK_API_KEY')
        self.api_base = os.getenv('DEEPSEEK_API_BASE', 'https://api.deepseek.com/v1')
        
    async def analyze_page_structure(self, html: str) -> Dict[str, Any]:
        """分析页面结构
        
        Args:
            html: HTML内容
            
        Returns:
            Dict[str, Any]: 页面结构
        """
        prompt = f"""
        分析以下HTML页面的结构，找出主要内容区域的选择器：
        
        {html}
        
        请以JSON格式返回以下信息：
        - title: 标题选择器
        - content: 正文选择器
        - author: 作者选择器
        - publish_time: 发布时间选择器
        - stats: 统计信息选择器（点赞数、评论数等）
        - media: 媒体内容选择器（图片、视频等）
        """
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": "deepseek-chat",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7
                    }
                ) as response:
                    result = await response.json()
                    content = result["choices"][0]["message"]["content"]
                    return json.loads(content)
        except Exception as e:
            logger.error(f"Error analyzing page structure: {e}")
            return {}
            
    async def extract_content(self, html: str, selectors: Dict[str, str]) -> Dict[str, Any]:
        """提取内容
        
        Args:
            html: HTML内容
            selectors: 选择器
            
        Returns:
            Dict[str, Any]: 提取的内容
        """
        prompt = f"""
        从以下HTML页面中提取内容：
        
        {html}
        
        使用以下选择器：
        {json.dumps(selectors, indent=2)}
        
        请以JSON格式返回提取的内容：
        - title: 标题
        - content: 正文
        - author: 作者信息（包含name等）
        - publish_time: 发布时间（ISO格式）
        - stats: 统计信息（包含likes、comments等）
        - media: 媒体内容（包含images、video等）
        """
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": "deepseek-chat",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7
                    }
                ) as response:
                    result = await response.json()
                    content = result["choices"][0]["message"]["content"]
                    return json.loads(content)
        except Exception as e:
            logger.error(f"Error extracting content: {e}")
            return {}
            
    async def evaluate_quality(self, content: Dict[str, Any]) -> float:
        """评估内容质量
        
        Args:
            content: 内容
            
        Returns:
            float: 质量分数（0-1）
        """
        prompt = f"""
        评估以下内容的质量，返回0到1之间的分数：
        
        {json.dumps(content, indent=2)}
        """
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": "deepseek-chat",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7
                    }
                ) as response:
                    result = await response.json()
                    content = result["choices"][0]["message"]["content"]
                    try:
                        score = float(content.strip())
                        return max(0.0, min(1.0, score))
                    except ValueError:
                        logger.error(f"Invalid quality score: {content}")
                        return 0.0
        except Exception as e:
            logger.error(f"Error evaluating quality: {e}")
            return 0.0
            
    async def get_detail(self, url: str) -> Dict[str, Any]:
        """获取详情数据
        
        Args:
            url: 目标URL
            
        Returns:
            Dict[str, Any]: 详情数据
        """
        try:
            # 获取HTML
            html = await self.get_html(url)
            if not html:
                return {}
                
            # 分析页面结构
            selectors = await self.analyze_page_structure(html)
            if not selectors:
                return {}
                
            # 提取内容
            data = await self.extract_content(html, selectors)
            if not data:
                return {}
                
            # 评估质量
            quality = await self.evaluate_quality(data)
            if quality < 0.6:  # 质量阈值
                logger.info(f"Content quality too low: {quality}")
                return {}
                
            return data
            
        except Exception as e:
            logger.error(f"Error getting detail from {url}: {e}")
            return {}
            
    async def crawl_with_ai(self, url: str) -> Optional[Content]:
        """使用AI辅助爬取
        
        Args:
            url: 目标URL
            
        Returns:
            Optional[Content]: 爬取的内容
        """
        try:
            # 获取详情数据
            data = await self.get_detail(url)
            if not data:
                return None
                
            # 解析内容
            return await self.parse(data)
            
        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")
            return None
            
    async def get_html(self, url: str) -> Optional[str]:
        """获取页面HTML内容
        
        Args:
            url: 目标URL
            
        Returns:
            HTML内容
        """
        try:
            response = await self.request(url)
            if response and hasattr(response, 'text'):
                return await response.text()
            return None
        except Exception as e:
            logger.error(f"Error getting HTML from {url}: {str(e)}")
            return None
            
    @abstractmethod
    async def search(self, keyword: str, time_range: str = '24h') -> List[str]:
        """搜索内容
        
        Args:
            keyword: 搜索关键词
            time_range: 时间范围
            
        Returns:
            URL列表
        """
        pass
        
    async def crawl(self, keywords: List[str], limit: int = 10) -> List[Content]:
        """批量爬取
        
        Args:
            keywords: 关键词列表
            limit: 每个关键词的爬取数量限制
            
        Returns:
            List[Content]: 爬取的内容列表
        """
        results = []
        for keyword in keywords:
            urls = await self.search(keyword)
            if not urls:
                continue
                
            for url in urls[:limit]:
                try:
                    content = await self.crawl_with_ai(url)
                    if content:
                        results.append(content)
                        if len(results) >= limit:
                            return results
                except Exception as e:
                    logger.error(f"Error crawling {url}: {e}")
                    continue
                    
        return results 