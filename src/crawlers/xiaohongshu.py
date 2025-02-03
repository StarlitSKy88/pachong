"""小红书爬虫模块。"""

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


class XiaoHongShuCrawler(BaseCrawler):
    """小红书爬虫。"""

    def __init__(self, settings: Settings):
        """初始化小红书爬虫。

        Args:
            settings: 配置对象
        """
        super().__init__(settings)
        self.base_url = "https://www.xiaohongshu.com"
        self.api_base_url = "https://edith.xiaohongshu.com"
        self.sign_key = "xhsapi"

    def _get_default_headers(self) -> Dict[str, str]:
        """获取默认请求头。

        Returns:
            默认请求头
        """
        headers = super()._get_default_headers()
        headers.update({
            "Origin": "https://www.xiaohongshu.com",
            "Referer": "https://www.xiaohongshu.com",
            "X-Sign": self._generate_sign(),
            "Authorization": self.settings.XHS_TOKEN,
        })
        return headers

    def _generate_sign(self, data: Optional[Dict] = None) -> str:
        """生成签名。

        Args:
            data: 请求数据

        Returns:
            签名
        """
        timestamp = str(int(time.time() * 1000))
        nonce = "".join(random.choices("abcdef0123456789", k=6))
        
        # 构建签名字符串
        sign_str = f"{self.sign_key}{timestamp}{nonce}"
        if data:
            sign_str += json.dumps(data, separators=(",", ":"))

        # 计算签名
        sign = hashlib.sha256(sign_str.encode()).hexdigest()
        
        return f"{timestamp}.{nonce}.{sign}"

    async def search_notes(
        self,
        keyword: str,
        page: int = 1,
        page_size: int = 20,
        sort: str = "general",
        note_type: str = "all",
    ) -> Tuple[List[Dict], int]:
        """搜索笔记。

        Args:
            keyword: 关键词
            page: 页码
            page_size: 每页数量
            sort: 排序方式（general/hot/time）
            note_type: 笔记类型（all/video/image）

        Returns:
            笔记列表和总数
        """
        try:
            url = f"{self.api_base_url}/api/sns/web/v1/search/notes"
            params = {
                "keyword": keyword,
                "page": page,
                "page_size": page_size,
                "sort": sort,
                "note_type": note_type,
            }

            status, content, _ = await self.get(url, params=params)
            if status != 200:
                raise CrawlerError(f"搜索笔记失败，状态码: {status}")

            data = self.parse_json(content)
            if data.get("code") != 0:
                raise CrawlerError(f"搜索笔记失败，错误: {data.get('msg')}")

            result = data.get("data", {})
            notes = result.get("notes", [])
            total = result.get("total", 0)

            return notes, total
        except Exception as e:
            raise CrawlerError(f"搜索笔记失败: {str(e)}")

    async def get_note_detail(self, note_id: str) -> Dict:
        """获取笔记详情。

        Args:
            note_id: 笔记ID

        Returns:
            笔记详情
        """
        try:
            url = f"{self.api_base_url}/api/sns/web/v1/feed"
            params = {"note_id": note_id}

            status, content, _ = await self.get(url, params=params)
            if status != 200:
                raise CrawlerError(f"获取笔记详情失败，状态码: {status}")

            data = self.parse_json(content)
            if data.get("code") != 0:
                raise CrawlerError(f"获取笔记详情失败，错误: {data.get('msg')}")

            return data.get("data", {})
        except Exception as e:
            raise CrawlerError(f"获取笔记详情失败: {str(e)}")

    async def get_user_notes(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Dict], int]:
        """获取用户笔记列表。

        Args:
            user_id: 用户ID
            page: 页码
            page_size: 每页数量

        Returns:
            笔记列表和总数
        """
        try:
            url = f"{self.api_base_url}/api/sns/web/v1/user/notes"
            params = {
                "user_id": user_id,
                "page": page,
                "page_size": page_size,
            }

            status, content, _ = await self.get(url, params=params)
            if status != 200:
                raise CrawlerError(f"获取用户笔记列表失败，状态码: {status}")

            data = self.parse_json(content)
            if data.get("code") != 0:
                raise CrawlerError(f"获取用户笔记列表失败，错误: {data.get('msg')}")

            result = data.get("data", {})
            notes = result.get("notes", [])
            total = result.get("total", 0)

            return notes, total
        except Exception as e:
            raise CrawlerError(f"获取用户笔记列表失败: {str(e)}")

    async def get_note_comments(
        self,
        note_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Dict], int]:
        """获取笔记评论列表。

        Args:
            note_id: 笔记ID
            page: 页码
            page_size: 每页数量

        Returns:
            评论列表和总数
        """
        try:
            url = f"{self.api_base_url}/api/sns/web/v1/comment/list"
            params = {
                "note_id": note_id,
                "page": page,
                "page_size": page_size,
            }

            status, content, _ = await self.get(url, params=params)
            if status != 200:
                raise CrawlerError(f"获取笔记评论列表失败，状态码: {status}")

            data = self.parse_json(content)
            if data.get("code") != 0:
                raise CrawlerError(f"获取笔记评论列表失败，错误: {data.get('msg')}")

            result = data.get("data", {})
            comments = result.get("comments", [])
            total = result.get("total", 0)

            return comments, total
        except Exception as e:
            raise CrawlerError(f"获取笔记评论列表失败: {str(e)}")

    async def get_comment_replies(
        self,
        note_id: str,
        comment_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Dict], int]:
        """获取评论回复列表。

        Args:
            note_id: 笔记ID
            comment_id: 评论ID
            page: 页码
            page_size: 每页数量

        Returns:
            回复列表和总数
        """
        try:
            url = f"{self.api_base_url}/api/sns/web/v1/comment/sub/list"
            params = {
                "note_id": note_id,
                "comment_id": comment_id,
                "page": page,
                "page_size": page_size,
            }

            status, content, _ = await self.get(url, params=params)
            if status != 200:
                raise CrawlerError(f"获取评论回复列表失败，状态码: {status}")

            data = self.parse_json(content)
            if data.get("code") != 0:
                raise CrawlerError(f"获取评论回复列表失败，错误: {data.get('msg')}")

            result = data.get("data", {})
            replies = result.get("comments", [])
            total = result.get("total", 0)

            return replies, total
        except Exception as e:
            raise CrawlerError(f"获取评论回复列表失败: {str(e)}")

    def _parse_note(self, note: Dict) -> Content:
        """解析笔记数据。

        Args:
            note: 笔记数据

        Returns:
            内容对象
        """
        try:
            # 确定内容类型
            content_type = ContentType.ARTICLE
            if note.get("type") == "video":
                content_type = ContentType.VIDEO
            elif note.get("type") == "normal":
                content_type = ContentType.IMAGE

            # 提取图片列表
            images = []
            if "images" in note:
                images = [img.get("url") for img in note["images"] if img.get("url")]

            # 提取视频信息
            videos = []
            if "video" in note and note["video"]:
                videos = [{
                    "url": note["video"].get("url"),
                    "cover": note["video"].get("cover"),
                    "duration": note["video"].get("duration"),
                }]

            # 提取统计数据
            stats = {
                "likes": note.get("likes", 0),
                "comments": note.get("comments", 0),
                "collects": note.get("collects", 0),
                "shares": note.get("shares", 0),
            }

            # 提取时间
            publish_time = None
            if "time" in note:
                publish_time = self.extract_datetime(note["time"])

            # 创建内容对象
            content = Content(
                title=note.get("title", ""),
                content=note.get("desc", ""),
                summary=note.get("desc", "")[:500] if note.get("desc") else None,
                content_type=content_type,
                platform_id=1,  # 小红书平台ID
                url=f"https://www.xiaohongshu.com/explore/{note.get('id')}",
                author=note.get("user", {}).get("nickname"),
                publish_time=publish_time,
                cover_image=note.get("cover", {}).get("url"),
                images=images,
                videos=videos,
                metadata={
                    "note_id": note.get("id"),
                    "user_id": note.get("user", {}).get("id"),
                    "ip_location": note.get("ip_location"),
                    "topic": note.get("topic", {}).get("name"),
                },
                stats=stats,
                keywords=note.get("keywords", []),
                categories=note.get("categories", []),
                language="zh",
                word_count=len(note.get("desc", "")),
                read_time=len(note.get("desc", "")) // 500 * 60,  # 假设阅读速度500字/分钟
                is_original=True,  # 小红书内容都是原创
            )

            return content
        except Exception as e:
            raise CrawlerError(f"解析笔记数据失败: {str(e)}")

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