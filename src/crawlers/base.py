import os
import time
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any
from datetime import datetime
from urllib.parse import urlparse

import aiohttp
import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.database.session import get_db
from src.models.platform import Platform
from src.models.content import Content
from src.utils.cookie_manager import CookieManager
from src.utils.proxy_manager import ProxyManager
from src.utils.rate_limiter import RateLimiter
from src.utils.headers_manager import HeadersManager

logger = logging.getLogger(__name__)

class BaseCrawler(ABC):
    """基础爬虫类"""
    
    def __init__(self, config: dict = None):
        """初始化爬虫"""
        self.config = config or {}
        self.platform_name = self.config.get("platform_name", "unknown")
        self.rate_limit = self.config.get("rate_limit", 1.0)
        self.retry_limit = self.config.get("retry_limit", 3)
        
        # 初始化组件
        self.platform = None
        self.cookie_manager = CookieManager()
        self.proxy_manager = ProxyManager()
        self.rate_limiter = RateLimiter(self.rate_limit)
        self.headers_manager = HeadersManager()
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
            
    async def _request(self, url: str, method: str = "GET", **kwargs) -> Optional[Dict]:
        """发送请求
        
        Args:
            url: 请求地址
            method: 请求方法
            **kwargs: 其他参数
            
        Returns:
            Optional[Dict]: 响应数据
        """
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        try:
            async with self.session.request(method, url, **kwargs) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    self.logger.error(f"请求失败: {response.status} {url}")
                    return None
        except Exception as e:
            self.logger.error(f"请求异常: {str(e)}")
            return None
            
    async def initialize(self) -> None:
        """初始化平台配置"""
        async with get_db() as db:
            self.platform = await self._get_or_create_platform(db)
            if not self.platform.is_active:
                raise ValueError(f"Platform {self.platform_name} is not active")
                
            # 更新爬虫配置
            self.rate_limit = self.platform.rate_limit or self.rate_limit
            self.retry_limit = self.platform.retry_limit or self.retry_limit
            
            # 初始化组件
            await self.rate_limiter.set_rate(self.rate_limit)
            await self.headers_manager.initialize()
            
    async def _get_or_create_platform(self, db: Session) -> Platform:
        """获取或创建平台记录"""
        stmt = select(Platform).where(Platform.name == self.platform_name)
        result = await db.execute(stmt)
        platform = result.scalar_one_or_none()
        
        if not platform:
            platform = Platform(
                name=self.platform_name,
                is_active=True,
                rate_limit=self.rate_limit,
                retry_limit=self.retry_limit
            )
            db.add(platform)
            await db.commit()
            await db.refresh(platform)
            
        if not platform.is_active:
            raise ValueError(f"Platform {self.platform_name} is not active")
            
        return platform
    
    async def _wait_for_rate_limit(self) -> None:
        """等待限流"""
        if self.rate_limit <= 0:
            return
        
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < 1.0 / self.rate_limit:
            await asyncio.sleep(1.0 / self.rate_limit - time_since_last_request)
        self.last_request_time = time.time()
    
    async def _make_request(
        self,
        url: str,
        method: str = 'GET',
        headers: Optional[Dict] = None,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        proxy: Optional[str] = None,
        timeout: int = 30
    ) -> Optional[aiohttp.ClientResponse]:
        """发送HTTP请求
        
        Args:
            url: 请求URL
            method: 请求方法
            headers: 请求头
            params: URL参数
            data: 请求数据
            proxy: 代理地址
            timeout: 超时时间（秒）
            
        Returns:
            响应对象
        """
        await self._wait_for_rate_limit()
        
        _headers = {**self.headers_manager.headers, **(headers or {})}
        cookies = await self.cookie_manager.get_cookies(urlparse(url).netloc)
        
        for attempt in range(self.retry_limit):
            try:
                async with aiohttp.ClientSession(cookies=cookies) as session:
                    async with session.request(
                        method=method,
                        url=url,
                        headers=_headers,
                        params=params,
                        json=data,
                        proxy=proxy or await self.proxy_manager.get_proxy(),
                        timeout=timeout
                    ) as response:
                        if response.status == 200:
                            return response
                        elif response.status == 403:
                            await self.cookie_manager.refresh_cookies()
                            cookies = await self.cookie_manager.get_cookies(urlparse(url).netloc)
                        else:
                            logger.warning(f"Request failed with status {response.status}: {url}")
                            
            except Exception as e:
                logger.error(f"Request failed: {str(e)}")
                if attempt == self.retry_limit - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # 指数退避
        
        return None
    
    @abstractmethod
    async def search(self, keyword: str) -> List[Any]:
        """搜索
        
        Args:
            keyword: 关键词
            
        Returns:
            List[Any]: 搜索结果
        """
        pass
        
    @abstractmethod
    async def get_detail(self, item: Any) -> Any:
        """获取详情
        
        Args:
            item: 项目
            
        Returns:
            Any: 详情
        """
        pass
    
    @abstractmethod
    async def crawl(self, keywords: List[str], time_range: str = '24h',
                   limit: int = 100) -> List[Dict]:
        """爬取内容
        
        Args:
            keywords: 关键词列表
            time_range: 时间范围
            limit: 限制数量
            
        Returns:
            List[Dict]: 内容列表
        """
        pass
        
    @abstractmethod
    async def parse(self, data: Dict) -> Dict:
        """解析数据
        
        Args:
            data: 原始数据
            
        Returns:
            Dict: 解析后的数据
        """
        pass
    
    async def save_content(self, content: Content) -> None:
        """保存内容
        
        Args:
            content: Content对象
        """
        async with get_db() as db:
            try:
                db.add(content)
                db.commit()
                db.refresh(content)
            except Exception as e:
                db.rollback()
                logger.error(f"Failed to save content: {str(e)}")
                raise
    
    async def run(self, **kwargs) -> None:
        """运行爬虫
        
        Args:
            **kwargs: 爬虫参数
        """
        try:
            await self.initialize()
            raw_contents = await self.crawl(**kwargs)
            for raw_content in raw_contents:
                content = await self.parse_content(raw_content)
                await self.save_content(content)
                
        except Exception as e:
            logger.error(f"Crawler failed: {str(e)}")
            if self.platform:
                self.platform.error_count += 1
                self.platform.last_error = str(e)
            raise
        finally:
            if self.platform:
                async with get_db() as db:
                    db.commit()
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} platform={self.platform_name}>" 