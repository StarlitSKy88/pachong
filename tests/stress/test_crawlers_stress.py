"""爬虫系统压力测试"""

import pytest
import asyncio
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, List
from src.crawlers.bilibili_crawler import BiliBiliCrawler
from src.crawlers.xiaohongshu_crawler import XiaoHongShuCrawler
from src.database import content_dao, platform_dao
from src.models.content import Content

class StressTestMetrics:
    """压力测试指标收集器"""
    
    def __init__(self):
        """初始化指标收集器"""
        self.start_time = datetime.now()
        self.request_count = 0
        self.error_count = 0
        self.success_count = 0
        self.response_times = []
        self.cpu_usages = []
        self.memory_usages = []
        
    def record_request(self, success: bool, response_time: float):
        """记录请求结果
        
        Args:
            success: 是否成功
            response_time: 响应时间（秒）
        """
        self.request_count += 1
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
        self.response_times.append(response_time)
        
    def record_resource_usage(self):
        """记录资源使用情况"""
        self.cpu_usages.append(psutil.cpu_percent())
        self.memory_usages.append(psutil.Process().memory_info().rss / 1024 / 1024)
        
    def get_summary(self) -> Dict:
        """获取测试结果摘要
        
        Returns:
            Dict: 测试结果摘要
        """
        duration = (datetime.now() - self.start_time).total_seconds()
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        
        return {
            "duration": duration,
            "total_requests": self.request_count,
            "success_rate": self.success_count / self.request_count if self.request_count else 0,
            "avg_response_time": avg_response_time,
            "max_response_time": max(self.response_times) if self.response_times else 0,
            "avg_cpu_usage": sum(self.cpu_usages) / len(self.cpu_usages) if self.cpu_usages else 0,
            "max_cpu_usage": max(self.cpu_usages) if self.cpu_usages else 0,
            "avg_memory_usage": sum(self.memory_usages) / len(self.memory_usages) if self.memory_usages else 0,
            "max_memory_usage": max(self.memory_usages) if self.memory_usages else 0
        }

@pytest.fixture
async def crawlers():
    """创建爬虫实例"""
    bilibili = BiliBiliCrawler(
        concurrent_limit=10,  # 增加并发限制
        retry_limit=3,
        timeout=10
    )
    xiaohongshu = XiaoHongShuCrawler(
        concurrent_limit=10,
        retry_limit=3,
        timeout=10
    )
    
    async with bilibili, xiaohongshu:
        yield {
            "bilibili": bilibili,
            "xiaohongshu": xiaohongshu
        }

async def run_crawler_task(
    crawler,
    keywords: List[str],
    metrics: StressTestMetrics
):
    """运行爬虫任务
    
    Args:
        crawler: 爬虫实例
        keywords: 关键词列表
        metrics: 指标收集器
    """
    start_time = time.time()
    try:
        results = await crawler.crawl(
            keywords=keywords,
            time_range="24h",
            limit=10
        )
        success = len(results) > 0
    except Exception:
        success = False
    finally:
        duration = time.time() - start_time
        metrics.record_request(success, duration)

@pytest.mark.asyncio
async def test_high_concurrency(crawlers):
    """测试高并发"""
    metrics = StressTestMetrics()
    keywords = ["Python", "AI", "数据", "编程", "开发"]
    tasks = []
    
    # 创建100个并发任务
    for _ in range(100):
        for crawler in crawlers.values():
            task = asyncio.create_task(
                run_crawler_task(
                    crawler=crawler,
                    keywords=keywords,
                    metrics=metrics
                )
            )
            tasks.append(task)
            
        # 每10个任务记录一次资源使用情况
        if len(tasks) % 10 == 0:
            metrics.record_resource_usage()
    
    # 等待所有任务完成
    await asyncio.gather(*tasks)
    
    # 获取测试结果
    summary = metrics.get_summary()
    
    # 验证结果
    assert summary["success_rate"] > 0.9  # 成功率大于90%
    assert summary["avg_response_time"] < 5  # 平均响应时间小于5秒
    assert summary["avg_cpu_usage"] < 80  # 平均CPU使用率小于80%
    assert summary["avg_memory_usage"] < 1024  # 平均内存使用小于1GB
    
@pytest.mark.asyncio
async def test_long_running(crawlers):
    """测试长时间运行"""
    metrics = StressTestMetrics()
    keywords = ["Python", "AI", "数据"]
    duration = 300  # 运行5分钟
    
    start_time = time.time()
    while time.time() - start_time < duration:
        tasks = []
        
        # 创建10个并发任务
        for crawler in crawlers.values():
            task = asyncio.create_task(
                run_crawler_task(
                    crawler=crawler,
                    keywords=keywords,
                    metrics=metrics
                )
            )
            tasks.append(task)
            
        # 记录资源使用情况
        metrics.record_resource_usage()
        
        # 等待当前批次完成
        await asyncio.gather(*tasks)
        
        # 短暂休息
        await asyncio.sleep(1)
    
    # 获取测试结果
    summary = metrics.get_summary()
    
    # 验证结果
    assert summary["duration"] >= duration
    assert summary["success_rate"] > 0.9
    assert summary["avg_cpu_usage"] < 80
    assert summary["avg_memory_usage"] < 1024
    
@pytest.mark.asyncio
async def test_error_handling(crawlers):
    """测试错误处理"""
    metrics = StressTestMetrics()
    
    # 使用无效关键词触发错误
    invalid_keywords = ["" * 1000]  # 过长的关键词
    tasks = []
    
    # 创建50个错误任务
    for _ in range(50):
        for crawler in crawlers.values():
            task = asyncio.create_task(
                run_crawler_task(
                    crawler=crawler,
                    keywords=invalid_keywords,
                    metrics=metrics
                )
            )
            tasks.append(task)
    
    # 等待所有任务完成
    await asyncio.gather(*tasks)
    
    # 验证错误处理
    assert metrics.error_count > 0
    assert metrics.request_count == len(tasks)
    
@pytest.mark.asyncio
async def test_resource_limits(crawlers):
    """测试资源限制"""
    metrics = StressTestMetrics()
    keywords = ["Python", "AI"]
    tasks = []
    
    # 设置资源限制
    process = psutil.Process()
    cpu_limit = 80
    memory_limit = 1024  # MB
    
    # 创建任务直到达到资源限制
    while True:
        # 检查CPU使用率
        if psutil.cpu_percent() > cpu_limit:
            break
            
        # 检查内存使用
        if process.memory_info().rss / 1024 / 1024 > memory_limit:
            break
            
        # 添加新任务
        for crawler in crawlers.values():
            task = asyncio.create_task(
                run_crawler_task(
                    crawler=crawler,
                    keywords=keywords,
                    metrics=metrics
                )
            )
            tasks.append(task)
            
        # 记录资源使用情况
        metrics.record_resource_usage()
        
        # 等待一小段时间
        await asyncio.sleep(0.1)
    
    # 等待所有任务完成
    await asyncio.gather(*tasks)
    
    # 验证资源使用
    summary = metrics.get_summary()
    assert summary["max_cpu_usage"] <= cpu_limit * 1.1  # 允许10%的误差
    assert summary["max_memory_usage"] <= memory_limit * 1.1 