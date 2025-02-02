import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .base import BilibiliBaseCrawler

logger = logging.getLogger(__name__)

class BilibiliDynamicCrawler(BilibiliBaseCrawler):
    """B站动态爬虫"""
    
    def __init__(self):
        """初始化爬虫"""
        super().__init__()
    
    async def crawl(
        self,
        dynamic_id: str = None,
        uid: str = None,
        offset: str = None,
        need_top: bool = False,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """获取动态内容
        
        Args:
            dynamic_id: 动态ID（获取指定动态）
            uid: 用户ID（获取用户动态列表）
            offset: 分页标识
            need_top: 是否需要置顶动态
            **kwargs: 其他参数
            
        Returns:
            动态内容列表
        """
        try:
            if dynamic_id:
                # 获取指定动态
                dynamic_data = await self._get_dynamic_detail(dynamic_id)
                if not dynamic_data:
                    return []
                    
                # 获取动态评论
                comments_data = await self._get_dynamic_comments(dynamic_id)
                if comments_data:
                    dynamic_data['comments'] = comments_data
                
                return [dynamic_data]
            
            elif uid:
                # 获取用户动态列表
                return await self._get_user_dynamics(
                    uid=uid,
                    offset=offset,
                    need_top=need_top
                )
            
            else:
                logger.error("Either dynamic_id or uid must be provided")
                return []
            
        except Exception as e:
            logger.error(f"Failed to get dynamic content: {str(e)}")
            return []
    
    async def _get_dynamic_detail(self, dynamic_id: str) -> Optional[Dict[str, Any]]:
        """获取动态详情
        
        Args:
            dynamic_id: 动态ID
            
        Returns:
            动态详情数据
        """
        try:
            data = await self._make_api_request(
                endpoint=f'/x/polymer/web-dynamic/v1/detail',
                params={'id': dynamic_id}
            )
            
            if data:
                return self._parse_dynamic_item(data.get('item', {}))
                
        except Exception as e:
            logger.error(f"Failed to get dynamic detail: {str(e)}")
        
        return None
    
    async def _get_dynamic_comments(
        self,
        dynamic_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Optional[Dict[str, Any]]:
        """获取动态评论
        
        Args:
            dynamic_id: 动态ID
            page: 页码
            page_size: 每页数量
            
        Returns:
            评论数据
        """
        try:
            data = await self._make_api_request(
                endpoint=f'/x/v2/reply',
                params={
                    'oid': dynamic_id,
                    'type': 17,  # 动态评论类型
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
            logger.error(f"Failed to get dynamic comments: {str(e)}")
        
        return None
    
    async def _get_user_dynamics(
        self,
        uid: str,
        offset: str = None,
        need_top: bool = False
    ) -> List[Dict[str, Any]]:
        """获取用户动态列表
        
        Args:
            uid: 用户ID
            offset: 分页标识
            need_top: 是否需要置顶动态
            
        Returns:
            动态列表
        """
        try:
            params = {
                'host_mid': uid,
                'need_top': 1 if need_top else 0
            }
            if offset:
                params['offset'] = offset
            
            data = await self._make_api_request(
                endpoint=f'/x/polymer/web-dynamic/v1/feed/space',
                params=params
            )
            
            if data:
                return [
                    self._parse_dynamic_item(item)
                    for item in data.get('items', [])
                ]
                
        except Exception as e:
            logger.error(f"Failed to get user dynamics: {str(e)}")
        
        return []
    
    def _parse_dynamic_item(self, item: Dict) -> Dict[str, Any]:
        """解析动态内容
        
        Args:
            item: 原始动态数据
            
        Returns:
            解析后的动态数据
        """
        try:
            # 获取基本信息
            result = {
                'dynamic_id': item.get('id_str'),
                'type': item.get('type'),
                'author': item.get('modules', {}).get('module_author'),
                'publish_time': item.get('modules', {}).get('module_author', {}).get('pub_ts'),
                'description': item.get('modules', {}).get('module_dynamic', {}).get('desc', {}).get('text'),
                'stats': item.get('modules', {}).get('module_stat')
            }
            
            # 获取主要内容
            major = item.get('modules', {}).get('module_dynamic', {}).get('major', {})
            if major:
                major_type = major.get('type')
                if major_type == 'MAJOR_TYPE_ARCHIVE':  # 视频
                    archive = major.get('archive')
                    result['major'] = {
                        'type': 'video',
                        'aid': archive.get('aid'),
                        'bvid': archive.get('bvid'),
                        'title': archive.get('title'),
                        'cover': archive.get('cover'),
                        'duration': archive.get('duration_text')
                    }
                elif major_type == 'MAJOR_TYPE_DRAW':  # 图片
                    draw = major.get('draw')
                    result['major'] = {
                        'type': 'draw',
                        'items': draw.get('items')
                    }
                elif major_type == 'MAJOR_TYPE_ARTICLE':  # 专栏
                    article = major.get('article')
                    result['major'] = {
                        'type': 'article',
                        'id': article.get('id'),
                        'title': article.get('title'),
                        'cover': article.get('covers', [None])[0]
                    }
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to parse dynamic item: {str(e)}")
            return item 