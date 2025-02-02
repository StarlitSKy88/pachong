"""爬虫基类"""
import logging
import aiohttp
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod

from src.utils.headers_manager import HeadersManager
from src.utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

class BaseCrawler(ABC):
    """爬虫基类"""

    def __init__(self):
        """初始化爬虫"""
        self.headers_manager = HeadersManager()
        self.rate_limiter = RateLimiter(1)  # 默认每秒1个请求
        self.session = None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
            self.session = None

    @abstractmethod
    async def search(self, keyword: str, **kwargs) -> List[Dict[str, Any]]:
        """搜索内容

        Args:
            keyword: 搜索关键词
            **kwargs: 其他参数

        Returns:
            List[Dict[str, Any]]: 搜索结果列表
        """
        pass

    @abstractmethod
    async def get_detail(self, url: str) -> Optional[Dict[str, Any]]:
        """获取内容详情

        Args:
            url: 内容URL

        Returns:
            Optional[Dict[str, Any]]: 内容详情
        """
        pass

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