"""爬虫基类"""
import logging
import aiohttp
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
import asyncio
from datetime import datetime, timedelta
import json

from src.utils.headers_manager import HeadersManager
from src.utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

class BaseCrawler(ABC):
    """爬虫基类"""

    def __init__(self, timeout: int = 30, proxy: Optional[str] = None):
        """初始化爬虫"""
        self.timeout = timeout
        self.proxy = proxy
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.logger = logging.getLogger(self.__class__.__name__)
        self.headers_manager = HeadersManager()
        self.rate_limiter = RateLimiter(1)  # 默认每秒1个请求

    async def __aenter__(self):
        """创建会话"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers=self.headers
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """关闭会话"""
        if self.session:
            await self.session.close()

    @abstractmethod
    async def search(self, keyword: str, time_range: str, limit: int) -> List[Dict[str, Any]]:
        """搜索内容"""
        pass

    @abstractmethod
    async def get_detail(self, item_id: str) -> Dict[str, Any]:
        """获取详情"""
        pass

    async def _get(self, url: str, params: Optional[Dict] = None) -> Dict:
        """发送GET请求"""
        try:
            async with self.session.get(url, params=params, proxy=self.proxy) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            self.logger.error(f"GET请求失败: {url}, {str(e)}")
            raise

    async def _post(self, url: str, data: Optional[Dict] = None) -> Dict:
        """发送POST请求"""
        try:
            async with self.session.post(url, json=data, proxy=self.proxy) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            self.logger.error(f"POST请求失败: {url}, {str(e)}")
            raise

    def parse_time_range(self, time_range: str) -> datetime:
        """解析时间范围"""
        hours = int(time_range.replace('h', ''))
        return datetime.now() - timedelta(hours=hours)

    def filter_by_time(self, items: List[Dict], time_range: str) -> List[Dict]:
        """按时间过滤结果"""
        if not time_range:
            return items
            
        start_time = self.parse_time_range(time_range)
        return [
            item for item in items
            if datetime.fromisoformat(item['publish_time']) >= start_time
        ]

    @abstractmethod
    def parse(self, data: Dict[str, Any]) -> Optional[Any]:
        """解析内容数据

        Args:
            data: 内容数据

        Returns:
            Optional[Any]: 解析后的内容对象
        """
        pass

    @abstractmethod
    async def crawl(self, keyword: str, **kwargs) -> List[Any]:
        """爬取内容

        Args:
            keyword: 搜索关键词
            **kwargs: 其他参数

        Returns:
            List[Any]: 爬取到的内容列表
        """
        pass 