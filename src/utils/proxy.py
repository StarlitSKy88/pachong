import os
import random
import logging
import aiohttp
import asyncio
from typing import Optional, List, Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ProxyManager:
    """代理管理器"""
    
    def __init__(self):
        """初始化代理管理器"""
        self.proxies: List[Dict] = []
        self.last_update: Optional[datetime] = None
        self.update_interval = timedelta(minutes=30)  # 代理更新间隔
        self.min_proxies = 10  # 最小代理数量
        
        # 从环境变量获取代理API配置
        self.proxy_api_url = os.getenv('PROXY_API_URL')
        self.proxy_api_key = os.getenv('PROXY_API_KEY')
        
        # 固定代理列表（从环境变量获取）
        self.static_proxies = []
        if os.getenv('HTTP_PROXY'):
            self.static_proxies.append({
                'url': os.getenv('HTTP_PROXY'),
                'protocol': 'http',
                'score': 100,
                'last_used': None
            })
        if os.getenv('HTTPS_PROXY'):
            self.static_proxies.append({
                'url': os.getenv('HTTPS_PROXY'),
                'protocol': 'https',
                'score': 100,
                'last_used': None
            })
    
    async def _fetch_proxies(self) -> List[Dict]:
        """从API获取代理列表"""
        if not self.proxy_api_url:
            return []
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.proxy_api_url,
                    headers={'Authorization': f'Bearer {self.proxy_api_key}'} if self.proxy_api_key else None
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return [
                            {
                                'url': proxy['url'],
                                'protocol': proxy.get('protocol', 'http'),
                                'score': 100,
                                'last_used': None
                            }
                            for proxy in data['proxies']
                        ]
            logger.warning(f"Failed to fetch proxies: {response.status}")
        except Exception as e:
            logger.error(f"Error fetching proxies: {str(e)}")
        
        return []
    
    async def _update_proxies(self) -> None:
        """更新代理列表"""
        # 如果距离上次更新时间不足更新间隔，且代理数量足够，则跳过
        if (
            self.last_update and
            datetime.now() - self.last_update < self.update_interval and
            len(self.proxies) >= self.min_proxies
        ):
            return
            
        # 获取新代理
        new_proxies = await self._fetch_proxies()
        
        # 添加静态代理
        new_proxies.extend(self.static_proxies)
        
        # 更新代理列表，保留评分较高的代理
        self.proxies = [
            proxy for proxy in self.proxies
            if proxy['score'] > 50 and proxy['url'] not in [p['url'] for p in new_proxies]
        ]
        self.proxies.extend(new_proxies)
        
        self.last_update = datetime.now()
        logger.info(f"Updated proxy list, total proxies: {len(self.proxies)}")
    
    def _select_proxy(self) -> Optional[Dict]:
        """选择代理"""
        if not self.proxies:
            return None
            
        # 按评分加权随机选择
        total_score = sum(proxy['score'] for proxy in self.proxies)
        if total_score <= 0:
            return random.choice(self.proxies)
            
        r = random.uniform(0, total_score)
        current_sum = 0
        for proxy in self.proxies:
            current_sum += proxy['score']
            if current_sum >= r:
                return proxy
        
        return self.proxies[-1]
    
    async def get_proxy(self) -> Optional[str]:
        """获取代理地址
        
        Returns:
            代理URL
        """
        await self._update_proxies()
        
        proxy = self._select_proxy()
        if proxy:
            proxy['last_used'] = datetime.now()
            return proxy['url']
        
        return None
    
    async def report_proxy_status(self, proxy_url: str, success: bool) -> None:
        """报告代理使用状态
        
        Args:
            proxy_url: 代理URL
            success: 是否成功
        """
        for proxy in self.proxies:
            if proxy['url'] == proxy_url:
                if success:
                    proxy['score'] = min(100, proxy['score'] + 10)
                else:
                    proxy['score'] = max(0, proxy['score'] - 20)
                break
    
    def __repr__(self) -> str:
        return f"<ProxyManager proxies={len(self.proxies)}>" 