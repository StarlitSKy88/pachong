"""任务调度器测试模块"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

from src.crawlers.scheduler import (
    TaskScheduler,
    Task,
    TaskPriority,
    TaskStatus
)

@pytest.fixture
def scheduler():
    """创建测试用调度器"""
    return TaskScheduler(
        max_concurrent_tasks=2,
        max_tasks_per_host=1,
        retry_delay=0  # 测试时不需要实际延迟
    )

@pytest.mark.asyncio
async def test_add_task(scheduler):
    """测试添加任务"""
    task = Task(
        id="test1",
        platform="test",
        url="http://example.com/1",
        priority=TaskPriority.HIGH,
        status=TaskStatus.PENDING
    )
    
    # 添加任务
    success = await scheduler.add_task(task)
    assert success is True
    
    # 验证任务在队列中
    assert len(scheduler.task_queues[TaskPriority.HIGH]) == 1
    assert task.id in scheduler.task_history
    
    # 重复添加
    success = await scheduler.add_task(task)
    assert success is False
    assert len(scheduler.task_queues[TaskPriority.HIGH]) == 1

@pytest.mark.asyncio
async def test_get_next_task(scheduler):
    """测试获取下一个任务"""
    # 添加不同优先级的任务
    tasks = [
        Task(
            id=f"test{i}",
            platform="test",
            url=f"http://example{i}.com/1",
            priority=priority,
            status=TaskStatus.PENDING
        )
        for i, priority in enumerate([
            TaskPriority.LOW,
            TaskPriority.MEDIUM,
            TaskPriority.HIGH
        ])
    ]
    
    for task in tasks:
        await scheduler.add_task(task)
    
    # 验证按优先级返回任务
    next_task = await scheduler.get_next_task()
    assert next_task.id == "test2"  # HIGH priority
    assert next_task.status == TaskStatus.RUNNING
    
    next_task = await scheduler.get_next_task()
    assert next_task.id == "test1"  # MEDIUM priority
    
    # 已达到并发限制
    next_task = await scheduler.get_next_task()
    assert next_task is None

@pytest.mark.asyncio
async def test_complete_task(scheduler):
    """测试完成任务"""
    task = Task(
        id="test1",
        platform="test",
        url="http://example.com/1",
        priority=TaskPriority.HIGH,
        status=TaskStatus.PENDING
    )
    
    await scheduler.add_task(task)
    next_task = await scheduler.get_next_task()
    
    # 成功完成
    await scheduler.complete_task(task.id, True)
    assert scheduler.task_history[task.id].status == TaskStatus.COMPLETED
    assert len(scheduler.running_tasks) == 0
    
    # 失败重试
    task2 = Task(
        id="test2",
        platform="test",
        url="http://example.com/2",
        priority=TaskPriority.HIGH,
        status=TaskStatus.PENDING
    )
    
    await scheduler.add_task(task2)
    next_task = await scheduler.get_next_task()
    
    await scheduler.complete_task(task2.id, False, "test error")
    assert scheduler.task_history[task2.id].status == TaskStatus.RETRY
    assert scheduler.task_history[task2.id].retry_count == 1
    
    # 失败超过重试次数
    for _ in range(3):
        next_task = await scheduler.get_next_task()
        await scheduler.complete_task(task2.id, False, "test error")
    
    assert scheduler.task_history[task2.id].status == TaskStatus.FAILED

@pytest.mark.asyncio
async def test_host_limits(scheduler):
    """测试主机限制"""
    # 添加同一主机的多个任务
    tasks = [
        Task(
            id=f"test{i}",
            platform="test",
            url="http://example.com/1",
            priority=TaskPriority.HIGH,
            status=TaskStatus.PENDING
        )
        for i in range(3)
    ]
    
    for task in tasks:
        await scheduler.add_task(task)
    
    # 只能获取一个任务（主机限制）
    next_task = await scheduler.get_next_task()
    assert next_task is not None
    
    next_task = await scheduler.get_next_task()
    assert next_task is None

@pytest.mark.asyncio
async def test_clear_completed_tasks(scheduler):
    """测试清理已完成任务"""
    # 添加并完成任务
    task = Task(
        id="test1",
        platform="test",
        url="http://example.com/1",
        priority=TaskPriority.HIGH,
        status=TaskStatus.PENDING
    )
    
    await scheduler.add_task(task)
    next_task = await scheduler.get_next_task()
    await scheduler.complete_task(task.id, True)
    
    # 清理之前
    assert task.id in scheduler.task_history
    
    # 清理
    await scheduler.clear_completed_tasks()
    assert task.id not in scheduler.task_history

@pytest.mark.asyncio
async def test_health_check(scheduler):
    """测试健康检查"""
    # 正常状态
    healthy, message = await scheduler.health_check()
    assert healthy is True
    
    # 添加卡住的任务
    task = Task(
        id="test1",
        platform="test",
        url="http://example.com/1",
        priority=TaskPriority.HIGH,
        status=TaskStatus.PENDING
    )
    
    await scheduler.add_task(task)
    next_task = await scheduler.get_next_task()
    
    # 修改开始时间使任务显示为卡住
    scheduler.task_history[task.id].started_at = datetime.now() - timedelta(hours=2)
    
    healthy, message = await scheduler.health_check()
    assert healthy is False
    assert "stuck tasks" in message

@pytest.mark.asyncio
async def test_metrics_collection(scheduler):
    """测试指标收集"""
    # 创建Mock指标收集器
    metrics_collector = Mock()
    metrics_collector.increment_counter = Mock()
    scheduler.metrics_collector = metrics_collector
    
    # 添加任务
    task = Task(
        id="test1",
        platform="test",
        url="http://example.com/1",
        priority=TaskPriority.HIGH,
        status=TaskStatus.PENDING
    )
    
    await scheduler.add_task(task)
    
    # 验证调用
    metrics_collector.increment_counter.assert_called_with(
        'scheduler_tasks_added',
        labels={'priority': 'HIGH'}
    )

@pytest.mark.asyncio
async def test_alert_engine(scheduler):
    """测试告警引擎"""
    # 创建Mock告警引擎
    alert_engine = AsyncMock()
    scheduler.alert_engine = alert_engine
    
    # 添加任务并使其失败
    task = Task(
        id="test1",
        platform="test",
        url="http://example.com/1",
        priority=TaskPriority.HIGH,
        status=TaskStatus.PENDING,
        max_retries=0
    )
    
    await scheduler.add_task(task)
    next_task = await scheduler.get_next_task()
    await scheduler.complete_task(task.id, False, "test error")
    
    # 验证告警
    alert_engine.send_alert.assert_called_once() 