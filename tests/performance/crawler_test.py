"""爬虫性能测试

该模块实现了爬虫系统的性能测试，包括：
1. 爬虫并发测试
2. 代理性能测试
3. 请求限流测试
4. 错误处理测试
"""

import logging
import asyncio
import psutil
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime
import random
import json
from pathlib import Path

from .base import PerformanceTest
from .config import TEST_SCENARIOS, PERFORMANCE_BASELINE, TEST_DATA

logger = logging.getLogger(__name__)

class CrawlerPerformanceTest(PerformanceTest):
    """爬虫性能测试类"""
    
    def __init__(
        self,
        name: str,
        platform: str,
        load_level: str = 'normal_load',
        output_dir: Optional[str] = None
    ):
        super().__init__(
            name=name,
            component='crawler',
            scenario='crawler',
            load_level=load_level,
            output_dir=output_dir
        )
        
        self.platform = platform
        
        # 测试数据
        self.test_urls: List[str] = []
        self.test_cookies: List[Dict] = []
        self.test_proxies: List[str] = []
        
        # 会话管理
        self.session: Optional[aiohttp.ClientSession] = None
        self.semaphore: Optional[asyncio.Semaphore] = None
        
        # 统计数据
        self.request_count = 0
        self.error_count = 0
        self.total_response_time = 0
    
    async def prepare_test_data(self):
        """准备测试数据"""
        self.logger.info("Preparing test data")
        
        # 加载测试URL
        urls_file = Path(f'tests/data/{self.platform}_urls.txt')
        if urls_file.exists():
            self.test_urls = urls_file.read_text().splitlines()
        else:
            # 生成测试URL
            self.test_urls = [
                f"https://example.com/{self.platform}/item/{i}"
                for i in range(self.test_data['data_size'][self.load_level])
            ]
            
            # 保存测试URL
            urls_file.parent.mkdir(parents=True, exist_ok=True)
            urls_file.write_text('\n'.join(self.test_urls))
        
        self.logger.info(f"Prepared {len(self.test_urls)} test URLs")
        
        # 加载测试Cookie
        cookies_file = Path(f'tests/data/{self.platform}_cookies.json')
        if cookies_file.exists():
            self.test_cookies = json.loads(cookies_file.read_text())
        else:
            # 生成测试Cookie
            self.test_cookies = [
                {'session': f'test_session_{i}'}
                for i in range(10)
            ]
            
            # 保存测试Cookie
            cookies_file.parent.mkdir(parents=True, exist_ok=True)
            cookies_file.write_text(json.dumps(self.test_cookies, indent=2))
        
        self.logger.info(f"Prepared {len(self.test_cookies)} test cookies")
        
        # 加载测试代理
        proxies_file = Path(f'tests/data/proxies.txt')
        if proxies_file.exists():
            self.test_proxies = proxies_file.read_text().splitlines()
        else:
            # 生成测试代理
            self.test_proxies = [
                f"http://proxy{i}.example.com:8080"
                for i in range(10)
            ]
            
            # 保存测试代理
            proxies_file.parent.mkdir(parents=True, exist_ok=True)
            proxies_file.write_text('\n'.join(self.test_proxies))
        
        self.logger.info(f"Prepared {len(self.test_proxies)} test proxies")
    
    async def prepare_environment(self):
        """准备测试环境"""
        self.logger.info("Preparing test environment")
        
        # 创建会话
        self.session = aiohttp.ClientSession()
        
        # 创建并发限制
        concurrent_users = self.config['current_scenario']['concurrent_users']
        self.semaphore = asyncio.Semaphore(concurrent_users)
        
        self.logger.info(f"Set concurrent users to {concurrent_users}")
        
        # 重置统计数据
        self.request_count = 0
        self.error_count = 0
        self.total_response_time = 0
    
    async def run_test(self):
        """运行测试"""
        self.logger.info("Running crawler performance test")
        
        try:
            # 创建请求任务
            tasks = []
            for url in self.test_urls:
                task = asyncio.create_task(self._make_request(url))
                tasks.append(task)
            
            # 等待所有任务完成
            await asyncio.gather(*tasks)
            
        finally:
            # 关闭会话
            if self.session:
                await self.session.close()
    
    async def _make_request(self, url: str):
        """发送请求"""
        async with self.semaphore:
            start_time = datetime.now()
            
            try:
                # 随机选择Cookie和代理
                cookie = random.choice(self.test_cookies)
                proxy = random.choice(self.test_proxies)
                
                # 发送请求
                async with self.session.get(
                    url,
                    cookies=cookie,
                    proxy=proxy,
                    timeout=30
                ) as response:
                    # 读取响应
                    await response.text()
                    
                    # 计算响应时间
                    response_time = (datetime.now() - start_time).total_seconds() * 1000
                    
                    # 记录指标
                    self.record_metric('response_time', response_time)
                    self.total_response_time += response_time
                    self.request_count += 1
                    
                    # 计算错误率
                    if response.status >= 400:
                        self.error_count += 1
                        error_rate = self.error_count / self.request_count
                        self.record_metric('error_rate', error_rate)
                    
                    # 计算吞吐量
                    elapsed = (datetime.now() - self.start_time).total_seconds()
                    if elapsed > 0:
                        throughput = self.request_count / elapsed
                        self.record_metric('throughput', throughput)
                    
            except Exception as e:
                self.logger.error(f"Request failed: {e}")
                self.error_count += 1
                error_rate = self.error_count / (self.request_count + 1)
                self.record_metric('error_rate', error_rate)
    
    async def get_cpu_usage(self) -> float:
        """获取CPU使用率"""
        return psutil.cpu_percent()
    
    async def get_memory_usage(self) -> float:
        """获取内存使用率"""
        return psutil.virtual_memory().percent
    
    async def get_disk_usage(self) -> float:
        """获取磁盘使用率"""
        return psutil.disk_usage('/').percent 