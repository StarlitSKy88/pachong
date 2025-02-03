"""B站爬虫实现"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from urllib.parse import urljoin
import aiohttp

from src.models.content import Content
from src.crawlers.base_crawler import BaseCrawler
from src.utils.headers_manager import HeadersManager

logger = logging.getLogger(__name__)

class BiliBiliCrawler(BaseCrawler):
    """B站爬虫 - 免登录版本"""
    
    def __init__(self, proxy_manager=None):
        """初始化爬虫"""
        super().__init__()
        self.proxy_manager = proxy_manager
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'Origin': 'https://www.bilibili.com',
            'Referer': 'https://www.bilibili.com'
        }
        self.base_url = "https://www.bilibili.com"
        self.api_base = "https://api.bilibili.com"
        
    async def get_video_info(self, bvid: str) -> Dict:
        """获取视频信息"""
        url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
        
        async with aiohttp.ClientSession() as session:
            proxy = await self.proxy_manager.get_proxy() if self.proxy_manager else None
            try:
                async with session.get(url, headers=self.headers, proxy=proxy) as response:
                    if response.status == 200:
                        data = await response.json()
                        if proxy:
                            self.proxy_manager.update_proxy_status(proxy, True)
                        return data.get('data', {})
                    else:
                        if proxy:
                            self.proxy_manager.update_proxy_status(proxy, False)
                        return None
            except Exception as e:
                if proxy:
                    self.proxy_manager.update_proxy_status(proxy, False)
                logger.error(f"获取视频信息失败: {str(e)}")
                return None
                
    async def search_videos(self, keyword: str, page: int = 1, page_size: int = 20) -> List[Dict]:
        """搜索视频"""
        url = "https://api.bilibili.com/x/web-interface/search/all/v2"
        params = {
            'keyword': keyword,
            'page': page,
            'pagesize': page_size,
            'search_type': 'video'
        }
        
        async with aiohttp.ClientSession() as session:
            proxy = await self.proxy_manager.get_proxy() if self.proxy_manager else None
            try:
                async with session.get(url, headers=self.headers, params=params, proxy=proxy) as response:
                    if response.status == 200:
                        data = await response.json()
                        if proxy:
                            self.proxy_manager.update_proxy_status(proxy, True)
                        return data.get('data', {}).get('result', [])
                    else:
                        if proxy:
                            self.proxy_manager.update_proxy_status(proxy, False)
                        return []
            except Exception as e:
                if proxy:
                    self.proxy_manager.update_proxy_status(proxy, False)
                logger.error(f"搜索视频失败: {str(e)}")
                return []
                
    async def get_user_videos(self, mid: str, page: int = 1, page_size: int = 30) -> List[Dict]:
        """获取用户视频列表"""
        url = f"https://api.bilibili.com/x/space/arc/search"
        params = {
            'mid': mid,
            'ps': page_size,
            'pn': page,
            'order': 'pubdate'
        }
        
        async with aiohttp.ClientSession() as session:
            proxy = await self.proxy_manager.get_proxy() if self.proxy_manager else None
            try:
                async with session.get(url, headers=self.headers, params=params, proxy=proxy) as response:
                    if response.status == 200:
                        data = await response.json()
                        if proxy:
                            self.proxy_manager.update_proxy_status(proxy, True)
                        return data.get('data', {}).get('list', {}).get('vlist', [])
                    else:
                        if proxy:
                            self.proxy_manager.update_proxy_status(proxy, False)
                        return []
            except Exception as e:
                if proxy:
                    self.proxy_manager.update_proxy_status(proxy, False)
                logger.error(f"获取用户视频失败: {str(e)}")
                return []
        
    async def get_detail(self, url: str) -> Dict[str, Any]:
        """获取视频详情
        
        Args:
            url: 视频URL
            
        Returns:
            视频详情数据
        """
        bvid = url.split("/")[-1]
        api_url = f"{self.api_base}/x/web-interface/view"
        params = {"bvid": bvid}
        
        try:
            response = await self._make_request("GET", api_url, params=params)
            data = await response.json()
            
            if data.get("code") == 0:
                video = data["data"]
                # 确保返回的数据包含所有必要字段
                return {
                    "bvid": video["bvid"],
                    "title": video["title"],
                    "desc": video["desc"],
                    "owner": {
                        "name": video["owner"]["name"],
                        "face": video["owner"].get("face", ""),
                        "mid": str(video["owner"].get("mid", ""))  # 确保mid是字符串
                    },
                    "pubdate": video["pubdate"],
                    "stat": {
                        "view": video["stat"].get("view", 0),
                        "like": video["stat"].get("like", 0),
                        "coin": video["stat"].get("coin", 0),
                        "favorite": video["stat"].get("favorite", 0),
                        "share": video["stat"].get("share", 0),
                        "reply": video["stat"].get("reply", 0)
                    },
                    "pic": video.get("pic", ""),
                    "duration": video.get("duration", 0),
                    "dynamic": video.get("dynamic", ""),
                    "tags": video.get("tags", [])
                }
        except Exception as e:
            logger.error(f"获取详情失败: {e}")
            
        return {}
        
    async def parse(self, data: Dict[str, Any]) -> Optional[Content]:
        """解析视频数据
        
        Args:
            data: 视频数据
            
        Returns:
            Content对象
        """
        try:
            # 解析发布时间
            publish_time = datetime.fromtimestamp(data["pubdate"])
            
            # 解析统计数据
            stat = data.get("stat", {})
            
            # 创建Content对象
            content = Content(
                title=data["title"],
                content=data["desc"],
                author={
                    "name": data["owner"]["name"],
                    "avatar": data["owner"]["face"],
                    "id": data["owner"]["mid"]
                },
                publish_time=publish_time,
                platform="bilibili",
                url=f"https://www.bilibili.com/video/{data['bvid']}",
                images=[data["pic"]],
                video=data.get("video_url", ""),
                views=stat["view"],
                likes=stat["like"],
                coins=stat["coin"],
                shares=stat["share"],
                comments=stat["reply"],
                collects=stat["favorite"]
            )
            
            return content
        except Exception as e:
            logger.error(f"解析数据失败: {e}")
            return None
            
    async def crawl(self, keywords: List[str], limit: int = 10) -> List[Content]:
        """批量爬取内容
        
        Args:
            keywords: 关键词列表
            limit: 每个关键词的最大爬取数量
            
        Returns:
            Content对象列表
        """
        results = []
        
        for keyword in keywords:
            try:
                # 搜索获取URL列表
                urls = await self.search_videos(keyword)
                
                # 限制数量
                urls = urls[:limit]
                
                # 获取详情并解析
                for url in urls:
                    try:
                        detail = await self.get_detail(url)
                        if detail:
                            content = await self.parse(detail)
                            if content:
                                results.append(content)
                    except Exception as e:
                        logger.error(f"爬取{url}失败: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"搜索关键词{keyword}失败: {e}")
                continue
                
        return results 