import random
import time
from typing import Optional, List, Dict
import requests
from requests.exceptions import RequestException
import logging
import aiohttp
import asyncio
from datetime import datetime, timedelta
import json
from dataclasses import dataclass, asdict
from enum import Enum

class ProxyAnonymity(str, Enum):
    """代理匿名度级别"""
    TRANSPARENT = "transparent"  # 透明代理
    ANONYMOUS = "anonymous"     # 普通匿名
    HIGH_ANONYMOUS = "high_anonymous"  # 高匿名

@dataclass
class ProxyStatus:
    """代理状态"""
    proxy: str                      # 代理地址
    is_valid: bool = False          # 是否可用
    anonymity: ProxyAnonymity = ProxyAnonymity.TRANSPARENT  # 匿名度
    response_time: float = float('inf')  # 响应时间(秒)
    success_count: int = 0          # 成功次数
    fail_count: int = 0            # 失败次数
    last_check_time: datetime = None  # 最后检查时间
    last_success_time: datetime = None  # 最后成功时间
    consecutive_failures: int = 0    # 连续失败次数
    
    @property
    def success_rate(self) -> float:
        """计算成功率"""
        total = self.success_count + self.fail_count
        return self.success_count / total if total > 0 else 0
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)

class ProxyManager:
    def __init__(self):
        self.proxies = []  # 代理列表
        self.proxy_scores = {}  # 代理评分
        self.test_url = 'http://www.baidu.com'  # 测试URL
        self.min_score = 0  # 最低分数
        self.max_score = 100  # 最高分数
        self.last_check_time = datetime.min  # 上次检查时间
        self.check_interval = 300  # 检查间隔(秒)
        self.min_proxies = 20  # 最少代理数量
        self.timeout = 10  # 超时时间(秒)
        
        # 初始化一些测试代理
        self._init_test_proxies()
        
    def _init_test_proxies(self):
        """初始化测试代理"""
        test_proxies = [
            "http://test1.proxy:8080",
            "http://test2.proxy:8080",
            "http://test3.proxy:8080"
        ]
        for proxy in test_proxies:
            self.proxies.append(proxy)
            self.proxy_scores[proxy] = self.max_score
    
    async def get_proxy(self) -> Optional[str]:
        """获取代理
        
        Returns:
            Optional[str]: 代理地址
        """
        if not self.proxies:
            await self.update_proxy_pool()
            
        # 按分数排序并随机选择前20%的代理
        valid_proxies = [p for p in self.proxies if self.proxy_scores.get(p, 0) > self.min_score]
        if not valid_proxies:
            logger.warning("没有可用的代理")
            return self.proxies[0] if self.proxies else None
            
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
            logger.error(f"Error updating proxy pool: {str(e)}")
            # 如果更新失败,使用测试代理
            self._init_test_proxies()
    
    async def check_proxy(self, proxy: str) -> bool:
        """检查代理是否可用
        
        Args:
            proxy: 代理地址
            
        Returns:
            bool: 是否可用
        """
        try:
            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.test_url,
                    proxy=proxy,
                    timeout=self.timeout
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

    def _fetch_proxies(self) -> List[Dict[str, str]]:
        """
        从代理服务商获取代理IP
        这里需要替换为实际的代理获取逻辑
        """
        # TODO: 对接具体的代理服务商API
        # 这里是示例代理，实际使用时需要替换为真实的代理服务
        return [
            {"http": "http://proxy1.example.com:8080"},
            {"http": "http://proxy2.example.com:8080"},
            # 添加更多代理
        ]

    def _test_proxy(self, proxy: Dict[str, str]) -> bool:
        """测试代理是否可用"""
        try:
            response = requests.get(
                self.test_url,
                proxies=proxy,
                timeout=5
            )
            return response.status_code == 200
        except RequestException:
            return False

    def update_proxy_pool(self):
        """更新代理池"""
        current_time = time.time()
        if current_time - self.last_update_time < self.update_interval:
            return

        self.logger.info("正在更新代理池...")
        new_proxies = self._fetch_proxies()
        valid_proxies = []

        for proxy in new_proxies:
            if self._test_proxy(proxy):
                valid_proxies.append(proxy)

        self.proxies = valid_proxies
        self.last_update_time = current_time
        self.logger.info(f"代理池更新完成，当前可用代理数量: {len(self.proxies)}")

    def remove_proxy(self, proxy: Dict[str, str]):
        """移除无效代理"""
        if proxy in self.proxies:
            self.proxies.remove(proxy)
            self.logger.info(f"移除无效代理: {proxy}")

    def get_proxy_with_retry(self) -> Optional[Dict[str, str]]:
        """获取代理，如果失败则重试"""
        for _ in range(self.max_retry_times):
            proxy = self.get_proxy()
            if proxy and self._test_proxy(proxy):
                return proxy
            if proxy:
                self.remove_proxy(proxy)
            time.sleep(1)
        return None

    async def add_proxy(self, proxy: str):
        """添加代理"""
        if proxy not in self.proxies:
            self.proxies.append(proxy)
            self.logger.info(f"Added proxy: {proxy}")
    
    async def add_proxies(self, proxies: List[str]):
        """批量添加代理"""
        for proxy in proxies:
            await self.add_proxy(proxy)
        self.logger.info(f"Added {len(proxies)} proxies")
    
    def get_random_proxy(self) -> Optional[str]:
        """获取随机代理"""
        # 过滤出可用且成功率达标的代理
        valid_proxies = [
            proxy for proxy in self.proxies
            if self.proxy_scores.get(proxy, 0) > self.min_score
        ]
        if not valid_proxies:
            return None
        return random.choice(valid_proxies)
    
    async def check_proxy_anonymity(self, proxy: str) -> ProxyAnonymity:
        """检查代理匿名度"""
        try:
            # 使用特定的检测网站
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'http://httpbin.org/ip',
                    proxy=proxy,
                    timeout=self.timeout
                ) as response:
                    if response.status != 200:
                        return ProxyAnonymity.TRANSPARENT
                    
                    data = await response.json()
                    proxy_ip = data.get('origin', '')
                    
                    # 检查请求头
                    async with session.get(
                        'http://httpbin.org/headers',
                        proxy=proxy,
                        timeout=self.timeout
                    ) as response:
                        if response.status != 200:
                            return ProxyAnonymity.TRANSPARENT
                        
                        headers_data = await response.json()
                        headers = headers_data.get('headers', {})
                        
                        # 检查是否包含代理相关头部
                        proxy_headers = ['Via', 'Proxy-Connection', 'X-Forwarded-For']
                        has_proxy_headers = any(h in headers for h in proxy_headers)
                        
                        if not has_proxy_headers and 'X-Real-IP' not in headers:
                            return ProxyAnonymity.HIGH_ANONYMOUS
                        elif not has_proxy_headers:
                            return ProxyAnonymity.ANONYMOUS
                        else:
                            return ProxyAnonymity.TRANSPARENT
                            
        except Exception as e:
            self.logger.error(f"Error checking proxy anonymity {proxy}: {str(e)}")
            return ProxyAnonymity.TRANSPARENT
    
    async def check_proxy(self, proxy: str) -> bool:
        """检查代理是否可用"""
        status = self.proxies[proxy]
        status.last_check_time = datetime.now()
        
        try:
            # 测试响应时间
            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'https://www.baidu.com',
                    proxy=proxy,
                    timeout=self.timeout
                ) as response:
                    if response.status != 200:
                        raise Exception(f"Bad status code: {response.status}")
                    
                    # 更新响应时间
                    status.response_time = time.time() - start_time
                    
                    # 检查匿名度
                    status.anonymity = await self.check_proxy_anonymity(proxy)
                    
                    # 更新统计信息
                    status.is_valid = True
                    status.success_count += 1
                    status.consecutive_failures = 0
                    status.last_success_time = datetime.now()
                    
                    return True
                    
        except Exception as e:
            self.logger.error(f"Error checking proxy {proxy}: {str(e)}")
            status.is_valid = False
            status.fail_count += 1
            status.consecutive_failures += 1
            
            # 连续失败次数过多，直接移除
            if status.consecutive_failures >= self.max_consecutive_failures:
                await self.remove_proxy(proxy)
                
            return False
    
    async def check_all_proxies(self):
        """检查所有代理"""
        now = datetime.now()
        if (now - self.last_check_time).total_seconds() < self.check_interval:
            return
        
        self.last_check_time = now
        self.logger.info("Start checking all proxies")
        
        tasks = []
        for proxy in list(self.proxies.keys()):
            task = asyncio.create_task(self.check_proxy(proxy))
            tasks.append((proxy, task))
        
        for proxy, task in tasks:
            try:
                await task
            except Exception as e:
                self.logger.error(f"Error checking proxy {proxy}: {str(e)}")
                continue
        
        # 清理无效代理
        await self.clean_invalid_proxies()
        
        self.logger.info(f"Finished checking proxies. Valid: {len([p for p in self.proxies.values() if p.is_valid])}")
    
    async def clean_invalid_proxies(self):
        """清理无效代理"""
        # 移除连续失败次数过多的代理
        for proxy, status in list(self.proxies.items()):
            if status.consecutive_failures >= self.max_consecutive_failures:
                await self.remove_proxy(proxy)
                continue
            
            # 移除成功率过低的代理
            if status.success_count + status.fail_count >= 10 and status.success_rate < self.min_success_rate:
                await self.remove_proxy(proxy)
                continue
            
            # 移除响应时间过长的代理
            if status.response_time > self.timeout:
                await self.remove_proxy(proxy)
                continue
    
    async def remove_proxy(self, proxy: str):
        """移除代理"""
        if proxy in self.proxies:
            self.proxies.remove(proxy)
            self.logger.info(f"Removed proxy: {proxy}")
    
    def clear(self):
        """清空代理池"""
        self.proxies.clear()
        self.logger.info("Cleared proxy pool")
    
    async def update_proxy_pool(self):
        """更新代理池"""
        # 检查代理数量是否足够
        valid_count = len([p for p in self.proxies.values() if p.is_valid])
        if valid_count >= self.min_proxies:
            return
            
        self.logger.info("Start updating proxy pool")
        
        # 从代理服务商获取新代理
        new_proxies = await self.fetch_proxies()
        if new_proxies:
            await self.add_proxies(new_proxies)
        
        # 检查新代理的可用性
        await self.check_all_proxies()
        
        self.logger.info("Finished updating proxy pool")
    
    async def fetch_proxies(self) -> List[str]:
        """从代理服务商获取代理
        这里需要实现具体的代理获取逻辑
        """
        # TODO: 实现代理获取逻辑
        return []
    
    def get_proxy_status(self, proxy: str) -> Optional[Dict]:
        """获取代理状态"""
        if proxy in self.proxies:
            return self.proxies[proxy].to_dict()
        return None
    
    def get_all_status(self) -> List[Dict]:
        """获取所有代理状态"""
        return [status.to_dict() for status in self.proxies.values()]
    
    def get_stats(self) -> Dict:
        """获取代理池统计信息"""
        valid_proxies = [p for p in self.proxies.values() if p.is_valid]
        return {
            'total': len(self.proxies),
            'valid': len(valid_proxies),
            'invalid': len(self.proxies) - len(valid_proxies),
            'high_anonymous': len([p for p in valid_proxies if p.anonymity == ProxyAnonymity.HIGH_ANONYMOUS]),
            'anonymous': len([p for p in valid_proxies if p.anonymity == ProxyAnonymity.ANONYMOUS]),
            'transparent': len([p for p in valid_proxies if p.anonymity == ProxyAnonymity.TRANSPARENT]),
            'avg_response_time': sum(p.response_time for p in valid_proxies) / len(valid_proxies) if valid_proxies else 0,
            'avg_success_rate': sum(p.success_rate for p in valid_proxies) / len(valid_proxies) if valid_proxies else 0
        } 