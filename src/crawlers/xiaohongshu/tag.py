import logging
from typing import Dict, Any, Optional, List

from .base import XiaohongshuBaseCrawler

logger = logging.getLogger(__name__)

class XiaohongshuTagCrawler(XiaohongshuBaseCrawler):
    """小红书标签爬虫"""
    
    def __init__(self):
        """初始化爬虫"""
        super().__init__()
    
    async def crawl(
        self,
        tag_name: str,
        include_notes: bool = True,
        page: int = 1,
        page_size: int = 20,
        sort: str = 'hot',
        **kwargs
    ) -> List[Dict[str, Any]]:
        """获取标签信息
        
        Args:
            tag_name: 标签名称
            include_notes: 是否包含标签下的笔记
            page: 笔记页码
            page_size: 每页笔记数量
            sort: 排序方式（hot-最热, time-最新）
            **kwargs: 其他参数
            
        Returns:
            标签信息列表（只包含一个元素）
        """
        try:
            # 获取标签基本信息
            tag_data = await self._get_tag_info(tag_name)
            if not tag_data:
                return []
            
            # 获取标签统计信息
            stats_data = await self._get_tag_stats(tag_name)
            if stats_data:
                tag_data.update(stats_data)
            
            # 获取标签下的笔记
            if include_notes:
                notes_data = await self._get_tag_notes(
                    tag_name=tag_name,
                    page=page,
                    page_size=page_size,
                    sort=sort
                )
                if notes_data:
                    tag_data['notes'] = notes_data
            
            return [tag_data]
            
        except Exception as e:
            logger.error(f"Failed to get tag info for '{tag_name}': {str(e)}")
            return []
    
    async def _get_tag_info(self, tag_name: str) -> Optional[Dict[str, Any]]:
        """获取标签基本信息
        
        Args:
            tag_name: 标签名称
            
        Returns:
            标签基本信息
        """
        try:
            data = await self._make_api_request(
                endpoint=f'/sns/web/v1/tag/info',
                params={'tag_name': tag_name}
            )
            
            if data:
                return {
                    'tag_id': data.get('tag_id'),
                    'tag_name': data.get('tag_name'),
                    'desc': data.get('desc'),
                    'cover': data.get('cover'),
                    'type': data.get('type'),
                    'category': data.get('category'),
                    'is_official': data.get('is_official', False)
                }
                
        except Exception as e:
            logger.error(f"Failed to get tag info: {str(e)}")
        
        return None
    
    async def _get_tag_stats(self, tag_name: str) -> Optional[Dict[str, Any]]:
        """获取标签统计信息
        
        Args:
            tag_name: 标签名称
            
        Returns:
            标签统计信息
        """
        try:
            data = await self._make_api_request(
                endpoint=f'/sns/web/v1/tag/stats',
                params={'tag_name': tag_name}
            )
            
            if data:
                return {
                    'notes_count': data.get('notes', 0),
                    'users_count': data.get('users', 0),
                    'views_count': data.get('views', 0),
                    'interaction_count': data.get('interaction', 0)
                }
                
        except Exception as e:
            logger.error(f"Failed to get tag stats: {str(e)}")
        
        return None
    
    async def _get_tag_notes(
        self,
        tag_name: str,
        page: int = 1,
        page_size: int = 20,
        sort: str = 'hot'
    ) -> Optional[List[Dict[str, Any]]]:
        """获取标签下的笔记
        
        Args:
            tag_name: 标签名称
            page: 页码
            page_size: 每页数量
            sort: 排序方式（hot-最热, time-最新）
            
        Returns:
            笔记列表
        """
        try:
            data = await self._make_api_request(
                endpoint=f'/sns/web/v1/tag/notes',
                params={
                    'tag_name': tag_name,
                    'page': page,
                    'page_size': page_size,
                    'sort': sort
                }
            )
            
            if data:
                return data.get('notes', [])
                
        except Exception as e:
            logger.error(f"Failed to get tag notes: {str(e)}")
        
        return None
    
    async def get_related_tags(self, tag_name: str) -> List[Dict[str, Any]]:
        """获取相关标签
        
        Args:
            tag_name: 标签名称
            
        Returns:
            相关标签列表
        """
        try:
            data = await self._make_api_request(
                endpoint=f'/sns/web/v1/tag/related',
                params={'tag_name': tag_name}
            )
            
            if data:
                return data.get('tags', [])
                
        except Exception as e:
            logger.error(f"Failed to get related tags: {str(e)}")
        
        return []
    
    async def get_hot_tags(
        self,
        category: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """获取热门标签
        
        Args:
            category: 标签分类
            limit: 返回数量
            
        Returns:
            热门标签列表
        """
        try:
            params = {'limit': limit}
            if category:
                params['category'] = category
                
            data = await self._make_api_request(
                endpoint=f'/sns/web/v1/tag/hot',
                params=params
            )
            
            if data:
                return data.get('tags', [])
                
        except Exception as e:
            logger.error(f"Failed to get hot tags: {str(e)}")
        
        return []
    
    async def crawl_tags(self, keyword: str) -> List[Dict[str, Any]]:
        """爬取标签列表
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            List[Dict[str, Any]]: 标签列表
        """
        data = await self.request('GET', '/api/sns/web/v1/search/topics', params={'keyword': keyword})
        return data['data']['topics']
    
    async def crawl_tag_detail(self, tag_id: str) -> Dict[str, Any]:
        """爬取标签详情
        
        Args:
            tag_id: 标签ID
            
        Returns:
            Dict[str, Any]: 标签详情
        """
        data = await self.request('GET', f'/api/sns/web/v1/topic/{tag_id}')
        return data['data']
    
    async def crawl_tag_notes(self, tag_id: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """爬取标签下的笔记
        
        Args:
            tag_id: 标签ID
            page: 页码
            page_size: 每页数量
            
        Returns:
            Dict[str, Any]: 笔记列表
        """
        params = {
            'tag_id': tag_id,
            'page': page,
            'page_size': page_size,
            'sort': 'hot'
        }
        
        data = await self.request('GET', '/api/sns/web/v1/topic/notes', params=params)
        return data['data']
    
    async def crawl_tag_users(self, tag_id: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """爬取标签下的用户
        
        Args:
            tag_id: 标签ID
            page: 页码
            page_size: 每页数量
            
        Returns:
            Dict[str, Any]: 用户列表
        """
        params = {
            'tag_id': tag_id,
            'page': page,
            'page_size': page_size,
            'sort': 'hot'
        }
        
        data = await self.request('GET', '/api/sns/web/v1/topic/users', params=params)
        return data['data']
    
    async def crawl_tag_related(self, tag_id: str) -> List[Dict[str, Any]]:
        """爬取相关标签
        
        Args:
            tag_id: 标签ID
            
        Returns:
            List[Dict[str, Any]]: 相关标签列表
        """
        data = await self.request('GET', f'/api/sns/web/v1/topic/{tag_id}/related')
        return data['data']['topics'] 