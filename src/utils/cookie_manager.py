from typing import Dict, Optional
import json
import os
import aiohttp
from datetime import datetime, timedelta
import logging
import random

logger = logging.getLogger(__name__)

class CookieManager:
    """Cookie管理器"""

    def __init__(self):
        self.cookies = {}
        self.cookie_file = "data/cookies.json"
        self.load_cookies()

    def load_cookies(self):
        """从文件加载Cookie"""
        try:
            if os.path.exists(self.cookie_file):
                with open(self.cookie_file, 'r') as f:
                    self.cookies = json.load(f)
        except Exception as e:
            print(f"加载Cookie失败: {str(e)}")

    def save_cookies(self):
        """保存Cookie到文件"""
        try:
            os.makedirs(os.path.dirname(self.cookie_file), exist_ok=True)
            with open(self.cookie_file, 'w') as f:
                json.dump(self.cookies, f)
        except Exception as e:
            print(f"保存Cookie失败: {str(e)}")

    def add_cookie(self, platform: str, cookie: str):
        """添加Cookie"""
        if platform not in self.cookies:
            self.cookies[platform] = []
        if cookie not in self.cookies[platform]:
            self.cookies[platform].append(cookie)
            self.save_cookies()

    def get_cookie(self, platform: str) -> Optional[str]:
        """获取随机Cookie"""
        if platform in self.cookies and self.cookies[platform]:
            return random.choice(self.cookies[platform])
        return None

    def remove_cookie(self, platform: str, cookie: str):
        """移除Cookie"""
        if platform in self.cookies and cookie in self.cookies[platform]:
            self.cookies[platform].remove(cookie)
            self.save_cookies()

    def format_cookie(self, cookie_dict: Dict) -> str:
        """格式化Cookie字典为字符串"""
        return '; '.join([f"{k}={v}" for k, v in cookie_dict.items()])

    def parse_cookie(self, cookie_str: str) -> Dict:
        """解析Cookie字符串为字典"""
        cookie_dict = {}
        for item in cookie_str.split(';'):
            if '=' in item:
                key, value = item.strip().split('=', 1)
                cookie_dict[key] = value
        return cookie_dict

    # 小红书Cookie
    XHS_COOKIES = [
        {
            "webId": "your_web_id",
            "webVersion": "your_web_version",
            "a1": "your_a1",
            "gid": "your_gid",
            "timestamp": "your_timestamp"
        }
    ]

    # B站Cookie
    BILIBILI_COOKIES = [
        {
            "SESSDATA": "your_sessdata",
            "bili_jct": "your_bili_jct",
            "DedeUserID": "your_dedeuserid"
        }
    ]

    def init_platform_cookies(self):
        """初始化平台Cookie"""
        # 添加小红书Cookie
        for cookie in self.XHS_COOKIES:
            self.add_cookie('xhs', self.format_cookie(cookie))
        
        # 添加B站Cookie
        for cookie in self.BILIBILI_COOKIES:
            self.add_cookie('bilibili', self.format_cookie(cookie))

    async def update_cookies(self):
        """更新Cookie池"""
        # 这里可以添加从Cookie池服务获取Cookie的逻辑
        self.init_platform_cookies()

    async def check_cookie(self, platform: str, cookie: str) -> bool:
        """检查Cookie是否有效"""
        # 这里需要实现具体的Cookie检查逻辑
        return True

    async def check_all_cookies(self):
        """检查所有Cookie"""
        for platform in self.cookies:
            valid_cookies = []
            for cookie in self.cookies[platform]:
                if await self.check_cookie(platform, cookie):
                    valid_cookies.append(cookie)
            self.cookies[platform] = valid_cookies
        self.save_cookies()

    def _load_cookies(self):
        """从文件加载Cookie"""
        if os.path.exists(self.cookie_file):
            try:
                with open(self.cookie_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.cookies = data["cookies"]
                    self.expiry_times = {
                        k: datetime.fromisoformat(v)
                        for k, v in data["expiry_times"].items()
                    }
            except Exception as e:
                print(f"加载Cookie文件失败: {e}")

    def _save_cookies(self):
        """保存Cookie到文件"""
        try:
            os.makedirs(os.path.dirname(self.cookie_file), exist_ok=True)
            data = {
                "cookies": self.cookies,
                "expiry_times": {
                    k: v.isoformat() for k, v in self.expiry_times.items()
                }
            }
            with open(self.cookie_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存Cookie文件失败: {e}")

    async def get_cookies(self, domain: str) -> Dict[str, str]:
        """获取Cookie
        
        Args:
            domain: 域名
            
        Returns:
            Cookie字典
        """
        if domain not in self.cookies:
            return {}
            
        # 检查是否过期
        if domain in self.expiry_times:
            if datetime.now() > self.expiry_times[domain]:
                del self.cookies[domain]
                del self.expiry_times[domain]
                return {}
                
        return self.cookies[domain]

    def add_cookies(self, domain: str, cookies: Dict[str, str], expiry: Optional[int] = None):
        """添加Cookie
        
        Args:
            domain: 域名
            cookies: Cookie字典
            expiry: 过期时间（秒）
        """
        self.cookies[domain] = cookies
        if expiry:
            self.expiry_times[domain] = datetime.now() + timedelta(seconds=expiry)

    def clear_cookies(self, domain: Optional[str] = None):
        """清除Cookie
        
        Args:
            domain: 域名，如果为None则清除所有Cookie
        """
        if domain:
            if domain in self.cookies:
                del self.cookies[domain]
            if domain in self.expiry_times:
                del self.expiry_times[domain]
        else:
            self.cookies.clear()
            self.expiry_times.clear()

    def is_expired(self) -> bool:
        """检查Cookie是否过期

        Returns:
            bool: 是否过期
        """
        if not self.cookies:
            return True

        # 检查过期时间
        if 'expires' in self.cookies:
            try:
                expires = datetime.fromisoformat(self.cookies['expires'])
                return datetime.now() > expires
            except:
                return True

        return False

    def save_to_file(self, filename: str):
        """保存Cookie到文件
        
        Args:
            filename: 文件名
        """
        data = {
            "cookies": self.cookies,
            "expiry_times": {
                k: v.isoformat() for k, v in self.expiry_times.items()
            }
        }
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_from_file(self, filename: str):
        """从文件加载Cookie
        
        Args:
            filename: 文件名
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.cookies = data["cookies"]
                self.expiry_times = {
                    k: datetime.fromisoformat(v)
                    for k, v in data["expiry_times"].items()
                }
        except FileNotFoundError:
            logger.warning(f"Cookie文件 {filename} 不存在") 