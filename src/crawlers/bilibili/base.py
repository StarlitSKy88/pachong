"""B站基础爬虫"""

from typing import Dict, Any, Optional
import hashlib
import time
import random
from ..base_crawler import BaseCrawler
from ...utils.headers_manager import HeadersManager
from ...utils.cookie_manager import CookieManager
from ...utils.proxy_manager import ProxyManager
from ...utils.rate_limiter import RateLimiter

class BilibiliBaseCrawler(BaseCrawler):
    """B站爬虫基类"""

    def __init__(self):
        """初始化B站爬虫基类"""
        super().__init__("bilibili")
        self.base_url = "https://www.bilibili.com"
        self.headers = HeadersManager.get_bilibili_headers()
        self.cookie_manager = CookieManager()
        self.proxy_manager = ProxyManager()
        self.rate_limiter = RateLimiter()
        self.web_url = "https://www.bilibili.com"
        self.app_key = "1d8b6e7d45233436"
        self.app_secret = "560c52ccd288fed045859ed18bffd973"
    
    def _generate_sign(self, params: Dict[str, Any]) -> str:
        """生成签名
        
        Args:
            params: 请求参数
            
        Returns:
            str: 签名
        """
        # 按照key排序
        sorted_params = dict(sorted(params.items()))
        
        # 拼接字符串
        query = []
        for k, v in sorted_params.items():
            if k != 'sign' and v is not None:
                query.append(f"{k}={v}")
        query = '&'.join(query)
        
        # 加上app secret
        query += self.app_secret
        
        # MD5
        return hashlib.md5(query.encode()).hexdigest()
    
    def _add_common_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """添加公共参数
        
        Args:
            params: 请求参数
            
        Returns:
            Dict[str, Any]: 添加公共参数后的请求参数
        """
        ts = int(time.time())
        common_params = {
            'appkey': self.app_key,
            'ts': ts,
            'platform': 'web',
            'lang': 'zh-CN'
        }
        params.update(common_params)
        
        # 生成签名
        params['sign'] = self._generate_sign(params)
        
        return params
    
    async def request(
        self,
        url: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Optional[Dict]:
        """发送请求

        Args:
            url: 请求地址
            method: 请求方法
            params: URL参数
            data: 请求数据
            headers: 请求头
            **kwargs: 其他参数

        Returns:
            Optional[Dict]: 响应数据
        """
        # 添加请求头
        request_headers = self.headers.copy()
        if headers:
            request_headers.update(headers)

        # 添加Cookie
        cookies = await self.cookie_manager.get_cookies()
        if cookies:
            kwargs['cookies'] = cookies

        # 添加代理
        proxy = await self.proxy_manager.get_proxy()
        if proxy:
            kwargs['proxy'] = proxy

        # 发送请求
        return await super().request(
            url=url,
            method=method,
            params=params,
            data=data,
            headers=request_headers,
            **kwargs
        ) 