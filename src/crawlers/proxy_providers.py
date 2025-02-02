from typing import Dict, List, Any, Optional
import aiohttp
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

class BaseProxyProvider(ABC):
    """代理服务商基类"""
    
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def fetch_proxies(self) -> List[str]:
        """获取代理列表"""
        pass
    
    @abstractmethod
    async def get_balance(self) -> float:
        """获取账户余额"""
        pass

class ZhimaProxyProvider(BaseProxyProvider):
    """芝麻代理服务商"""
    
    async def fetch_proxies(self) -> List[str]:
        """获取代理列表"""
        try:
            params = {
                'api_key': self.api_key,
                'order': 'asc',
                'type': 2,  # 动态代理
                'protocol': 2,  # HTTP/HTTPS
                'num': 20
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.api_url, params=params) as response:
                    if response.status == 200:
                        text = await response.text()
                        proxies = []
                        for line in text.strip().split('\n'):
                            ip, port = line.strip().split(':')
                            proxies.append(f"http://{ip}:{port}")
                        return proxies
            return []
            
        except Exception as e:
            self.logger.error(f"Error fetching proxies from Zhima: {str(e)}")
            return []
    
    async def get_balance(self) -> float:
        """获取账户余额"""
        try:
            params = {
                'api_key': self.api_key,
                'type': 'balance'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.api_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return float(data.get('balance', 0))
            return 0.0
            
        except Exception as e:
            self.logger.error(f"Error getting balance from Zhima: {str(e)}")
            return 0.0

class KuaidailiProxyProvider(BaseProxyProvider):
    """快代理服务商"""
    
    async def fetch_proxies(self) -> List[str]:
        """获取代理列表"""
        try:
            params = {
                'orderid': self.api_key,
                'num': 20,
                'protocol': 2,
                'method': 2,
                'format': 'json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.api_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('code') == 0:
                            return [
                                f"http://{proxy['ip']}:{proxy['port']}"
                                for proxy in data.get('data', {}).get('proxy_list', [])
                            ]
            return []
            
        except Exception as e:
            self.logger.error(f"Error fetching proxies from Kuaidaili: {str(e)}")
            return []
    
    async def get_balance(self) -> float:
        """获取账户余额"""
        try:
            params = {
                'orderid': self.api_key,
                'format': 'json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/balance", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('code') == 0:
                            return float(data.get('data', {}).get('balance', 0))
            return 0.0
            
        except Exception as e:
            self.logger.error(f"Error getting balance from Kuaidaili: {str(e)}")
            return 0.0

class ProxyProviderManager:
    """代理服务商管理器"""
    
    def __init__(self):
        self.providers: Dict[str, BaseProxyProvider] = {}
        self.logger = logging.getLogger('ProxyProviderManager')
        
    def add_provider(self, name: str, provider: BaseProxyProvider):
        """添加代理服务商"""
        self.providers[name] = provider
        self.logger.info(f"Added proxy provider: {name}")
    
    def remove_provider(self, name: str):
        """移除代理服务商"""
        if name in self.providers:
            del self.providers[name]
            self.logger.info(f"Removed proxy provider: {name}")
    
    async def fetch_all_proxies(self) -> List[str]:
        """从所有服务商获取代理"""
        all_proxies = []
        for name, provider in self.providers.items():
            try:
                proxies = await provider.fetch_proxies()
                self.logger.info(f"Fetched {len(proxies)} proxies from {name}")
                all_proxies.extend(proxies)
            except Exception as e:
                self.logger.error(f"Error fetching proxies from {name}: {str(e)}")
        return all_proxies
    
    async def check_balances(self) -> Dict[str, float]:
        """检查所有服务商的余额"""
        balances = {}
        for name, provider in self.providers.items():
            try:
                balance = await provider.get_balance()
                balances[name] = balance
                self.logger.info(f"Provider {name} balance: {balance}")
            except Exception as e:
                self.logger.error(f"Error checking balance for {name}: {str(e)}")
                balances[name] = 0.0
        return balances
    
    def get_provider(self, name: str) -> Optional[BaseProxyProvider]:
        """获取代理服务商"""
        return self.providers.get(name)
    
    def get_all_providers(self) -> Dict[str, BaseProxyProvider]:
        """获取所有代理服务商"""
        return self.providers 