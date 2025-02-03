import random
import time
from typing import Optional, List, Dict, Set
import requests
from requests.exceptions import RequestException
import logging
import aiohttp
import asyncio
from datetime import datetime, timedelta
import json
from dataclasses import dataclass, asdict
from enum import Enum
from .proxy_providers import ProxyProviderManager
from loguru import logger
import os

class ProxyAnonymity(str, Enum):
    """代理匿名度级别"""
    TRANSPARENT = "transparent"  # 透明代理
    ANONYMOUS = "anonymous"     # 普通匿名
    HIGH_ANONYMOUS = "high_anonymous"  # 高匿名

@dataclass
class ProxyInfo:
    """代理信息"""
    url: str                # 代理地址
    anonymity: ProxyAnonymity = ProxyAnonymity.TRANSPARENT  # 匿名度
    response_time: float = float('inf')  # 响应时间(秒)
    success_count: int = 0  # 成功次数
    fail_count: int = 0     # 失败次数
    last_check: datetime = None  # 最后检查时间
    score: float = 50.0     # 代理评分(0-100)
    consecutive_failures: int = 0  # 连续失败次数
    is_valid: bool = False  # 是否可用
    
    @property
    def success_rate(self) -> float:
        """计算成功率"""
        total = self.success_count + self.fail_count
        return self.success_count / total if total > 0 else 0
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)

