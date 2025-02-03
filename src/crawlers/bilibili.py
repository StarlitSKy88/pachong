"""B站爬虫模块。"""

import asyncio
import hashlib
import json
import random
import time
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urlencode

from loguru import logger

from src.config.settings import Settings
from src.crawlers.base import BaseCrawler
from src.models.content import Content, ContentType
from src.utils.error_handler import CrawlerError


class BiliBiliCrawler(BaseCrawler):
    """B站爬虫。"""

    def __init__(self, settings: Settings):
        """初始化B站爬虫。

        Args:
            settings: 配置对象
        """
        super().__init__(settings)
        self.base_url = "https://www.bilibili.com"
        self.api_base_url = "https://api.bilibili.com"
        self.search_base_url = "https://api.bilibili.com/x/web-interface/search"
        self.video_base_url = "https://api.bilibili.com/x/web-interface/view"
        self.dynamic_base_url = "https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr"
        self.article_base_url = "https://api.bilibili.com/x/article/viewinfo"

    def _get_default_headers(self) -> Dict[str, str]:
        """获取默认请求头。

        Returns:
            默认请求头
        """
        headers = super()._get_default_headers()
        headers.update({
            "Origin": "https://www.bilibili.com",
            "Referer": "https://www.bilibili.com",
            "Cookie": self.settings.BILIBILI_COOKIE,
        })
        return headers

    async def search_videos(
        self,
        keyword: str,
        page: int = 1,
        page_size: int = 20,
        order: str = "totalrank",
        duration: int = 0,
        tids: Optional[int] = None,
    ) -> Tuple[List[Dict], int]:
        """搜索视频。

        Args:
            keyword: 关键词
            page: 页码
            page_size: 每页数量
            order: 排序方式（totalrank/click/pubdate/dm/stow）
            duration: 时长筛选（0:全部, 1:0-10分钟, 2:10-30分钟, 3:30-60分钟, 4:60分钟以上）
            tids: 分区ID

        Returns:
            视频列表和总数
        """
        try:
            url = f"{self.search_base_url}/all/v2"
            params = {
                "keyword": keyword,
                "page": page,
                "pagesize": page_size,
                "order": order,
                "duration": duration,
                "search_type": "video",
            }
            if tids:
                params["tids"] = tids

            status, content, _ = await self.get(url, params=params)
            if status != 200:
                raise CrawlerError(f"搜索视频失败，状态码: {status}")

            data = self.parse_json(content)
            if data.get("code") != 0:
                raise CrawlerError(f"搜索视频失败，错误: {data.get('message')}")

            result = data.get("data", {})
            videos = result.get("result", [])
            total = result.get("numResults", 0)

            return videos, total
        except Exception as e:
            raise CrawlerError(f"搜索视频失败: {str(e)}")

    async def get_video_detail(self, bvid: str) -> Dict:
        """获取视频详情。

        Args:
            bvid: 视频BV号

        Returns:
            视频详情
        """
        try:
            url = self.video_base_url
            params = {"bvid": bvid}

            status, content, _ = await self.get(url, params=params)
            if status != 200:
                raise CrawlerError(f"获取视频详情失败，状态码: {status}")

            data = self.parse_json(content)
            if data.get("code") != 0:
                raise CrawlerError(f"获取视频详情失败，错误: {data.get('message')}")

            return data.get("data", {})
        except Exception as e:
            raise CrawlerError(f"获取视频详情失败: {str(e)}")

    async def get_user_videos(
        self,
        mid: int,
        page: int = 1,
        page_size: int = 30,
        order: str = "pubdate",
    ) -> Tuple[List[Dict], int]:
        """获取用户视频列表。

        Args:
            mid: 用户ID
            page: 页码
            page_size: 每页数量
            order: 排序方式（pubdate/click/stow）

        Returns:
            视频列表和总数
        """
        try:
            url = f"{self.api_base_url}/x/space/arc/search"
            params = {
                "mid": mid,
                "pn": page,
                "ps": page_size,
                "order": order,
            }

            status, content, _ = await self.get(url, params=params)
            if status != 200:
                raise CrawlerError(f"获取用户视频列表失败，状态码: {status}")

            data = self.parse_json(content)
            if data.get("code") != 0:
                raise CrawlerError(f"获取用户视频列表失败，错误: {data.get('message')}")

            result = data.get("data", {})
            videos = result.get("list", {}).get("vlist", [])
            total = result.get("page", {}).get("count", 0)

            return videos, total
        except Exception as e:
            raise CrawlerError(f"获取用户视频列表失败: {str(e)}")

    async def get_video_comments(
        self,
        aid: int,
        page: int = 1,
        page_size: int = 20,
        order: str = "time",
    ) -> Tuple[List[Dict], int]:
        """获取视频评论列表。

        Args:
            aid: 视频AV号
            page: 页码
            page_size: 每页数量
            order: 排序方式（time/like）

        Returns:
            评论列表和总数
        """
        try:
            url = f"{self.api_base_url}/x/v2/reply"
            params = {
                "type": 1,
                "oid": aid,
                "pn": page,
                "ps": page_size,
                "sort": 2 if order == "like" else 0,
            }

            status, content, _ = await self.get(url, params=params)
            if status != 200:
                raise CrawlerError(f"获取视频评论列表失败，状态码: {status}")

            data = self.parse_json(content)
            if data.get("code") != 0:
                raise CrawlerError(f"获取视频评论列表失败，错误: {data.get('message')}")

            result = data.get("data", {})
            comments = result.get("replies", [])
            total = result.get("page", {}).get("count", 0)

            return comments, total
        except Exception as e:
            raise CrawlerError(f"获取视频评论列表失败: {str(e)}")

    async def get_comment_replies(
        self,
        aid: int,
        root: int,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Dict], int]:
        """获取评论回复列表。

        Args:
            aid: 视频AV号
            root: 根评论ID
            page: 页码
            page_size: 每页数量

        Returns:
            回复列表和总数
        """
        try:
            url = f"{self.api_base_url}/x/v2/reply/reply"
            params = {
                "type": 1,
                "oid": aid,
                "root": root,
                "pn": page,
                "ps": page_size,
            }

            status, content, _ = await self.get(url, params=params)
            if status != 200:
                raise CrawlerError(f"获取评论回复列表失败，状态码: {status}")

            data = self.parse_json(content)
            if data.get("code") != 0:
                raise CrawlerError(f"获取评论回复列表失败，错误: {data.get('message')}")

            result = data.get("data", {})
            replies = result.get("replies", [])
            total = result.get("page", {}).get("count", 0)

            return replies, total
        except Exception as e:
            raise CrawlerError(f"获取评论回复列表失败: {str(e)}")

    async def get_user_dynamics(
        self,
        uid: int,
        offset: str = "0",
        page_size: int = 20,
    ) -> Tuple[List[Dict], str]:
        """获取用户动态列表。

        Args:
            uid: 用户ID
            offset: 偏移值
            page_size: 每页数量

        Returns:
            动态列表和下一页偏移值
        """
        try:
            url = f"{self.dynamic_base_url}/space_history"
            params = {
                "host_uid": uid,
                "offset_dynamic_id": offset,
                "need_top": 0,
                "platform": "web",
            }

            status, content, _ = await self.get(url, params=params)
            if status != 200:
                raise CrawlerError(f"获取用户动态列表失败，状态码: {status}")

            data = self.parse_json(content)
            if data.get("code") != 0:
                raise CrawlerError(f"获取用户动态列表失败，错误: {data.get('message')}")

            result = data.get("data", {})
            dynamics = result.get("cards", [])
            next_offset = result.get("next_offset", "0")

            return dynamics, next_offset
        except Exception as e:
            raise CrawlerError(f"获取用户动态列表失败: {str(e)}")

    def _parse_video(self, video: Dict) -> Content:
        """解析视频数据。

        Args:
            video: 视频数据

        Returns:
            内容对象
        """
        try:
            # 提取视频信息
            videos = [{
                "url": video.get("play_url"),
                "cover": video.get("pic"),
                "duration": video.get("duration"),
            }]

            # 提取统计数据
            stats = {
                "view": video.get("stat", {}).get("view", 0),
                "danmaku": video.get("stat", {}).get("danmaku", 0),
                "reply": video.get("stat", {}).get("reply", 0),
                "favorite": video.get("stat", {}).get("favorite", 0),
                "coin": video.get("stat", {}).get("coin", 0),
                "share": video.get("stat", {}).get("share", 0),
                "like": video.get("stat", {}).get("like", 0),
            }

            # 提取时间
            publish_time = None
            if "pubdate" in video:
                publish_time = datetime.fromtimestamp(video["pubdate"])

            # 创建内容对象
            content = Content(
                title=video.get("title", ""),
                content=video.get("desc", ""),
                summary=video.get("desc", "")[:500] if video.get("desc") else None,
                content_type=ContentType.VIDEO,
                platform_id=2,  # B站平台ID
                url=f"https://www.bilibili.com/video/{video.get('bvid')}",
                author=video.get("owner", {}).get("name"),
                publish_time=publish_time,
                cover_image=video.get("pic"),
                videos=videos,
                metadata={
                    "bvid": video.get("bvid"),
                    "aid": video.get("aid"),
                    "cid": video.get("cid"),
                    "tid": video.get("tid"),
                    "tname": video.get("tname"),
                    "copyright": video.get("copyright"),
                    "duration": video.get("duration"),
                },
                stats=stats,
                keywords=video.get("keywords", []),
                categories=[video.get("tname")] if video.get("tname") else [],
                language="zh",
                word_count=len(video.get("desc", "")),
                read_time=video.get("duration", 0),
                is_original=video.get("copyright") == 1,
            )

            return content
        except Exception as e:
            raise CrawlerError(f"解析视频数据失败: {str(e)}")

    async def start(self) -> None:
        """启动爬虫。"""
        pass

    async def parse(self, response: str, url: str) -> Any:
        """解析响应。

        Args:
            response: 响应内容
            url: 请求URL

        Returns:
            解析结果
        """
        pass 