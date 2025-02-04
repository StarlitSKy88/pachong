from typing import Dict, List, Optional, Set
import json
import time
import random
import asyncio
from datetime import datetime, timedelta
import aiohttp
import logging
from .proxy_providers import ProxyProviderManager, ZhimaProxyProvider, KuaidailiProxyProvider
from loguru import logger

class ProxyManager:
    """代理管理器"""
    
    def __init__(self):
        self.logger = logger.bind(name='proxy_manager')
        self.proxies = []  # 代理列表
        self.proxy_scores = {}  # 代理评分
        self.test_url = 'http://www.baidu.com'  # 测试URL
        self.min_score = 0  # 最低分数
        self.max_score = 100  # 最高分数
        self.proxies: Set[str] = set()  # 代理IP集合
        self.valid_proxies: Set[str] = set()  # 有效的代理IP集合
        self.last_check_time = datetime.min  # 上次检查时间
        self.check_interval = 300  # 检查间隔(秒)
        self.min_proxies = 20  # 最少代理数量
        self.timeout = 10  # 超时时间(秒)
        
        # 初始化代理服务商管理器
        self.provider_manager = ProxyProviderManager()
        self._init_providers()
    
    def _init_providers(self):
        """初始化代理服务商"""
        # 添加芝麻代理
        zhima = ZhimaProxyProvider(
            api_url='http://webapi.zhimaproxy.com/api/getip',
            api_key='your_zhima_api_key'
        )
        self.provider_manager.add_provider('zhima', zhima)
        
        # 添加快代理
        kuaidaili = KuaidailiProxyProvider(
            api_url='http://dev.kdlapi.com/api/getproxy',
            api_key='your_kuaidaili_api_key'
        )
        self.provider_manager.add_provider('kuaidaili', kuaidaili)
    
    async def add_proxy(self, proxy: str):
        """添加代理"""
        self.proxies.add(proxy)
        self.logger.info(f"Added proxy: {proxy}")
    
    async def add_proxies(self, proxies: List[str]):
        """批量添加代理"""
        self.proxies.update(proxies)
        self.logger.info(f"Added {len(proxies)} proxies")
    
    async def get_proxy(self) -> Optional[str]:
        """获取代理
        
        Returns:
            代理地址
        """
        if not self.proxies:
            await self.update_proxy_pool()
            
        # 按分数排序并随机选择前20%的代理
        valid_proxies = [p for p in self.proxies if self.proxy_scores.get(p, 0) > self.min_score]
        if not valid_proxies:
            return None
            
        top_n = max(1, len(valid_proxies) // 5)
        sorted_proxies = sorted(
            valid_proxies,
            key=lambda x: self.proxy_scores.get(x, 0),
            reverse=True
        )
        return random.choice(sorted_proxies[:top_n])
    
    async def update_proxy_pool(self):
        """更新代理池"""
        try:
            # 从代理API获取代理
            async with aiohttp.ClientSession() as session:
                async with session.get('http://localhost:5555/get_all') as response:
                    if response.status == 200:
                        proxies = await response.json()
                        if isinstance(proxies, list):
                            self.proxies = proxies
                            
            # 初始化新代理的分数
            for proxy in self.proxies:
                if proxy not in self.proxy_scores:
                    self.proxy_scores[proxy] = self.max_score
                    
            # 测试代理
            await self.check_all_proxies()
            
        except Exception as e:
            self.logger.error(f"Error updating proxy pool: {str(e)}")
    
    async def check_proxy(self, proxy: str) -> bool:
        """检查代理是否可用
        
        Args:
            proxy: 代理地址
            
        Returns:
            是否可用
        """
        try:
            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.test_url,
                    proxy=proxy,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        # 根据响应时间调整分数
                        response_time = time.time() - start_time
                        self._adjust_score(proxy, True, response_time)
                        return True
                    else:
                        self._adjust_score(proxy, False)
                        return False
        except Exception as e:
            self._adjust_score(proxy, False)
            return False
    
    async def check_all_proxies(self):
        """检查所有代理"""
        tasks = []
        for proxy in self.proxies:
            task = asyncio.create_task(self.check_proxy(proxy))
            tasks.append(task)
            
        # 限制并发数
        chunk_size = 10
        for i in range(0, len(tasks), chunk_size):
            chunk = tasks[i:i + chunk_size]
            await asyncio.gather(*chunk)
            
        # 移除分数过低的代理
        self.proxies = [p for p in self.proxies if self.proxy_scores.get(p, 0) > self.min_score]
    
    def _adjust_score(self, proxy: str, success: bool, response_time: float = None):
        """调整代理分数
        
        Args:
            proxy: 代理地址
            success: 是否成功
            response_time: 响应时间
        """
        current_score = self.proxy_scores.get(proxy, self.max_score)
        
        if success:
            # 成功时，根据响应时间调整分数
            if response_time:
                if response_time < 1:
                    current_score += 5
                elif response_time < 2:
                    current_score += 2
                elif response_time > 5:
                    current_score -= 2
        else:
            # 失败时扣分
            current_score -= 10
            
        # 限制分数范围
        current_score = max(self.min_score, min(self.max_score, current_score))
        self.proxy_scores[proxy] = current_score
    
    async def remove_proxy(self, proxy: str):
        """移除代理"""
        self.proxies.discard(proxy)
        self.valid_proxies.discard(proxy)
        self.logger.info(f"Removed proxy: {proxy}")
    
    def clear(self):
        """清空代理池"""
        self.proxies.clear()
        self.valid_proxies.clear()
        self.logger.info("Cleared proxy pool")
    
    def get_stats(self) -> Dict:
        """获取代理池统计信息"""
        return {
            'total': len(self.proxies),
            'valid': len(self.valid_proxies),
            'invalid': len(self.proxies) - len(self.valid_proxies)
        } 