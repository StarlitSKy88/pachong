"""小红书用户爬虫"""

from typing import Dict, Any
from .base import XiaohongshuBaseCrawler

class XiaohongshuUserCrawler(XiaohongshuBaseCrawler):
    """小红书用户爬虫"""
    
    async def crawl_user(self, user_id: str) -> Dict[str, Any]:
        """爬取用户信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 用户信息
        """
        data = await self.request('GET', f'/api/sns/web/v1/user/{user_id}')
        
        user = data['data']['user']
        return {
            'id': user['id'],
            'nickname': user['nickname'],
            'avatar': user['avatar'],
            'desc': user.get('desc', ''),
            'gender': user.get('gender', 0),
            'location': user.get('location', ''),
            'follows': user.get('follows', 0),
            'fans': user.get('fans', 0),
            'notes': user.get('notes', 0),
            'collected': user.get('collected', 0),
            'liked': user.get('liked', 0)
        }
    
    async def crawl_user_notes(self, user_id: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """爬取用户笔记列表
        
        Args:
            user_id: 用户ID
            page: 页码
            page_size: 每页数量
            
        Returns:
            Dict[str, Any]: 笔记列表
        """
        params = {
            'user_id': user_id,
            'page': page,
            'page_size': page_size
        }
        
        data = await self.request('GET', '/api/sns/web/v1/user/notes', params=params)
        return data['data']
    
    async def crawl_user_collects(self, user_id: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """爬取用户收藏列表
        
        Args:
            user_id: 用户ID
            page: 页码
            page_size: 每页数量
            
        Returns:
            Dict[str, Any]: 收藏列表
        """
        params = {
            'user_id': user_id,
            'page': page,
            'page_size': page_size
        }
        
        data = await self.request('GET', '/api/sns/web/v1/user/collects', params=params)
        return data['data']
    
    async def crawl_user_likes(self, user_id: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """爬取用户点赞列表
        
        Args:
            user_id: 用户ID
            page: 页码
            page_size: 每页数量
            
        Returns:
            Dict[str, Any]: 点赞列表
        """
        params = {
            'user_id': user_id,
            'page': page,
            'page_size': page_size
        }
        
        data = await self.request('GET', '/api/sns/web/v1/user/likes', params=params)
        return data['data'] 