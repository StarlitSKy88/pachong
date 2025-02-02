"""爬虫系统长期稳定性测试"""

import pytest
import asyncio
import psutil
import time
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Set
from src.crawlers.bilibili_crawler import BiliBiliCrawler
from src.crawlers.xiaohongshu_crawler import XiaoHongShuCrawler
from src.database import content_dao, platform_dao
from src.models.content import Content

class StabilityTestMetrics:
    """稳定性测试指标收集器"""
    
    def __init__(self):
        """初始化指标收集器"""
        self.start_time = datetime.now()
        self.request_count = 0
        self.error_count = 0
        self.success_count = 0
        self.response_times = []
        self.cpu_usages = []
        self.memory_usages = []
        self.error_types: Dict[str, int] = {}
        self.recovery_count = 0
        self.unique_contents: Set[str] = set()
        
        # 配置日志
        self.logger = logging.getLogger("stability_test")
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler("stability_test.log")
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(levelname)s - %(message)s"
            )
        )
        self.logger.addHandler(handler)
        
    def record_request(
        self,
        success: bool,
        response_time: float,
        error_type: str = None
    ):
        """记录请求结果
        
        Args:
            success: 是否成功
            response_time: 响应时间（秒）
            error_type: 错误类型
        """
        self.request_count += 1
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
            if error_type:
                self.error_types[error_type] = \
                    self.error_types.get(error_type, 0) + 1
                
        self.response_times.append(response_time)
        
        # 记录日志
        self.logger.info(
            f"Request completed: success={success}, "
            f"time={response_time:.2f}s, "
            f"error_type={error_type}"
        )
        
    def record_content(self, content_id: str):
        """记录内容ID
        
        Args:
            content_id: 内容ID
        """
        self.unique_contents.add(content_id)
        
    def record_recovery(self):
        """记录恢复事件"""
        self.recovery_count += 1
        self.logger.info("System recovered from error")
        
    def record_resource_usage(self):
        """记录资源使用情况"""
        cpu = psutil.cpu_percent()
        memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        self.cpu_usages.append(cpu)
        self.memory_usages.append(memory)
        
        # 记录日志
        self.logger.info(
            f"Resource usage: CPU={cpu}%, Memory={memory:.2f}MB"
        )
        
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
            "max_memory_usage": max(self.memory_usages) if self.memory_usages else 0,
            "error_types": self.error_types,
            "recovery_count": self.recovery_count,
            "unique_content_count": len(self.unique_contents)
        }

@pytest.fixture
async def crawlers():
    """创建爬虫实例"""
    bilibili = BiliBiliCrawler(
        concurrent_limit=5,
        retry_limit=5,
        timeout=15
    )
    xiaohongshu = XiaoHongShuCrawler(
        concurrent_limit=5,
        retry_limit=5,
        timeout=15
    )
    
    async with bilibili, xiaohongshu:
        yield {
            "bilibili": bilibili,
            "xiaohongshu": xiaohongshu
        }

async def run_crawler_task(
    crawler,
    keywords: List[str],
    metrics: StabilityTestMetrics
):
    """运行爬虫任务
    
    Args:
        crawler: 爬虫实例
        keywords: 关键词列表
        metrics: 指标收集器
    """
    start_time = time.time()
    error_type = None
    try:
        results = await crawler.crawl(
            keywords=keywords,
            time_range="24h",
            limit=5
        )
        success = len(results) > 0
        if success:
            for item in results:
                metrics.record_content(item["content_id"])
    except Exception as e:
        success = False
        error_type = e.__class__.__name__
        
        # 记录错误日志
        metrics.logger.error(
            f"Error in crawler task: {str(e)}",
            exc_info=True
        )
    finally:
        duration = time.time() - start_time
        metrics.record_request(success, duration, error_type)

