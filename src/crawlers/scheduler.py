"""任务调度器模块

该模块负责爬虫任务的调度管理，包括：
1. 任务优先级管理
2. 任务队列管理
3. 并发控制
4. 失败重试
5. 资源分配
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import time
import random

from src.utils.logger import get_logger
from src.monitor.metrics import MetricsCollector
from src.monitor.alert import AlertEngine

logger = get_logger(__name__)

class TaskPriority(Enum):
    """任务优先级定义"""
    HIGH = 0
    MEDIUM = 1
    LOW = 2

class TaskStatus(Enum):
    """任务状态定义"""
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    RETRY = 'retry'

@dataclass
class Task:
    """任务数据类"""
    id: str
    platform: str
    url: str
    priority: TaskPriority
    status: TaskStatus
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = None
    started_at: datetime = None
    completed_at: datetime = None
    error: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class TaskScheduler:
    """任务调度器"""
    
    def __init__(
        self,
        max_concurrent_tasks: int = 10,
        max_tasks_per_host: int = 3,
        retry_delay: int = 60,
        metrics_collector: Optional[MetricsCollector] = None,
        alert_engine: Optional[AlertEngine] = None
    ):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.max_tasks_per_host = max_tasks_per_host
        self.retry_delay = retry_delay
        
        # 任务队列（按优先级）
        self.task_queues: Dict[TaskPriority, List[Task]] = {
            TaskPriority.HIGH: [],
            TaskPriority.MEDIUM: [],
            TaskPriority.LOW: []
        }
        
        # 运行中的任务
        self.running_tasks: Set[str] = set()
        
        # 主机任务计数
        self.host_task_counts: Dict[str, int] = {}
        
        # 任务历史
        self.task_history: Dict[str, Task] = {}
        
        # 监控和告警
        self.metrics_collector = metrics_collector
        self.alert_engine = alert_engine
        
        # 调度锁
        self._schedule_lock = asyncio.Lock()
    
    async def add_task(self, task: Task) -> bool:
        """添加新任务"""
        async with self._schedule_lock:
            # 检查任务是否已存在
            if task.id in self.task_history:
                logger.warning(f"Task {task.id} already exists")
                return False
            
            # 添加到对应优先级队列
            self.task_queues[task.priority].append(task)
            self.task_history[task.id] = task
            
            # 记录指标
            if self.metrics_collector:
                self.metrics_collector.increment_counter(
                    'scheduler_tasks_added',
                    labels={'priority': task.priority.name}
                )
            
            logger.info(f"Added task {task.id} with priority {task.priority}")
            return True
    
    async def get_next_task(self) -> Optional[Task]:
        """获取下一个要执行的任务"""
        async with self._schedule_lock:
            # 检查是否达到并发限制
            if len(self.running_tasks) >= self.max_concurrent_tasks:
                return None
            
            # 按优先级遍历队列
            for priority in TaskPriority:
                queue = self.task_queues[priority]
                if not queue:
                    continue
                
                # 找到符合主机限制的任务
                for i, task in enumerate(queue):
                    host = task.url.split('/')[2]
                    if self.host_task_counts.get(host, 0) < self.max_tasks_per_host:
                        # 更新状态
                        task.status = TaskStatus.RUNNING
                        task.started_at = datetime.now()
                        
                        # 更新计数
                        self.running_tasks.add(task.id)
                        self.host_task_counts[host] = self.host_task_counts.get(host, 0) + 1
                        
                        # 从队列中移除
                        queue.pop(i)
                        
                        # 记录指标
                        if self.metrics_collector:
                            self.metrics_collector.increment_counter(
                                'scheduler_tasks_started',
                                labels={'priority': task.priority.name}
                            )
                        
                        logger.info(f"Starting task {task.id}")
                        return task
            
            return None
    
    async def complete_task(self, task_id: str, success: bool, error: str = None):
        """完成任务处理"""
        async with self._schedule_lock:
            if task_id not in self.task_history:
                logger.error(f"Task {task_id} not found")
                return
            
            task = self.task_history[task_id]
            host = task.url.split('/')[2]
            
            # 更新计数
            self.running_tasks.remove(task_id)
            self.host_task_counts[host] = max(0, self.host_task_counts.get(host, 1) - 1)
            
            # 更新任务状态
            task.completed_at = datetime.now()
            if success:
                task.status = TaskStatus.COMPLETED
                logger.info(f"Task {task_id} completed successfully")
            else:
                task.error = error
                if task.retry_count < task.max_retries:
                    task.status = TaskStatus.RETRY
                    task.retry_count += 1
                    # 延迟重试
                    await asyncio.sleep(self.retry_delay)
                    # 重新加入队列
                    self.task_queues[task.priority].append(task)
                    logger.warning(f"Task {task_id} failed, scheduling retry {task.retry_count}/{task.max_retries}")
                else:
                    task.status = TaskStatus.FAILED
                    logger.error(f"Task {task_id} failed permanently: {error}")
                    # 触发告警
                    if self.alert_engine:
                        await self.alert_engine.send_alert(
                            title=f"Task {task_id} failed",
                            message=f"Task failed after {task.max_retries} retries: {error}",
                            level="error"
                        )
            
            # 记录指标
            if self.metrics_collector:
                self.metrics_collector.increment_counter(
                    'scheduler_tasks_completed',
                    labels={
                        'priority': task.priority.name,
                        'status': task.status.value
                    }
                )
    
    async def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """获取任务状态"""
        if task_id in self.task_history:
            return self.task_history[task_id].status
        return None
    
    def get_queue_stats(self) -> Dict[str, int]:
        """获取队列统计信息"""
        return {
            'total_pending': sum(len(q) for q in self.task_queues.values()),
            'running': len(self.running_tasks),
            'high_priority': len(self.task_queues[TaskPriority.HIGH]),
            'medium_priority': len(self.task_queues[TaskPriority.MEDIUM]),
            'low_priority': len(self.task_queues[TaskPriority.LOW])
        }
    
    async def clear_completed_tasks(self, before: datetime = None):
        """清理已完成的任务历史"""
        async with self._schedule_lock:
            to_remove = []
            for task_id, task in self.task_history.items():
                if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                    if before is None or task.completed_at < before:
                        to_remove.append(task_id)
            
            for task_id in to_remove:
                del self.task_history[task_id]
            
            logger.info(f"Cleared {len(to_remove)} completed tasks")
    
    async def health_check(self) -> Tuple[bool, str]:
        """健康检查"""
        # 检查队列状态
        stats = self.get_queue_stats()
        
        # 检查是否有任务卡住
        stuck_tasks = []
        now = datetime.now()
        for task_id in self.running_tasks:
            task = self.task_history[task_id]
            if (now - task.started_at).total_seconds() > 3600:  # 1小时
                stuck_tasks.append(task_id)
        
        if stuck_tasks:
            return False, f"Found {len(stuck_tasks)} stuck tasks: {stuck_tasks}"
        
        # 检查队列是否正常
        if stats['running'] > self.max_concurrent_tasks:
            return False, f"Too many running tasks: {stats['running']}"
        
        return True, "Scheduler healthy" 