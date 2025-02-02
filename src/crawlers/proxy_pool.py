import aiohttp
import asyncio
from typing import List, Set, Optional
import random
import time
from datetime import datetime, timedelta

class ProxyPool:
    """代理IP池管理类"""
    
    def __init__(self):
        self.proxies: Set[str] = set()  # 代理IP集合
        self.valid_proxies: Set[str] = set()  # 有效的代理IP集合
        self.last_check_time: datetime = datetime.min  # 上次检查时间
        self.check_interval: int = 300  # 检查间隔(秒)
        self.timeout: int = 10  # 超时时间(秒)
        
    async def add_proxy(self, proxy: str):
        """添加代理"""
        self.proxies.add(proxy)
    
    async def add_proxies(self, proxies: List[str]):
        """批量添加代理"""
        self.proxies.update(proxies)
    
    def get_random_proxy(self) -> Optional[str]:
        """获取随机代理"""
        if not self.valid_proxies:
            return None
        return random.choice(list(self.valid_proxies))
    
    async def check_proxy(self, proxy: str) -> bool:
        """检查代理是否可用"""
        try:
            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                async with session.get(
                    'https://www.baidu.com',
                    proxy=proxy,
                    timeout=self.timeout
                ) as response:
                    if response.status == 200 and time.time() - start_time < self.timeout:
                        return True
        except:
            pass
        return False
    
    async def check_all_proxies(self):
        """检查所有代理"""
        now = datetime.now()
        if (now - self.last_check_time).total_seconds() < self.check_interval:
            return
        
        self.last_check_time = now
        self.valid_proxies.clear()
        
        tasks = []
        for proxy in self.proxies:
            task = asyncio.create_task(self.check_proxy(proxy))
            tasks.append((proxy, task))
        
        for proxy, task in tasks:
            try:
                is_valid = await task
                if is_valid:
                    self.valid_proxies.add(proxy)
            except:
                continue
    
    async def remove_proxy(self, proxy: str):
        """移除代理"""
        self.proxies.discard(proxy)
        self.valid_proxies.discard(proxy)
    
    def clear(self):
        """清空代理池"""
        self.proxies.clear()
        self.valid_proxies.clear()
    
    @property
    def proxy_count(self) -> int:
        """获取代理总数"""
        return len(self.proxies)
    
    @property
    def valid_proxy_count(self) -> int:
        """获取有效代理数"""
        return len(self.valid_proxies)
    
    async def fetch_proxies(self):
        """从代理服务商获取代理
        这里需要实现具体的代理获取逻辑
        """
        pass 