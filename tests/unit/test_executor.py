"""任务执行器测试模块"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.crawlers.executor import TaskExecutor
from src.crawlers.scheduler import TaskScheduler, Task, TaskPriority, TaskStatus
from src.crawlers.crawler_factory import CrawlerFactory
from src.crawlers.base import BaseCrawler

class MockCrawler(BaseCrawler):
    """模拟爬虫类"""
    async def crawl(self, url: str):
        return {"url": url, "content": "test content"}

@pytest.fixture
def scheduler():
    """创建测试用调度器"""
    return TaskScheduler(
        max_concurrent_tasks=2,
        max_tasks_per_host=1,
        retry_delay=0
    )

@pytest.fixture
def crawler_factory():
    """创建测试用爬虫工厂"""
    factory = Mock(spec=CrawlerFactory)
    crawler = MockCrawler()
    factory.get_crawler.return_value = crawler
    return factory

@pytest.fixture
def executor(scheduler, crawler_factory):
    """创建测试用执行器"""
    return TaskExecutor(
        scheduler=scheduler,
        crawler_factory=crawler_factory,
        max_workers=2
    )

@pytest.mark.asyncio
async def test_start_stop(executor):
    """测试启动和停止"""
    # 启动执行器
    await executor.start()
    assert executor.running is True
    assert len(executor.workers) == 2
    
    # 重复启动
    await executor.start()
    assert len(executor.workers) == 2
    
    # 停止执行器
    await executor.stop()
    assert executor.running is False
    assert len(executor.workers) == 0

@pytest.mark.asyncio
async def test_execute_task(executor, scheduler):
    """测试任务执行"""
    # 创建测试任务
    task = Task(
        id="test1",
        platform="test",
        url="http://example.com/1",
        priority=TaskPriority.HIGH,
        status=TaskStatus.PENDING
    )
    
    # 添加任务并启动执行器
    await scheduler.add_task(task)
    await executor.start()
    
    # 等待任务执行完成
    await asyncio.sleep(0.1)
    
    # 验证任务状态
    assert scheduler.task_history[task.id].status == TaskStatus.COMPLETED
    assert executor.stats['tasks_completed'] == 1
    assert executor.stats['tasks_failed'] == 0

@pytest.mark.asyncio
async def test_execute_task_failure(executor, scheduler, crawler_factory):
    """测试任务执行失败"""
    # 模拟爬虫执行失败
    crawler = AsyncMock()
    crawler.crawl.side_effect = Exception("Test error")
    crawler_factory.get_crawler.return_value = crawler
    
    # 创建测试任务
    task = Task(
        id="test1",
        platform="test",
        url="http://example.com/1",
        priority=TaskPriority.HIGH,
        status=TaskStatus.PENDING,
        max_retries=0
    )
    
    # 添加任务并启动执行器
    await scheduler.add_task(task)
    await executor.start()
    
    # 等待任务执行完成
    await asyncio.sleep(0.1)
    
    # 验证任务状态
    assert scheduler.task_history[task.id].status == TaskStatus.FAILED
    assert executor.stats['tasks_completed'] == 0
    assert executor.stats['tasks_failed'] == 1

@pytest.mark.asyncio
async def test_metrics_collection(executor, scheduler):
    """测试指标收集"""
    # 创建Mock指标收集器
    metrics_collector = Mock()
    metrics_collector.increment_counter = Mock()
    metrics_collector.observe = Mock()
    executor.metrics_collector = metrics_collector
    
    # 创建测试任务
    task = Task(
        id="test1",
        platform="test",
        url="http://example.com/1",
        priority=TaskPriority.HIGH,
        status=TaskStatus.PENDING
    )
    
    # 添加任务并启动执行器
    await scheduler.add_task(task)
    await executor.start()
    
    # 等待任务执行完成
    await asyncio.sleep(0.1)
    
    # 验证指标收集
    assert metrics_collector.increment_counter.call_count >= 2
    assert metrics_collector.observe.call_count >= 1

@pytest.mark.asyncio
async def test_alert_engine(executor, scheduler, crawler_factory):
    """测试告警引擎"""
    # 创建Mock告警引擎
    alert_engine = AsyncMock()
    executor.alert_engine = alert_engine
    
    # 模拟爬虫执行失败
    crawler = AsyncMock()
    crawler.crawl.side_effect = Exception("Test error")
    crawler_factory.get_crawler.return_value = crawler
    
    # 创建测试任务
    task = Task(
        id="test1",
        platform="test",
        url="http://example.com/1",
        priority=TaskPriority.HIGH,
        status=TaskStatus.PENDING,
        max_retries=0
    )
    
    # 添加任务并启动执行器
    await scheduler.add_task(task)
    await executor.start()
    
    # 等待任务执行完成
    await asyncio.sleep(0.1)
    
    # 验证告警
    alert_engine.send_alert.assert_called_once()

@pytest.mark.asyncio
async def test_health_check(executor):
    """测试健康检查"""
    # 未启动状态
    healthy, message = await executor.health_check()
    assert healthy is False
    assert "not running" in message
    
    # 启动后正常状态
    await executor.start()
    healthy, message = await executor.health_check()
    assert healthy is True
    assert "healthy" in message
    
    # 模拟高失败率
    executor.stats['tasks_completed'] = 7
    executor.stats['tasks_failed'] = 3
    healthy, message = await executor.health_check()
    assert healthy is False
    assert "failure rate" in message

@pytest.mark.asyncio
async def test_concurrent_execution(executor, scheduler):
    """测试并发执行"""
    # 创建多个测试任务
    tasks = [
        Task(
            id=f"test{i}",
            platform="test",
            url=f"http://example{i}.com/1",
            priority=TaskPriority.HIGH,
            status=TaskStatus.PENDING
        )
        for i in range(5)
    ]
    
    # 添加任务
    for task in tasks:
        await scheduler.add_task(task)
    
    # 启动执行器
    await executor.start()
    
    # 等待任务执行
    await asyncio.sleep(0.2)
    
    # 验证执行结果
    assert executor.stats['tasks_completed'] == 5
    for task in tasks:
        assert scheduler.task_history[task.id].status == TaskStatus.COMPLETED

@pytest.mark.asyncio
async def test_get_stats(executor):
    """测试统计信息获取"""
    # 启动执行器
    await executor.start()
    
    # 获取统计信息
    stats = executor.get_stats()
    assert 'tasks_completed' in stats
    assert 'tasks_failed' in stats
    assert 'total_time' in stats
    assert 'avg_time' in stats
    assert 'workers' in stats
    assert 'is_running' in stats
    
    # 验证统计值
    assert stats['workers'] == 2
    assert stats['is_running'] is True 