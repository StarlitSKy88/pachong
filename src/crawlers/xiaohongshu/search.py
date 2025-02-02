"""小红书搜索爬虫"""

from typing import List, Dict, Any
from datetime import datetime
from .base import XiaohongshuBaseCrawler
from ...models.content import Content
from ...models.platform import Platform

class XiaohongshuSearchCrawler(XiaohongshuBaseCrawler):
    """小红书搜索爬虫"""
    
    async def search(self, keyword: str, platform: Platform, page: int = 1, page_size: int = 20) -> List[Content]:
        """搜索笔记
        
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
            'page_size': page_size,
            'sort': 'general',
            'source': 'web'
        }
        
        data = await self.request('GET', '/api/sns/web/v1/search/notes', params=params)
        
        contents = []
        for note in data['data']['notes']:
            content = Content(
                title=note['title'],
                content=note['desc'],
                url=f"https://www.xiaohongshu.com/explore/{note['id']}",
                platform=platform,
                author={
                    'id': note['user']['id'],
                    'name': note['user']['nickname'],
                    'avatar': note['user']['avatar']
                },
                images=[note['cover']['url']] if note.get('cover') else [],
                likes=note.get('likes', 0),
                collects=note.get('collects', 0),
                comments=note.get('comments', 0),
                publish_time=datetime.fromisoformat(note['time'].replace('Z', '+00:00'))
            )
            contents.append(content)
        
        return contents 