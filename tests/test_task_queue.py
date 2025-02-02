import pytest
import asyncio
from datetime import datetime
from src.utils.task_queue import Task, TaskQueue
from src.utils.exceptions import CrawlerException

@pytest.fixture
async def task_queue():
    """创建任务队列实例"""
    queue = TaskQueue(max_workers=2)
    await queue.start()
    yield queue
    await queue.stop()

async def dummy_task(sleep_time: float = 0.1) -> str:
    """测试用任务"""
    await asyncio.sleep(sleep_time)
    return "success"

async def failing_task() -> None:
    """失败任务"""
    raise ValueError("任务失败")

def test_task_init():
    """测试任务初始化"""
    task = Task(
        task_id="test_task",
        func=dummy_task,
        args=(0.1,),
        priority=1
    )
    
    assert task.task_id == "test_task"
    assert task.priority == 1
    assert task.status == "pending"
    assert task.retried == 0
    assert isinstance(task.create_time, datetime)
    assert task.start_time is None
    assert task.end_time is None

def test_task_comparison():
    """测试任务优先级比较"""
    task1 = Task("task1", dummy_task, priority=1)
    task2 = Task("task2", dummy_task, priority=2)
    task3 = Task("task3", dummy_task, priority=0)
    
    # 优先级高的排在前面
    assert task2 < task1  # task2优先级更高
    assert task1 < task3  # task1优先级更高
    assert task2 < task3  # task2优先级更高

def test_task_to_dict():
    """测试任务转换为字典"""
    task = Task("test_task", dummy_task)
    task_dict = task.to_dict()
    
    assert task_dict["task_id"] == "test_task"
    assert task_dict["status"] == "pending"
    assert task_dict["priority"] == 0
    assert task_dict["retried"] == 0
    assert task_dict["start_time"] is None
    assert task_dict["end_time"] is None
    assert task_dict["error"] is None

@pytest.mark.asyncio
async def test_task_queue_start_stop(task_queue):
    """测试任务队列启动和停止"""
    assert task_queue.running
    assert len(task_queue.workers) == 2
    
    await task_queue.stop()
    assert not task_queue.running
    assert all(w.done() for w in task_queue.workers)

@pytest.mark.asyncio
async def test_add_task(task_queue):
    """测试添加任务"""
    task = Task("test_task", dummy_task)
    await task_queue.add_task(task)
    
    assert task.task_id in task_queue.tasks
    assert task_queue.queue.qsize() == 1

@pytest.mark.asyncio
async def test_add_task_queue_not_running():
    """测试向未启动的队列添加任务"""
    queue = TaskQueue()
    task = Task("test_task", dummy_task)
    
    with pytest.raises(CrawlerException, match="任务队列未启动"):
        await queue.add_task(task)

@pytest.mark.asyncio
async def test_add_task_queue_full():
    """测试向已满的队列添加任务"""
    queue = TaskQueue(max_queue_size=1)
    await queue.start()
    
    # 添加第一个任务
    task1 = Task("task1", dummy_task)
    await queue.add_task(task1)
    
    # 添加第二个任务应该失败
    task2 = Task("task2", dummy_task)
    with pytest.raises(CrawlerException, match="任务队列已满"):
        await queue.add_task(task2)
        
    await queue.stop()

@pytest.mark.asyncio
async def test_task_execution(task_queue):
    """测试任务执行"""
    task = Task("test_task", dummy_task, args=(0.1,))
    await task_queue.add_task(task)
    
    # 等待任务完成
    await asyncio.sleep(0.2)
    
    assert task.status == "completed"
    assert task.result == "success"
    assert task.start_time is not None
    assert task.end_time is not None
    assert len(task_queue.completed_tasks) == 1

@pytest.mark.asyncio
async def test_task_retry(task_queue):
    """测试任务重试"""
    task = Task(
        "failing_task",
        failing_task,
        retry_times=2,
        retry_delay=0.1
    )
    await task_queue.add_task(task)
    
    # 等待任务重试完成
    await asyncio.sleep(0.5)
    
    assert task.status == "failed"
    assert task.retried == 2
    assert isinstance(task.error, ValueError)
    assert len(task_queue.failed_tasks) == 1

@pytest.mark.asyncio
async def test_get_task(task_queue):
    """测试获取任务"""
    task = Task("test_task", dummy_task)
    await task_queue.add_task(task)
    
    assert task_queue.get_task("test_task") == task
    assert task_queue.get_task("non_existent") is None

@pytest.mark.asyncio
async def test_get_tasks(task_queue):
    """测试获取任务列表"""
    # 添加多个任务
    task1 = Task("task1", dummy_task)
    task2 = Task("task2", failing_task)
    await task_queue.add_task(task1)
    await task_queue.add_task(task2)
    
    # 等待任务执行
    await asyncio.sleep(0.2)
    
    # 获取所有任务
    all_tasks = task_queue.get_tasks()
    assert len(all_tasks) == 2
    
    # 获取完成的任务
    completed_tasks = task_queue.get_tasks(status="completed")
    assert len(completed_tasks) == 1
    assert completed_tasks[0].task_id == "task1"
    
    # 获取失败的任务
    failed_tasks = task_queue.get_tasks(status="failed")
    assert len(failed_tasks) == 1
    assert failed_tasks[0].task_id == "task2"

@pytest.mark.asyncio
async def test_get_stats(task_queue):
    """测试获取统计信息"""
    # 添加多个任务
    task1 = Task("task1", dummy_task, args=(0.1,))
    task2 = Task("task2", failing_task)
    await task_queue.add_task(task1)
    await task_queue.add_task(task2)
    
    # 等待任务执行
    await asyncio.sleep(0.2)
    
    stats = task_queue.get_stats()
    
    assert stats["total"] == 2
    assert stats["completed"] == 1
    assert stats["failed"] == 1
    assert stats["workers"] == 2
    assert "avg_time" in stats 