@pytest.mark.asyncio
async def test_long_term_stability(crawlers):
    """测试长期稳定性"""
    metrics = StabilityTestMetrics()
    keywords_pool = [
        "Python", "AI", "数据", "编程", "开发",
        "机器学习", "深度学习", "人工智能", "大数据", "云计算"
    ]
    duration = 3600  # 运行1小时
    
    start_time = time.time()
    while time.time() - start_time < duration:
        tasks = []
        
        # 随机选择关键词
        keywords = random.sample(keywords_pool, 3)
        
        # 创建5个并发任务
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
        
        try:
            # 等待当前批次完成
            await asyncio.gather(*tasks)
        except Exception as e:
            # 记录错误并尝试恢复
            metrics.logger.error(
                f"Batch error: {str(e)}",
                exc_info=True
            )
            await asyncio.sleep(5)  # 等待系统恢复
            metrics.record_recovery()
            
        # 随机休息1-5秒
        await asyncio.sleep(random.uniform(1, 5))
    
    # 获取测试结果
    summary = metrics.get_summary()
    
    # 验证结果
    assert summary["duration"] >= duration
    assert summary["success_rate"] > 0.8  # 成功率大于80%
    assert summary["avg_response_time"] < 10  # 平均响应时间小于10秒
    assert summary["avg_cpu_usage"] < 80  # 平均CPU使用率小于80%
    assert summary["avg_memory_usage"] < 1024  # 平均内存使用小于1GB
    assert summary["unique_content_count"] > 0  # 有获取到唯一内容
    
    # 输出详细报告
    metrics.logger.info("Stability Test Summary:")
    metrics.logger.info(f"Duration: {summary['duration']:.2f}s")
    metrics.logger.info(f"Total Requests: {summary['total_requests']}")
    metrics.logger.info(f"Success Rate: {summary['success_rate']:.2%}")
    metrics.logger.info(f"Average Response Time: {summary['avg_response_time']:.2f}s")
    metrics.logger.info(f"Error Types: {summary['error_types']}")
    metrics.logger.info(f"Recovery Count: {summary['recovery_count']}")
    metrics.logger.info(f"Unique Content Count: {summary['unique_content_count']}")
    
@pytest.mark.asyncio
async def test_system_recovery(crawlers):
    """测试系统恢复能力"""
    metrics = StabilityTestMetrics()
    keywords = ["Python", "AI"]
    
    for _ in range(10):  # 执行10轮测试
        tasks = []
        
        # 创建正常任务
        for crawler in crawlers.values():
            task = asyncio.create_task(
                run_crawler_task(
                    crawler=crawler,
                    keywords=keywords,
                    metrics=metrics
                )
            )
            tasks.append(task)
            
        # 创建错误任务
        for crawler in crawlers.values():
            task = asyncio.create_task(
                run_crawler_task(
                    crawler=crawler,
                    keywords=["" * 1000],  # 触发错误
                    metrics=metrics
                )
            )
            tasks.append(task)
            
        # 等待所有任务完成
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # 短暂休息让系统恢复
        await asyncio.sleep(5)
        metrics.record_recovery()
        
    # 验证结果
    summary = metrics.get_summary()
    assert summary["recovery_count"] == 10  # 成功恢复10次
    assert len(summary["error_types"]) > 0  # 记录了错误类型
    
@pytest.mark.asyncio
async def test_data_consistency(crawlers):
    """测试数据一致性"""
    metrics = StabilityTestMetrics()
    keywords = ["Python"]
    
    # 清理测试数据
    await content_dao.delete_many({
        "create_time": {
            "$gte": datetime.now() - timedelta(hours=1)
        }
    })
    
    # 执行多轮爬取
    for _ in range(5):
        tasks = []
        for crawler in crawlers.values():
            task = asyncio.create_task(
                run_crawler_task(
                    crawler=crawler,
                    keywords=keywords,
                    metrics=metrics
                )
            )
            tasks.append(task)
            
        await asyncio.gather(*tasks)
        
        # 验证数据一致性
        for content_id in metrics.unique_contents:
            count = await content_dao.count({
                "content_id": content_id
            })
            assert count == 1  # 每个内容只应该存在一份
            
        # 随机休息
        await asyncio.sleep(random.uniform(1, 3))
    
    # 验证结果
    summary = metrics.get_summary()
    assert summary["unique_content_count"] > 0
    assert summary["success_rate"] > 0.8
</rewritten_file> 