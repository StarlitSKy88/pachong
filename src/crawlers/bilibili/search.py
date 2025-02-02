import logging
from typing import Dict, Any, Optional, List
from urllib.parse import quote
from datetime import datetime

from .base import BilibiliBaseCrawler
from ...models.content import Content
from ...models.platform import Platform

logger = logging.getLogger(__name__)

class BilibiliSearchCrawler(BilibiliBaseCrawler):
    """B站搜索爬虫"""
    
    def __init__(self):
        """初始化爬虫"""
        super().__init__()
    
    async def search(self, keyword: str, platform: Platform, page: int = 1, page_size: int = 20) -> List[Content]:
        """搜索内容
        
        Args:
            keyword: 搜索关键词
            platform: 平台信息
            page: 页码
            page_size: 每页数量
            
        Returns:
            List[Content]: 内容列表
        """
        params = {
            'keyword': keyword,
            'page': page,
            'pagesize': page_size,
            'search_type': 'video',
            'order': 'totalrank'
        }
        
        data = await self.request('GET', '/x/web-interface/search/type', params=params)
        
        contents = []
        for result in data['data']['result']:
            content = Content(
                title=result['title'],
                content=result['description'],
                url=f"https://www.bilibili.com/video/{result['bvid']}",
                platform=platform,
                author={
                    'id': str(result['mid']),
                    'name': result['author'],
                    'avatar': ''
                },
                cover=result['pic'],
                views=result['play'],
                likes=0,  # 搜索结果中没有点赞数
                comments=result['review'],
                shares=0,  # 搜索结果中没有分享数
                collects=result['favorites'],
                publish_time=datetime.fromtimestamp(result['pubdate'])
            )
            contents.append(content)
        
        return contents
    
    async def search_by_type(self, keyword: str, search_type: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """按类型搜索
        
        Args:
            keyword: 搜索关键词
            search_type: 搜索类型（video/article/bangumi/live/user）
            page: 页码
            page_size: 每页数量
            
        Returns:
            Dict[str, Any]: 搜索结果
        """
        params = {
            'keyword': keyword,
            'page': page,
            'pagesize': page_size,
            'search_type': search_type,
            'order': 'totalrank'
        }
        
        data = await self.request('GET', '/x/web-interface/search/type', params=params)
        return data['data']
    
    async def search_suggest(self, keyword: str) -> List[str]:
        """搜索建议
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            List[str]: 建议列表
        """
        data = await self.request('GET', '/x/web-interface/search/suggest', params={'keyword': keyword})
        return [tag['value'] for tag in data['data']['tag']]
    
    async def search_default(self) -> Dict[str, Any]:
        """获取默认搜索
        
        Returns:
            Dict[str, Any]: 默认搜索信息
        """
        data = await self.request('GET', '/x/web-interface/search/default')
        return data['data']
    
    async def search_by_tag(
        self,
        tag: str,
        page: int = 1,
        page_size: int = 20,
        order: str = 'pubdate',
        **kwargs
    ) -> List[Dict[str, Any]]:
        """按标签搜索
        
        Args:
            tag: 标签名称
            page: 页码
            page_size: 每页数量
            order: 排序方式（pubdate-最新发布, click-最多点击, stow-最多收藏）
            **kwargs: 其他参数
            
        Returns:
            搜索结果列表
        """
        # 构建请求参数
        params = {
            'tag_name': tag,
            'page': page,
            'pagesize': page_size,
            'order': order
        }
        
        # 发送搜索请求
        try:
            data = await self._make_api_request(
                endpoint=f'/x/tag/info',
                params=params
            )
            
            if data:
                return data.get('archives', [])
            
        except Exception as e:
            logger.error(f"Tag search failed for tag '{tag}': {str(e)}")
        
        return []
    
    async def search_related_tags(
        self,
        keyword: str,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """搜索相关标签
        
        Args:
            keyword: 搜索关键词
            **kwargs: 其他参数
            
        Returns:
            相关标签列表
        """
        # 构建请求参数
        params = {
            'keyword': keyword
        }
        
        # 发送搜索请求
        try:
            data = await self._make_api_request(
                endpoint=f'/x/tag/similar',
                params=params
            )
            
            if data:
                return data.get('tags', [])
            
        except Exception as e:
            logger.error(f"Related tags search failed for keyword '{keyword}': {str(e)}")
        
        return []
    
    async def search_hot_words(self) -> List[Dict[str, Any]]:
        """获取热搜词
        
        Returns:
            热搜词列表
        """
        try:
            data = await self._make_api_request(
                endpoint=f'/x/web-interface/search/square'
            )
            
            if data:
                trending = data.get('trending', {})
                return trending.get('list', [])
            
        except Exception as e:
            logger.error(f"Hot words search failed: {str(e)}")
        
        return [] 