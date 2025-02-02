from typing import Dict
import random
import os

class HeadersManager:
    """请求头管理器"""

    def __init__(self):
        """初始化请求头管理器"""
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0"
        ]

    def get_headers(self) -> Dict[str, str]:
        """获取请求头

        Returns:
            请求头字典
        """
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "X-Requested-With": "XMLHttpRequest"
        }

    async def initialize(self):
        """初始化"""
        self.rotate_user_agent()
        
    def rotate_user_agent(self):
        """轮换User-Agent"""
        self.headers['User-Agent'] = random.choice(self.user_agents)
        
    def update_headers(self, headers: Dict[str, str]):
        """更新请求头
        
        Args:
            headers: 请求头字典
        """
        self.headers.update(headers)

    @staticmethod
    def get_random_user_agent() -> str:
        """获取随机User-Agent

        Returns:
            str: User-Agent字符串
        """
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        ]
        return random.choice(user_agents)

    @staticmethod
    def get_random_accept_language() -> str:
        """获取随机Accept-Language

        Returns:
            str: Accept-Language字符串
        """
        accept_languages = [
            "zh-CN,zh;q=0.9,en;q=0.8",
            "en-US,en;q=0.9",
            "zh-TW,zh;q=0.9,en;q=0.8",
            "ja-JP,ja;q=0.9,en;q=0.8",
            "ko-KR,ko;q=0.9,en;q=0.8"
        ]
        return random.choice(accept_languages)

    @staticmethod
    def get_headers() -> Dict[str, str]:
        """获取随机的请求头

        Returns:
            Dict[str, str]: 请求头字典
        """
        return {
            'User-Agent': HeadersManager.get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': HeadersManager.get_random_accept_language(),
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

    @staticmethod
    def get_xiaohongshu_headers() -> Dict[str, str]:
        """获取小红书请求头

        Returns:
            Dict[str, str]: 请求头字典
        """
        headers = HeadersManager.get_headers()
        headers.update({
            'Origin': 'https://www.xiaohongshu.com',
            'Referer': 'https://www.xiaohongshu.com'
        })
        return headers

    @staticmethod
    def get_bilibili_headers() -> Dict[str, str]:
        """获取B站请求头

        Returns:
            Dict[str, str]: 请求头字典
        """
        headers = HeadersManager.get_headers()
        headers.update({
            'Origin': 'https://www.bilibili.com',
            'Referer': 'https://www.bilibili.com'
        })
        return headers 