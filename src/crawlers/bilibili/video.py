import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .base import BilibiliBaseCrawler
from ...models.content import Content
from ...models.platform import Platform

logger = logging.getLogger(__name__)

class BilibiliVideoCrawler(BilibiliBaseCrawler):
    """B站视频爬虫"""
    
    def __init__(self):
        """初始化爬虫"""
        super().__init__()
    
    async def crawl(
        self,
        aid: str,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """获取视频信息
        
        Args:
            aid: 视频AV号
            **kwargs: 其他参数
            
        Returns:
            视频信息列表（只包含一个元素）
        """
        try:
            # 获取视频详情
            video_data = await self._get_video_detail(aid)
            if not video_data:
                return []
                
            # 获取视频统计信息
            stat_data = await self._get_video_stat(aid)
            if stat_data:
                video_data['stat'] = stat_data
            
            # 获取视频标签
            tags_data = await self._get_video_tags(aid)
            if tags_data:
                video_data['tags'] = tags_data
            
            # 获取相关视频
            related_data = await self._get_related_videos(aid)
            if related_data:
                video_data['related'] = related_data
            
            return [video_data]
            
        except Exception as e:
            logger.error(f"Failed to get video info for '{aid}': {str(e)}")
            return []
    
    async def _get_video_detail(self, aid: str) -> Optional[Dict[str, Any]]:
        """获取视频详情
        
        Args:
            aid: 视频AV号
            
        Returns:
            视频详情数据
        """
        try:
            data = await self._make_api_request(
                endpoint=f'/x/web-interface/view',
                params={'aid': aid}
            )
            
            if data:
                return {
                    'aid': data.get('aid'),
                    'bvid': data.get('bvid'),
                    'title': data.get('title'),
                    'desc': data.get('desc'),
                    'pic': data.get('pic'),
                    'owner': data.get('owner'),
                    'cid': data.get('cid'),
                    'tid': data.get('tid'),
                    'tname': data.get('tname'),
                    'copyright': data.get('copyright'),
                    'pubdate': data.get('pubdate'),
                    'ctime': data.get('ctime'),
                    'duration': data.get('duration'),
                    'dimension': data.get('dimension'),
                    'pages': data.get('pages', [])
                }
                
        except Exception as e:
            logger.error(f"Failed to get video detail: {str(e)}")
        
        return None
    
    async def _get_video_stat(self, aid: str) -> Optional[Dict[str, Any]]:
        """获取视频统计信息
        
        Args:
            aid: 视频AV号
            
        Returns:
            视频统计信息
        """
        try:
            data = await self._make_api_request(
                endpoint=f'/x/web-interface/archive/stat',
                params={'aid': aid}
            )
            
            if data:
                return {
                    'view': data.get('view', 0),
                    'danmaku': data.get('danmaku', 0),
                    'reply': data.get('reply', 0),
                    'favorite': data.get('favorite', 0),
                    'coin': data.get('coin', 0),
                    'share': data.get('share', 0),
                    'like': data.get('like', 0)
                }
                
        except Exception as e:
            logger.error(f"Failed to get video stat: {str(e)}")
        
        return None
    
    async def _get_video_tags(self, aid: str) -> Optional[List[Dict[str, Any]]]:
        """获取视频标签
        
        Args:
            aid: 视频AV号
            
        Returns:
            视频标签列表
        """
        try:
            data = await self._make_api_request(
                endpoint=f'/x/tag/archive/tags',
                params={'aid': aid}
            )
            
            if data:
                return [
                    {
                        'tag_id': tag.get('tag_id'),
                        'tag_name': tag.get('tag_name'),
                        'type': tag.get('type'),
                        'count': tag.get('count', {
                            'use': tag.get('use', 0),
                            'atten': tag.get('atten', 0)
                        })
                    }
                    for tag in data
                ]
                
        except Exception as e:
            logger.error(f"Failed to get video tags: {str(e)}")
        
        return None
    
    async def _get_related_videos(self, aid: str) -> Optional[List[Dict[str, Any]]]:
        """获取相关视频
        
        Args:
            aid: 视频AV号
            
        Returns:
            相关视频列表
        """
        try:
            data = await self._make_api_request(
                endpoint=f'/x/web-interface/archive/related',
                params={'aid': aid}
            )
            
            if data:
                return data
                
        except Exception as e:
            logger.error(f"Failed to get related videos: {str(e)}")
        
        return None
    
    async def get_video_parts(
        self,
        aid: str,
        cid: str
    ) -> Optional[List[Dict[str, Any]]]:
        """获取视频分P信息
        
        Args:
            aid: 视频AV号
            cid: 视频CID
            
        Returns:
            视频分P列表
        """
        try:
            data = await self._make_api_request(
                endpoint=f'/x/player/pagelist',
                params={
                    'aid': aid,
                    'cid': cid
                }
            )
            
            if data:
                return data
                
        except Exception as e:
            logger.error(f"Failed to get video parts: {str(e)}")
        
        return None
    
    async def get_video_playurl(
        self,
        aid: str,
        cid: str,
        qn: int = 64
    ) -> Optional[Dict[str, Any]]:
        """获取视频播放地址
        
        Args:
            aid: 视频AV号
            cid: 视频CID
            qn: 清晰度等级（16-流畅, 32-清晰, 64-高清, 80-超清）
            
        Returns:
            视频播放信息
        """
        try:
            data = await self._make_api_request(
                endpoint=f'/x/player/playurl',
                params={
                    'avid': aid,
                    'cid': cid,
                    'qn': qn,
                    'fnval': 16
                }
            )
            
            if data:
                return data
                
        except Exception as e:
            logger.error(f"Failed to get video playurl: {str(e)}")
        
        return None
    
    async def crawl_video(self, bvid: str, platform: Platform) -> Content:
        """爬取视频详情
        
        Args:
            bvid: 视频BV号
            platform: 平台信息
            
        Returns:
            Content: 内容对象
        """
        data = await self.request('GET', f'/x/web-interface/view', params={'bvid': bvid})
        
        video = data['data']
        content = Content(
            title=video['title'],
            content=video['desc'],
            url=f"https://www.bilibili.com/video/{video['bvid']}",
            platform=platform,
            author={
                'id': str(video['owner']['mid']),
                'name': video['owner']['name'],
                'avatar': video['owner']['face']
            },
            cover=video['pic'],
            views=video['stat']['view'],
            likes=video['stat']['like'],
            comments=video['stat']['reply'],
            shares=video['stat']['share'],
            collects=video['stat']['favorite'],
            coins=video['stat']['coin'],
            publish_time=datetime.fromtimestamp(video['pubdate'])
        )
        return content
    
    async def crawl_video_comments(self, aid: int, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """爬取视频评论
        
        Args:
            aid: 视频AV号
            page: 页码
            page_size: 每页数量
            
        Returns:
            Dict[str, Any]: 评论列表
        """
        params = {
            'type': 1,
            'oid': aid,
            'pn': page,
            'ps': page_size,
            'sort': 2
        }
        
        data = await self.request('GET', '/x/v2/reply', params=params)
        return data['data']
    
    async def crawl_video_related(self, aid: int) -> List[Dict[str, Any]]:
        """爬取相关视频
        
        Args:
            aid: 视频AV号
            
        Returns:
            List[Dict[str, Any]]: 相关视频列表
        """
        data = await self.request('GET', '/x/web-interface/archive/related', params={'aid': aid})
        return data['data']
    
    async def crawl_video_tags(self, aid: int) -> List[Dict[str, Any]]:
        """爬取视频标签
        
        Args:
            aid: 视频AV号
            
        Returns:
            List[Dict[str, Any]]: 标签列表
        """
        data = await self.request('GET', '/x/tag/archive/tags', params={'aid': aid})
        return data['data']
    
    async def crawl_video_stat(self, aid: int) -> Dict[str, Any]:
        """爬取视频统计数据
        
        Args:
            aid: 视频AV号
            
        Returns:
            Dict[str, Any]: 统计数据
        """
        data = await self.request('GET', '/x/web-interface/archive/stat', params={'aid': aid})
        return data['data'] 