"""小红书爬虫"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin
from datetime import datetime, timezone
import random
import json
import base64
import hashlib
import time

import aiohttp
from loguru import logger

from .sign import XHSSign
from ...models.content import Content
from ...utils.headers_manager import HeadersManager

class XiaoHongShuCrawler:
    """小红书爬虫 - 免登录版本"""
    
    def __init__(self, proxy_manager=None):
        self.proxy_manager = proxy_manager
        self.device_id = ''.join(random.choices('0123456789abcdef', k=16))
        self.headers = self._get_headers()
        
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_8 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.20(0x18001442) NetType/WIFI Language/zh_CN',
            'Accept': 'application/json',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'Origin': 'https://www.xiaohongshu.com',
            'Referer': 'https://www.xiaohongshu.com',
            'X-B3-TraceId': ''.join(random.choices('0123456789abcdef', k=32)),
            'X-S-Common': self._get_xs_common(),
        }
        
    def _get_xs_common(self) -> str:
        """获取通用签名参数"""
        data = {
            'deviceId': self.device_id,
            'platform': 'web',
            'timestamp': str(int(time.time() * 1000))
        }
        return base64.b64encode(json.dumps(data).encode()).decode()
        
    def _get_sign(self, path: str, params: Dict = None) -> str:
        """获取签名"""
        timestamp = str(int(time.time() * 1000))
        data = f"{path}{''.join(sorted(params.values()) if params else '')}WSUDD{timestamp}"
        return hashlib.md5(data.encode()).hexdigest()
        
    async def get_note_by_id(self, note_id: str) -> Dict:
        """通过笔记ID获取内容"""
        path = f"/api/sns/web/v1/feed"
        params = {
            'note_id': note_id,
            'source_note_id': '',
        }
        
        headers = self.headers.copy()
        headers['X-Sign'] = self._get_sign(path, params)
        
        url = f"https://www.xiaohongshu.com{path}"
        
        async with aiohttp.ClientSession() as session:
            proxy = await self.proxy_manager.get_proxy() if self.proxy_manager else None
            try:
                async with session.get(url, headers=headers, params=params, proxy=proxy) as response:
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
                logger.error(f"获取笔记失败: {str(e)}")
                return None
                
    async def search_notes(self, keyword: str, page: int = 1, page_size: int = 20) -> List[Dict]:
        """搜索笔记"""
        path = "/api/sns/web/v1/search/notes"
        params = {
            'keyword': keyword,
            'page': str(page),
            'page_size': str(page_size),
            'sort': 'general',
            'source': 'web_search'
        }
        
        headers = self.headers.copy()
        headers['X-Sign'] = self._get_sign(path, params)
        
        url = f"https://www.xiaohongshu.com{path}"
        
        async with aiohttp.ClientSession() as session:
            proxy = await self.proxy_manager.get_proxy() if self.proxy_manager else None
            try:
                async with session.get(url, headers=headers, params=params, proxy=proxy) as response:
                    if response.status == 200:
                        data = await response.json()
                        if proxy:
                            self.proxy_manager.update_proxy_status(proxy, True)
                        return data.get('data', {}).get('notes', [])
                    else:
                        if proxy:
                            self.proxy_manager.update_proxy_status(proxy, False)
                        return []
            except Exception as e:
                if proxy:
                    self.proxy_manager.update_proxy_status(proxy, False)
                logger.error(f"搜索笔记失败: {str(e)}")
                return []
                
    async def get_user_notes(self, user_id: str, page: int = 1, page_size: int = 20) -> List[Dict]:
        """获取用户笔记列表"""
        url = f"https://www.xiaohongshu.com/fe_api/burdock/weixin/v2/user/{user_id}/notes"
        params = {
            'page': page,
            'page_size': page_size
        }
        
        async with aiohttp.ClientSession() as session:
            proxy = await self.proxy_manager.get_proxy() if self.proxy_manager else None
            try:
                async with session.get(url, headers=self.headers, params=params, proxy=proxy) as response:
                    if response.status == 200:
                        data = await response.json()
                        if proxy:
                            self.proxy_manager.update_proxy_status(proxy, True)
                        return data.get('data', {}).get('notes', [])
                    else:
                        if proxy:
                            self.proxy_manager.update_proxy_status(proxy, False)
                        return []
            except Exception as e:
                if proxy:
                    self.proxy_manager.update_proxy_status(proxy, False)
                logger.error(f"获取用户笔记失败: {str(e)}")
                return []

    def is_valid_url(self, url: str) -> bool:
        """检查URL是否有效"""
        return url.startswith("https://www.xiaohongshu.com/explore/")

    async def _make_request(
        self,
        method: str,
        url: str,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """发送请求

        Args:
            method: 请求方法
            url: 请求URL
            **kwargs: 其他参数

        Returns:
            响应数据

        Raises:
            Exception: 请求失败时抛出异常
        """
        await self._init_session()

        retry_count = 0
        max_retries = self.retry_policy.max_retries if self.retry_policy else 3
        last_error = None
        current_proxy = None

        while True:
            try:
                # 速率限制
                if self.rate_limiter:
                    delay = await self.rate_limiter.get_delay()
                    self.logger.debug(f"Rate limiter delay: {delay}")
                    if delay > 0:
                        await asyncio.sleep(delay)
                    await self.rate_limiter.acquire()

                # 获取代理
                if self.proxy_manager:
                    current_proxy = await self.proxy_manager.get_proxy()
                    kwargs["proxy"] = current_proxy

                # 获取Cookie
                if self.cookie_manager:
                    try:
                        kwargs["cookies"] = await self.cookie_manager.get_cookie()
                    except Exception as e:
                        await self.cookie_manager.report_failure()
                        raise e  # 直接抛出原始异常

                # 添加请求头
                kwargs["headers"] = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                    "Connection": "keep-alive",
                    "Referer": "https://www.xiaohongshu.com",
                    **(kwargs.get("headers", {}))
                }

                # 发送请求
                try:
                    response = await self.session.request(method, url, **kwargs)
                response.raise_for_status()
                data = await response.json()

                    # 报告成功
                    if self.proxy_manager and current_proxy:
                        await self.proxy_manager.report_success(current_proxy)
                    if self.cookie_manager:
                        await self.cookie_manager.report_success()
                    if self.rate_limiter:
                        await self.rate_limiter.report_success()

                return data

                except (aiohttp.ClientError, aiohttp.ContentTypeError) as e:
                    if self.proxy_manager and current_proxy:
                        await self.proxy_manager.report_failure(current_proxy)
                    if self.cookie_manager:
                        await self.cookie_manager.report_failure()
                    if self.rate_limiter:
                        await self.rate_limiter.report_failure()
                    raise e  # 直接抛出原始异常

        except Exception as e:
                # 记录错误
                self.logger.error(f"Request failed: {e}")
                last_error = e

                # 检查是否需要重试
                retry_count += 1
                if retry_count >= max_retries:
                    raise last_error

                if self.retry_policy:
                    should_retry = self.retry_policy.should_retry(last_error)
                    if not should_retry:
                        raise last_error
                    
                    delay = self.retry_policy.get_delay(retry_count)
                    await asyncio.sleep(delay)
                else:
                    raise last_error

            finally:
                if self.rate_limiter:
                    await self.rate_limiter.release()

    async def search(self, keyword: str) -> dict:
        """搜索笔记"""
        trace = self.langsmith.start_trace("search")
        try:
            # 获取Cookie
            cookie = await self.cookie_manager.get_cookie()
            # 获取代理
            proxy = await self.proxy_manager.get_proxy()
            # 获取速率限制
            await self.rate_limiter.acquire()

            try:
                url = f"{self.base_url}/api/sns/web/v1/search/notes"
                params = {
                    "keyword": keyword,
                    "cursor": ""
                }
                headers = {
                    "Cookie": cookie,
                    "User-Agent": self.user_agent
                }
                async with self.session.get(url, params=params, headers=headers, proxy=proxy) as response:
                    if response.status != 200:
                        self.logger.error(f"Search failed with status {response.status}")
                        await self.cookie_manager.report_failure()
                        await self.proxy_manager.report_failure()
                        return {
                            "success": False,
                            "data": {
                                "notes": [],
                                "has_more": False,
                                "cursor": ""
                            }
                        }

                    data = await response.json()
                    if not data.get("success"):
                        self.logger.error(f"Search failed: {data.get('msg')}")
                        await self.cookie_manager.report_failure()
                        await self.proxy_manager.report_failure()
                        return {
                            "success": False,
                            "data": {
                                "notes": [],
                                "has_more": False,
                                "cursor": ""
                            }
                        }

                    await self.cookie_manager.report_success()
                    await self.proxy_manager.report_success()
                    return data

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                self.logger.error(f"Search failed: {str(e)}")
                await self.cookie_manager.report_failure()
                await self.proxy_manager.report_failure()
                return {
                    "success": False,
                    "data": {
                        "notes": [],
                        "has_more": False,
                        "cursor": ""
                    }
                }
            finally:
                await self.rate_limiter.release()
        finally:
            await self.langsmith.end_trace(trace)

    async def get_detail(self, note_id: str) -> dict:
        """获取笔记详情"""
        trace = self.langsmith.start_trace("get_detail")
        try:
            # 获取Cookie
            cookie = await self.cookie_manager.get_cookie()
            # 获取代理
            proxy = await self.proxy_manager.get_proxy()
            # 获取速率限制
            await self.rate_limiter.acquire()

            try:
                url = f"{self.base_url}/api/sns/web/v1/feed"
                params = {
                    "note_id": note_id
                }
                headers = {
                    "Cookie": cookie,
                    "User-Agent": self.user_agent
                }
                async with self.session.get(url, params=params, headers=headers, proxy=proxy) as response:
                    if response.status != 200:
                        self.logger.error(f"Get detail failed with status {response.status}")
                        await self.cookie_manager.report_failure()
                        await self.proxy_manager.report_failure()
                        return {
                            "success": False,
                            "data": {}
                        }

                    data = await response.json()
                    if not data.get("success"):
                        self.logger.error(f"Get detail failed: {data.get('msg')}")
                        await self.cookie_manager.report_failure()
                        await self.proxy_manager.report_failure()
                        return {
                            "success": False,
                            "data": {}
                        }

                    await self.cookie_manager.report_success()
                    await self.proxy_manager.report_success()
                    return data

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                self.logger.error(f"Get detail failed: {str(e)}")
                await self.cookie_manager.report_failure()
                await self.proxy_manager.report_failure()
                return {
                    "success": False,
                    "data": {}
                }
            finally:
                await self.rate_limiter.release()
        finally:
            await self.langsmith.end_trace(trace)

    async def parse(self, data: Dict[str, Any]) -> Content:
        """解析数据

        Args:
            data: 原始数据

        Returns:
            解析后的内容
        """
        if self.data_cleaner:
            # 清洗文本
            title = self.data_cleaner.clean_text(data.get("title", ""))
            desc = self.data_cleaner.clean_text(data.get("desc", ""))
            
            # 清洗HTML
            content = self.data_cleaner.clean_html(data.get("content", ""))
            
            # 清洗URL
            images = [
                self.data_cleaner.clean_url(url)
                for url in data.get("images", [])
            ]
            
            # 验证数据
            if not self.data_cleaner.validate_data({
                "title": title,
                "desc": desc,
                "content": content,
                "images": images
            }):
                raise ValueError("Invalid data after cleaning")
        else:
            title = data.get("title", "")
            desc = data.get("desc", "")
            content = data.get("content", "")
            images = data.get("images", [])
        
        return Content(
            id=data["id"],
            title=title,
            desc=desc,
            content=content,
            images=images,
            user=data.get("user", {}),
            stats=data.get("stats", {}),
            type=data.get("type", "normal"),
            created_at=datetime.now(timezone.utc)
        )

    async def crawl(self, keywords: List[str], max_items: int = 100) -> List[Content]:
        """批量爬取

        Args:
            keywords: 关键词列表
            max_items: 最大爬取数量

        Returns:
            爬取结果
        """
        if self.data_cleaner:
            # 清洗关键词
            keywords = [
                self.data_cleaner.clean_text(keyword)
                for keyword in keywords
            ]

        results = []
        for keyword in keywords:
            while len(results) < max_items:
                search_result = await self.search(keyword)
                if not search_result["success"]:
                    break

                items = search_result["data"]["notes"]
                if not items:
                    break

                for item in items:
                    if len(results) >= max_items:
                        break

                    try:
                        detail_result = await self.get_detail(item["id"])
                        if detail_result["success"]:
                            content = await self.parse(detail_result["data"]["note"])
                            results.append(content)
                    except Exception as e:
                        self.logger.error(f"Failed to process item {item.get('id')}: {e}")

                if not search_result["data"]["has_more"]:
                    break

        return results[:max_items]

    async def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Origin": "https://www.xiaohongshu.com",
            "Referer": "https://www.xiaohongshu.com",
            "Content-Type": "application/json;charset=UTF-8"
        }
        
        # 如果有cookie,添加到请求头
        if self.cookie_manager and (cookie := await self.cookie_manager.get_cookie()):
            headers["Cookie"] = cookie
            
        return headers 