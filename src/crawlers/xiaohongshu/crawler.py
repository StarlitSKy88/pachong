"""小红书爬虫"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin
from datetime import datetime, UTC

import aiohttp
from loguru import logger

from .sign import XHSSign
from ...models.content import Content
from ...utils.headers_manager import HeadersManager

class XiaoHongShuCrawler:
    """小红书爬虫类"""

    def __init__(self):
        """初始化爬虫"""
        self.base_url = "https://www.xiaohongshu.com/api"
        self.sign_generator = XHSSign()
        self.headers_manager = HeadersManager()
        self.session = None

    async def _init_session(self):
        """初始化会话"""
        if self.session is None:
            self.session = aiohttp.ClientSession(headers=self.headers_manager.get_headers())

    async def _close_session(self):
        """关闭会话"""
        if self.session:
            await self.session.close()
            self.session = None

    async def _make_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """发送请求

        Args:
            method: 请求方法
            url: 请求URL
            **kwargs: 其他参数

        Returns:
            响应数据
        """
        await self._init_session()
        try:
            async with self.session.request(method, url, **kwargs) as response:
                response.raise_for_status()
                data = await response.json()
                return data
        except Exception as e:
            logger.error(f"请求失败: {e}")
            return {"success": False, "error": str(e)}

    def _validate_url(self, url: str) -> bool:
        """验证URL是否有效

        Args:
            url: 要验证的URL

        Returns:
            URL是否有效
        """
        return url.startswith("https://www.xiaohongshu.com/explore/")

    async def search(self, keyword: str, page: int = 1, page_size: int = 20) -> List[Dict[str, Any]]:
        """搜索笔记

        Args:
            keyword: 搜索关键词
            page: 页码
            page_size: 每页数量

        Returns:
            搜索结果列表
        """
        url = urljoin(self.base_url, "/search/notes")
        params = self.sign_generator.generate_search_sign(keyword, page, page_size)
        
        try:
            response = await self._make_request("GET", url, params=params)
            if response.get("success"):
                return response["data"]["notes"]
            logger.error(f"搜索失败: {response.get('error')}")
            return []
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []

    async def get_detail(self, note_id: str) -> Optional[Dict[str, Any]]:
        """获取笔记详情

        Args:
            note_id: 笔记ID或URL

        Returns:
            笔记详情
        """
        # 如果是URL，提取笔记ID
        if self._validate_url(note_id):
            note_id = note_id.split("/")[-1]
            
        url = urljoin(self.base_url, f"/note/{note_id}")
        params = self.sign_generator.generate_note_sign(note_id)
        
        try:
            response = await self._make_request("GET", url, params=params)
            if response.get("success"):
                return response["data"]
            logger.error(f"获取笔记详情失败: {response.get('error')}")
            return None
        except Exception as e:
            logger.error(f"获取笔记详情失败: {e}")
            return None

    def parse(self, data: Dict[str, Any]) -> Content:
        """解析数据

        Args:
            data: 原始数据

        Returns:
            解析后的内容对象
        """
        try:
            # 处理发布时间
            publish_time = datetime.fromisoformat(data["time"]) if "time" in data else datetime.now(UTC)
            
            # 创建Content对象
            content = Content(
                title=data.get("title", ""),
                content=data.get("content", ""),
                author_name=data["user"]["nickname"],
                author_id=data["user"]["id"],
                url=f"https://www.xiaohongshu.com/explore/{data['id']}",
                images=data.get("images", []),
                video={"url": data.get("video", "")},
                publish_time=publish_time,
                likes=data["stats"]["likes"],
                comments=data["stats"]["comments"],
                shares=data["stats"]["shares"],
                collects=data["stats"]["collects"]
            )
            return content
        except KeyError as e:
            logger.error(f"解析数据失败，缺少必要字段: {e}")
            raise
        except Exception as e:
            logger.error(f"解析数据失败: {e}")
            raise

    async def crawl(self, keywords: List[str], max_pages: int = 1) -> List[Content]:
        """批量爬取

        Args:
            keywords: 关键词列表
            max_pages: 每个关键词的最大页数

        Returns:
            爬取的内容列表
        """
        results = []
        try:
            for keyword in keywords:
                for page in range(1, max_pages + 1):
                    notes = await self.search(keyword, page)
                    for note in notes:
                        if detail := await self.get_detail(note["id"]):
                            results.append(self.parse(detail))
                    await asyncio.sleep(1)  # 避免请求过快
        except Exception as e:
            logger.error(f"批量爬取失败: {e}")
        finally:
            await self._close_session()
        return results

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self._init_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self._close_session() 