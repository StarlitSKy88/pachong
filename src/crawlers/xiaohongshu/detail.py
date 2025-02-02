import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .base import XiaohongshuBaseCrawler

logger = logging.getLogger(__name__)

class XiaohongshuDetailCrawler(XiaohongshuBaseCrawler):
    """小红书详情爬虫"""
    
    def __init__(self):
        """初始化爬虫"""
        super().__init__()
    
    async def crawl(
        self,
        note_id: str,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """获取笔记详情
        
        Args:
            note_id: 笔记ID
            **kwargs: 其他参数
            
        Returns:
            笔记详情列表（只包含一个元素）
        """
        try:
            # 获取笔记详情
            note_data = await self._get_note_detail(note_id)
            if not note_data:
                return []
                
            # 获取评论数据
            comments_data = await self._get_note_comments(note_id)
            if comments_data:
                note_data['comments_detail'] = comments_data
            
            # 获取互动数据
            interaction_data = await self._get_note_interaction(note_id)
            if interaction_data:
                note_data.update(interaction_data)
            
            return [note_data]
            
        except Exception as e:
            logger.error(f"Failed to get note detail for '{note_id}': {str(e)}")
            return []
    
    async def _get_note_detail(self, note_id: str) -> Optional[Dict[str, Any]]:
        """获取笔记详情
        
        Args:
            note_id: 笔记ID
            
        Returns:
            笔记详情数据
        """
        try:
            data = await self._make_api_request(
                endpoint=f'/sns/web/v1/feed',
                params={'note_id': note_id}
            )
            
            if data and data.get('items'):
                return data['items'][0]
                
        except Exception as e:
            logger.error(f"Failed to get note detail: {str(e)}")
        
        return None
    
    async def _get_note_comments(
        self,
        note_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Optional[Dict[str, Any]]:
        """获取笔记评论
        
        Args:
            note_id: 笔记ID
            page: 页码
            page_size: 每页数量
            
        Returns:
            评论数据
        """
        try:
            data = await self._make_api_request(
                endpoint=f'/sns/web/v1/comment/list',
                params={
                    'note_id': note_id,
                    'page': page,
                    'page_size': page_size
                }
            )
            
            if data:
                return {
                    'total': data.get('total_count', 0),
                    'comments': data.get('comments', [])
                }
                
        except Exception as e:
            logger.error(f"Failed to get note comments: {str(e)}")
        
        return None
    
    async def _get_note_interaction(self, note_id: str) -> Optional[Dict[str, Any]]:
        """获取笔记互动数据
        
        Args:
            note_id: 笔记ID
            
        Returns:
            互动数据
        """
        try:
            data = await self._make_api_request(
                endpoint=f'/sns/web/v1/note/interaction',
                params={'note_id': note_id}
            )
            
            if data:
                return {
                    'likes': data.get('likes', 0),
                    'comments': data.get('comments', 0),
                    'shares': data.get('shares', 0),
                    'collects': data.get('collects', 0),
                    'views': data.get('views', 0)
                }
                
        except Exception as e:
            logger.error(f"Failed to get note interaction: {str(e)}")
        
        return None
    
    async def parse_content(self, raw_content: Dict) -> Dict[str, Any]:
        """解析内容
        
        Args:
            raw_content: 原始内容数据
            
        Returns:
            解析后的内容
        """
        # 调用父类的解析方法
        content = await super().parse_content(raw_content)
        
        # 添加详情特有的字段
        if 'comments_detail' in raw_content:
            content.meta_info['comments_detail'] = raw_content['comments_detail']
        
        # 处理时间
        if 'time' in raw_content:
            try:
                content.publish_time = datetime.fromtimestamp(raw_content['time'] / 1000)
            except:
                pass
        
        return content 