class ProxyManager:
    """代理池管理器"""
    
    def __init__(self):
        self.proxies: Dict[str, ProxyInfo] = {}  # 代理信息字典
        self.provider_manager = ProxyProviderManager()  # 代理源管理器
        self.logger = logger.bind(name="proxy_manager")  # 初始化logger
        
        # 配置参数
        self.check_urls = [
            'https://www.baidu.com',
            'https://www.taobao.com',
            'https://www.jd.com'
        ]
        self.timeout = 10  # 超时时间(秒)
        self.min_proxies = 20  # 最少代理数量
        self.check_interval = 300  # 检查间隔(秒)
        self.last_check_time = datetime.min  # 上次检查时间
        self.min_score = 0  # 最低分数
        self.max_score = 100  # 最高分数
        self.max_consecutive_failures = 3  # 最大连续失败次数
        self.min_success_rate = 0.7  # 最低成功率
        self.max_fails = 3  # 最大失败次数
        self.last_check = {}  # 最后检查时间
        self.fail_counts = {}  # 失败次数统计
        self.success_counts = {}  # 成功次数统计
        
        self.logger.info("ProxyManager initialized")
        
        self.proxy_file = "data/proxies.json"
        self.load_proxies()
    
    def load_proxies(self):
        """从文件加载代理"""
        try:
            if os.path.exists(self.proxy_file):
                with open(self.proxy_file, 'r') as f:
                    self.proxies = json.load(f)
        except Exception as e:
            print(f"加载代理失败: {str(e)}")
    
    def save_proxies(self):
        """保存代理到文件"""
        try:
            os.makedirs(os.path.dirname(self.proxy_file), exist_ok=True)
            with open(self.proxy_file, 'w') as f:
                json.dump(self.proxies, f)
        except Exception as e:
            print(f"保存代理失败: {str(e)}")
    
    async def get_proxy(self) -> Optional[str]:
        """获取可用代理"""
        available_proxies = []
        current_time = datetime.now()
        
        for proxy in self.proxies:
            # 检查失败次数
            if self.fail_counts.get(proxy, 0) >= self.max_fails:
                continue
                
            # 检查成功率
            total = self.success_counts.get(proxy, 0) + self.fail_counts.get(proxy, 0)
            if total > 10:  # 至少有10次请求才计算成功率
                success_rate = self.success_counts.get(proxy, 0) / total
                if success_rate < self.min_success_rate:
                    continue
                    
            # 检查是否需要等待
            last_time = self.last_check.get(proxy)
            if last_time and (current_time - last_time).total_seconds() < self.check_interval:
                continue
                
            available_proxies.append(proxy)
            
        if not available_proxies:
            return None
            
        return random.choice(available_proxies)
    
    async def check_proxy(self, proxy: str) -> Optional[ProxyInfo]:
        """检查代理可用性"""
        info = self.proxies.get(proxy, ProxyInfo(url=proxy))
        info.last_check = datetime.now()
        
        try:
            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                # 随机选择一个检查URL
                url = random.choice(self.check_urls)
                self.logger.debug(f"Checking proxy {proxy} with {url}")
                async with session.get(
                    url,
                    proxy=proxy,
                    timeout=self.timeout,
                    verify_ssl=False  # 禁用SSL验证
                ) as response:
                    if response.status == 200:
                        info.response_time = time.time() - start_time
                        info.success_count += 1
                        info.score = min(self.max_score, info.score + 10)
                        info.consecutive_failures = 0
                        info.is_valid = True
                        
                        # 检查匿名度
                        info.anonymity = await self.check_anonymity(proxy)
                        self.logger.info(f"Proxy {proxy} check success (response time: {info.response_time:.2f}s, score: {info.score:.1f})")
                        return info
                    else:
                        self.logger.warning(f"Proxy {proxy} check failed with status {response.status}")
                        info.fail_count += 1
                        info.consecutive_failures += 1
                        info.score = max(self.min_score, info.score - 10)
                        info.is_valid = False
                        
        except Exception as e:
            self.logger.debug(f"Proxy {proxy} check failed: {e}")
            info.fail_count += 1
            info.consecutive_failures += 1
            info.score = max(self.min_score, info.score - 20)
            info.is_valid = False
            
        # 连续失败次数过多，直接移除
        if info.consecutive_failures >= self.max_consecutive_failures:
            if proxy in self.proxies:
                del self.proxies[proxy]
            return None
            
        return None
    
    async def check_anonymity(self, proxy: str) -> ProxyAnonymity:
        """检查代理匿名度"""
        try:
            self.logger.debug(f"Checking anonymity for proxy {proxy}")
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'http://httpbin.org/ip',
                    proxy=proxy,
                    timeout=self.timeout,
                    verify_ssl=False  # 禁用SSL验证
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        proxy_ip = data.get('origin', '')
                        
                        # 检查请求头
                        async with session.get(
                            'http://httpbin.org/headers',
                            proxy=proxy,
                            timeout=self.timeout,
                            verify_ssl=False  # 禁用SSL验证
                        ) as response:
                            if response.status == 200:
                                headers = (await response.json()).get('headers', {})
                                proxy_headers = ['Via', 'Proxy-Connection', 'X-Forwarded-For']
                                
                                if not any(h in headers for h in proxy_headers):
                                    self.logger.info(f"Proxy {proxy} is high anonymous")
                                    return ProxyAnonymity.HIGH_ANONYMOUS
                                elif 'X-Forwarded-For' not in headers:
                                    self.logger.info(f"Proxy {proxy} is anonymous")
                                    return ProxyAnonymity.ANONYMOUS
                                    
        except Exception as e:
            self.logger.debug(f"Anonymity check failed for {proxy}: {e}")
            
        self.logger.info(f"Proxy {proxy} is transparent")
        return ProxyAnonymity.TRANSPARENT
    
    async def update_proxy_pool(self):
        """更新代理池"""
        now = datetime.now()
        if (now - self.last_check_time).total_seconds() < self.check_interval:
            self.logger.debug("Skip proxy pool update due to check interval")
            return
            
        self.last_check_time = now
        self.logger.info("Start updating proxy pool")
        
        # 获取新代理
        new_proxies = await self.provider_manager.get_all_proxies()
        self.logger.info(f"Fetched {len(new_proxies)} new proxies")
        
        # 检查新代理
        tasks = []
        for proxy in new_proxies:
            if proxy not in self.proxies:
                tasks.append(self.check_proxy(proxy))
                
        results = await asyncio.gather(*tasks)
        
        # 更新代理池
        valid_count = 0
        for info in results:
            if info and info.is_valid:
                self.proxies[info.url] = info
                valid_count += 1
                
        # 移除失效代理
        removed_count = 0
        for proxy in list(self.proxies.keys()):
            info = self.proxies[proxy]
            if (
                info.score <= self.min_score or
                not info.is_valid or
                info.consecutive_failures >= self.max_consecutive_failures or
                (info.success_count + info.fail_count >= 10 and info.success_rate < self.min_success_rate) or
                (info.last_check and (now - info.last_check).total_seconds() > 3600)
            ):
                del self.proxies[proxy]
                removed_count += 1
                
        self.logger.info(f"Proxy pool updated: {valid_count} new valid proxies, {removed_count} removed, {len(self.proxies)} total")
    
    async def report_result(self, proxy: str, success: bool):
        """报告代理使用结果"""
        if proxy in self.proxies:
            info = self.proxies[proxy]
            if success:
                info.success_count += 1
                info.score = min(self.max_score, info.score + 5)
                info.consecutive_failures = 0
                info.is_valid = True
                self.logger.info(f"Proxy {proxy} success reported (score: {info.score:.1f})")
            else:
                info.fail_count += 1
                info.score = max(self.min_score, info.score - 10)
                info.consecutive_failures += 1
                if info.consecutive_failures >= self.max_consecutive_failures:
                    del self.proxies[proxy]
                    self.logger.warning(f"Proxy {proxy} removed due to consecutive failures")
                else:
                    self.logger.warning(f"Proxy {proxy} failure reported (score: {info.score:.1f})")
                
    def get_stats(self) -> Dict:
        """获取代理池统计信息"""
        valid_proxies = [p for p in self.proxies.values() if p.score > self.min_score and p.is_valid]
        stats = {
            'total': len(self.proxies),
            'valid': len(valid_proxies),
            'high_anonymous': len([p for p in valid_proxies if p.anonymity == ProxyAnonymity.HIGH_ANONYMOUS]),
            'anonymous': len([p for p in valid_proxies if p.anonymity == ProxyAnonymity.ANONYMOUS]),
            'transparent': len([p for p in valid_proxies if p.anonymity == ProxyAnonymity.TRANSPARENT]),
            'avg_response_time': sum(p.response_time for p in valid_proxies) / len(valid_proxies) if valid_proxies else 0,
            'avg_success_rate': sum(p.success_rate for p in valid_proxies) / len(valid_proxies) if valid_proxies else 0
        }
        self.logger.info(f"Proxy pool stats: {stats}")
        return stats

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

    def update_proxy_status(self, proxy: str, success: bool):
        """更新代理状态"""
        if success:
            self.success_counts[proxy] = self.success_counts.get(proxy, 0) + 1
            self.fail_counts[proxy] = 0  # 重置失败计数
        else:
            self.fail_counts[proxy] = self.fail_counts.get(proxy, 0) + 1
            
        self.last_check[proxy] = datetime.now()

    def remove_invalid_proxies(self):
        """清理无效代理"""
        for proxy in list(self.proxies):
            if self.fail_counts.get(proxy, 0) >= self.max_fails:
                del self.proxies[proxy]
                self.fail_counts.pop(proxy, None)
                self.success_counts.pop(proxy, None)
                self.last_check.pop(proxy, None)

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
        if proxy not in self.proxies and await self.check_proxy(proxy):
            self.proxies[proxy] = await self.check_proxy(proxy)
            self.save_proxies()
    
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
            del self.proxies[proxy]
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