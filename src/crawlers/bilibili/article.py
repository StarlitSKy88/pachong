import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .base import BilibiliBaseCrawler

logger = logging.getLogger(__name__)

class BilibiliArticleCrawler(BilibiliBaseCrawler):
    """B站专栏爬虫"""
    
    def __init__(self):
        """初始化爬虫"""
        super().__init__()
    
    async def crawl(
        self,
        article_id: str,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """获取专栏文章
        
        Args:
            article_id: 文章ID
            **kwargs: 其他参数
            
        Returns:
            文章内容列表（只包含一个元素）
        """
        try:
            # 获取文章详情
            article_data = await self._get_article_detail(article_id)
            if not article_data:
                return []
                
            # 获取文章统计信息
            stats_data = await self._get_article_stats(article_id)
            if stats_data:
                article_data['stats'] = stats_data
            
            # 获取文章评论
            comments_data = await self._get_article_comments(article_id)
            if comments_data:
                article_data['comments'] = comments_data
            
            # 获取相关文章
            related_data = await self._get_related_articles(article_id)
            if related_data:
                article_data['related'] = related_data
            
            return [article_data]
            
        except Exception as e:
            logger.error(f"Failed to get article content for '{article_id}': {str(e)}")
            return []
    
    async def _get_article_detail(self, article_id: str) -> Optional[Dict[str, Any]]:
        """获取文章详情
        
        Args:
            article_id: 文章ID
            
        Returns:
            文章详情数据
        """
        try:
            data = await self._make_api_request(
                endpoint=f'/x/article/view',
                params={'id': article_id}
            )
            
            if data:
                return {
                    'id': data.get('id'),
                    'title': data.get('title'),
                    'content': data.get('content'),
                    'summary': data.get('summary'),
                    'banner_url': data.get('banner_url'),
                    'template_id': data.get('template_id'),
                    'category': {
                        'id': data.get('category', {}).get('id'),
                        'parent_id': data.get('category', {}).get('parent_id'),
                        'name': data.get('category', {}).get('name')
                    },
                    'categories': data.get('categories', []),
                    'tags': data.get('tags', []),
                    'author': data.get('author'),
                    'publish_time': data.get('publish_time'),
                    'ctime': data.get('ctime'),
                    'mtime': data.get('mtime'),
                    'words': data.get('words'),
                    'image_urls': data.get('image_urls', []),
                    'origin_image_urls': data.get('origin_image_urls', [])
                }
                
        except Exception as e:
            logger.error(f"Failed to get article detail: {str(e)}")
        
        return None
    
    async def _get_article_stats(self, article_id: str) -> Optional[Dict[str, Any]]:
        """获取文章统计信息
        
        Args:
            article_id: 文章ID
            
        Returns:
            文章统计信息
        """
        try:
            data = await self._make_api_request(
                endpoint=f'/x/article/stats',
                params={'id': article_id}
            )
            
            if data:
                return {
                    'view': data.get('view', 0),
                    'favorite': data.get('favorite', 0),
                    'like': data.get('like', 0),
                    'dislike': data.get('dislike', 0),
                    'reply': data.get('reply', 0),
                    'share': data.get('share', 0),
                    'coin': data.get('coin', 0)
                }
                
        except Exception as e:
            logger.error(f"Failed to get article stats: {str(e)}")
        
        return None
    
    async def _get_article_comments(
        self,
        article_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Optional[Dict[str, Any]]:
        """获取文章评论
        
        Args:
            article_id: 文章ID
            page: 页码
            page_size: 每页数量
            
        Returns:
            评论数据
        """
        try:
            data = await self._make_api_request(
                endpoint=f'/x/v2/reply',
                params={
                    'oid': article_id,
                    'type': 12,  # 专栏评论类型
                    'pn': page,
                    'ps': page_size,
                    'sort': 2  # 按时间倒序
                }
            )
            
            if data:
                return {
                    'page': data.get('page', {}),
                    'replies': data.get('replies', [])
                }
                
        except Exception as e:
            logger.error(f"Failed to get article comments: {str(e)}")
        
        return None
    
    async def _get_related_articles(self, article_id: str) -> Optional[List[Dict[str, Any]]]:
        """获取相关文章
        
        Args:
            article_id: 文章ID
            
        Returns:
            相关文章列表
        """
        try:
            data = await self._make_api_request(
                endpoint=f'/x/article/recommends',
                params={
                    'id': article_id,
                    'from': 'article'
                }
            )
            
            if data:
                return data.get('articles', [])
                
        except Exception as e:
            logger.error(f"Failed to get related articles: {str(e)}")
        
        return None
    
    async def get_articles_by_category(
        self,
        category_id: int,
        page: int = 1,
        page_size: int = 20,
        sort: str = 'publish_time'
    ) -> List[Dict[str, Any]]:
        """获取分类下的文章
        
        Args:
            category_id: 分类ID
            page: 页码
            page_size: 每页数量
            sort: 排序方式（publish_time-发布时间, view-浏览量, fav-收藏数）
            
        Returns:
            文章列表
        """
        try:
            data = await self._make_api_request(
                endpoint=f'/x/article/list',
                params={
                    'category_id': category_id,
                    'page_num': page,
                    'page_size': page_size,
                    'sort': sort
                }
            )
            
            if data:
                return data.get('articles', [])
                
        except Exception as e:
            logger.error(f"Failed to get articles by category: {str(e)}")
        
        return []
    
    async def get_categories(self) -> List[Dict[str, Any]]:
        """获取专栏分类
        
        Returns:
            分类列表
        """
        try:
            data = await self._make_api_request(
                endpoint=f'/x/article/categories'
            )
            
            if data:
                return data.get('categories', [])
                
        except Exception as e:
            logger.error(f"Failed to get categories: {str(e)}")
        
        return [] 