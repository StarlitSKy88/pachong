from typing import Dict, Optional
import json
import os
import aiohttp
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CookieManager:
    """Cookie管理器"""

    def __init__(self, platform_name: str = None):
        """初始化Cookie管理器
        
        Args:
            platform_name: 平台名称
        """
        self.platform_name = platform_name
        self.cookies = {}
        self.expiry_times = {}
        self.cookie_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'cookies.json')
        if platform_name:
            self.cookie_file = os.path.join(os.path.dirname(__file__), '..', 'data', f'cookies_{platform_name}.json')
        self._load_cookies()

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