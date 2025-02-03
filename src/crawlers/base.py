"""爬虫基类模块。"""

import asyncio
import json
import random
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import aiohttp
from aiohttp import ClientSession, ClientTimeout, TCPConnector
from bs4 import BeautifulSoup
from loguru import logger
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.config.settings import Settings
from src.utils.error_handler import CrawlerError


class BaseCrawler(ABC):
    """爬虫基类。"""

    def __init__(
        self,
        settings: Settings,
        session: Optional[ClientSession] = None,
        proxy: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        timeout: int = 30,
        retry_times: int = 3,
        retry_delay: int = 1,
        max_concurrent: int = 3,
    ):
        """初始化爬虫。

        Args:
            settings: 配置对象
            session: aiohttp会话对象
            proxy: 代理地址
            headers: 请求头
            cookies: Cookie
            timeout: 超时时间（秒）
            retry_times: 重试次数
            retry_delay: 重试延迟（秒）
            max_concurrent: 最大并发数
        """
        self.settings = settings
        self.session = session
        self.proxy = proxy
        self.headers = headers or self._get_default_headers()
        self.cookies = cookies or {}
        self.timeout = timeout
        self.retry_times = retry_times
        self.retry_delay = retry_delay
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.visited_urls: Set[str] = set()

    @abstractmethod
    async def start(self) -> None:
        """启动爬虫。"""
        pass

    @abstractmethod
    async def parse(self, response: str, url: str) -> Any:
        """解析响应。

        Args:
            response: 响应内容
            url: 请求URL

        Returns:
            解析结果
        """
        pass

    async def _init_session(self) -> None:
        """初始化会话。"""
        if not self.session:
            timeout = ClientTimeout(total=self.timeout)
            connector = TCPConnector(ssl=False)
            self.session = ClientSession(
                timeout=timeout,
                connector=connector,
                headers=self.headers,
                cookies=self.cookies,
            )

    async def _close_session(self) -> None:
        """关闭会话。"""
        if self.session and not self.session.closed:
            await self.session.close()

    def _get_default_headers(self) -> Dict[str, str]:
        """获取默认请求头。

        Returns:
            默认请求头
        """
        return {
            "User-Agent": self._get_random_ua(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
        }

    def _get_random_ua(self) -> str:
        """获取随机User-Agent。

        Returns:
            随机User-Agent
        """
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        ]
        return random.choice(user_agents)

    async def _get_proxy(self) -> Optional[str]:
        """获取代理地址。

        Returns:
            代理地址
        """
        if not self.settings.USE_PROXY:
            return None

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.settings.PROXY_API_URL,
                    headers={"Authorization": f"Bearer {self.settings.PROXY_API_KEY}"},
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("proxy")
        except Exception as e:
            logger.warning(f"获取代理失败: {str(e)}")
        return None

    @retry(
        retry=retry_if_exception_type(CrawlerError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    async def _request(
        self,
        url: str,
        method: str = "GET",
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        cookies: Optional[Dict] = None,
        allow_redirects: bool = True,
        verify_ssl: bool = False,
        proxy: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> Tuple[int, str, Dict[str, str]]:
        """发送请求。

        Args:
            url: 请求URL
            method: 请求方法
            params: 查询参数
            data: 表单数据
            json_data: JSON数据
            headers: 请求头
            cookies: Cookie
            allow_redirects: 是否允许重定向
            verify_ssl: 是否验证SSL证书
            proxy: 代理地址
            timeout: 超时时间（秒）

        Returns:
            状态码、响应内容和响应头

        Raises:
            CrawlerError: 请求失败
        """
        try:
            await self._init_session()

            if not self.session:
                raise CrawlerError("会话未初始化")

            # 更新请求头
            request_headers = self.headers.copy()
            if headers:
                request_headers.update(headers)

            # 更新Cookie
            request_cookies = self.cookies.copy()
            if cookies:
                request_cookies.update(cookies)

            # 设置代理
            request_proxy = proxy or self.proxy or await self._get_proxy()

            # 设置超时
            request_timeout = ClientTimeout(total=timeout or self.timeout)

            async with self.semaphore:
                async with self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    data=data,
                    json=json_data,
                    headers=request_headers,
                    cookies=request_cookies,
                    allow_redirects=allow_redirects,
                    verify_ssl=verify_ssl,
                    proxy=request_proxy,
                    timeout=request_timeout,
                ) as response:
                    content = await response.text()
                    return response.status, content, dict(response.headers)

        except asyncio.TimeoutError:
            raise CrawlerError(f"请求超时: {url}")
        except aiohttp.ClientError as e:
            raise CrawlerError(f"请求失败: {url}, 错误: {str(e)}")
        except Exception as e:
            raise CrawlerError(f"请求异常: {url}, 错误: {str(e)}")

    async def get(
        self,
        url: str,
        params: Optional[Dict] = None,
        **kwargs: Any,
    ) -> Tuple[int, str, Dict[str, str]]:
        """发送GET请求。

        Args:
            url: 请求URL
            params: 查询参数
            **kwargs: 其他参数

        Returns:
            状态码、响应内容和响应头
        """
        return await self._request(url=url, method="GET", params=params, **kwargs)

    async def post(
        self,
        url: str,
        data: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        **kwargs: Any,
    ) -> Tuple[int, str, Dict[str, str]]:
        """发送POST请求。

        Args:
            url: 请求URL
            data: 表单数据
            json_data: JSON数据
            **kwargs: 其他参数

        Returns:
            状态码、响应内容和响应头
        """
        return await self._request(
            url=url, method="POST", data=data, json_data=json_data, **kwargs
        )

    def parse_html(self, html: str) -> BeautifulSoup:
        """解析HTML。

        Args:
            html: HTML内容

        Returns:
            BeautifulSoup对象
        """
        return BeautifulSoup(html, "lxml")

    def parse_json(self, text: str) -> Dict:
        """解析JSON。

        Args:
            text: JSON文本

        Returns:
            JSON对象
        """
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise CrawlerError(f"JSON解析失败: {str(e)}")

    def extract_datetime(
        self,
        text: str,
        formats: Optional[List[str]] = None,
    ) -> Optional[datetime]:
        """提取日期时间。

        Args:
            text: 日期时间文本
            formats: 日期时间格式列表

        Returns:
            日期时间对象
        """
        if not formats:
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M",
                "%Y-%m-%d",
                "%Y年%m月%d日 %H:%M:%S",
                "%Y年%m月%d日 %H:%M",
                "%Y年%m月%d日",
            ]

        for fmt in formats:
            try:
                return datetime.strptime(text.strip(), fmt)
            except ValueError:
                continue
        return None

    async def download_file(
        self,
        url: str,
        save_path: str,
        chunk_size: int = 8192,
        **kwargs: Any,
    ) -> bool:
        """下载文件。

        Args:
            url: 文件URL
            save_path: 保存路径
            chunk_size: 块大小
            **kwargs: 其他参数

        Returns:
            是否下载成功
        """
        try:
            await self._init_session()

            if not self.session:
                raise CrawlerError("会话未初始化")

            async with self.session.get(url, **kwargs) as response:
                if response.status != 200:
                    raise CrawlerError(f"下载失败，状态码: {response.status}")

                with open(save_path, "wb") as f:
                    async for chunk in response.content.iter_chunked(chunk_size):
                        f.write(chunk)
                return True

        except Exception as e:
            logger.error(f"下载文件失败: {url}, 错误: {str(e)}")
            return False

    async def __aenter__(self) -> "BaseCrawler":
        """异步上下文管理器入口。

        Returns:
            爬虫对象
        """
        await self._init_session()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """异步上下文管理器出口。

        Args:
            exc_type: 异常类型
            exc_val: 异常值
            exc_tb: 异常回溯
        """
        await self._close_session() 