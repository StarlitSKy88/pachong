"""任务执行器模块

该模块负责执行调度器分配的爬虫任务，包括：
1. 任务执行
2. 错误处理
3. 资源管理
4. 性能监控
"""

import asyncio
import logging
from typing import Dict, Optional, List
from datetime import datetime

from src.utils.logger import get_logger
from src.monitor.metrics import MetricsCollector
from src.monitor.alert import AlertEngine
from src.crawlers.scheduler import TaskScheduler, Task, TaskStatus
from src.crawlers.base import BaseCrawler
from src.crawlers.crawler_factory import CrawlerFactory

logger = get_logger(__name__)

class TaskExecutor:
    """任务执行器"""
    
    def __init__(
        self,
        scheduler: TaskScheduler,
        crawler_factory: CrawlerFactory,
        max_workers: int = 10,
        metrics_collector: Optional[MetricsCollector] = None,
        alert_engine: Optional[AlertEngine] = None
    ):
        self.scheduler = scheduler
        self.crawler_factory = crawler_factory
        self.max_workers = max_workers
        self.metrics_collector = metrics_collector
        self.alert_engine = alert_engine
        
        # 运行状态
        self.running = False
        self.workers: List[asyncio.Task] = []
        
        # 性能统计
        self.stats = {
            'tasks_completed': 0,
            'tasks_failed': 0,
            'total_time': 0,
            'avg_time': 0
        }
    
    async def start(self):
        """启动执行器"""
        if self.running:
            logger.warning("Executor is already running")
            return
        
        self.running = True
        logger.info("Starting task executor")
        
        # 启动工作协程
        for _ in range(self.max_workers):
            worker = asyncio.create_task(self._worker())
            self.workers.append(worker)
    
    async def stop(self):
        """停止执行器"""
        if not self.running:
            return
        
        self.running = False
        logger.info("Stopping task executor")
        
        # 等待所有工作协程完成
        if self.workers:
            await asyncio.gather(*self.workers, return_exceptions=True)
            self.workers.clear()
    
    async def _worker(self):
        """工作协程"""
        while self.running:
            try:
                # 获取下一个任务
                task = await self.scheduler.get_next_task()
                if task is None:
                    # 没有任务，等待一段时间
                    await asyncio.sleep(1)
                    continue
                
                # 执行任务
                success, error = await self._execute_task(task)
                
                # 更新任务状态
                await self.scheduler.complete_task(task.id, success, error)
                
            except Exception as e:
                logger.error(f"Worker error: {e}", exc_info=True)
                if self.alert_engine:
                    await self.alert_engine.send_alert(
                        title="Worker Error",
                        message=str(e),
                        level="error"
                    )
    
    async def _execute_task(self, task: Task) -> tuple[bool, Optional[str]]:
        """执行单个任务"""
        start_time = datetime.now()
        
        try:
            # 获取对应的爬虫实例
            crawler = self.crawler_factory.get_crawler(task.platform)
            if crawler is None:
                return False, f"No crawler found for platform: {task.platform}"
            
            # 记录开始指标
            if self.metrics_collector:
                self.metrics_collector.increment_counter(
                    'executor_task_started',
                    labels={
                        'platform': task.platform,
                        'priority': task.priority.name
                    }
                )
            
            # 执行爬取
            result = await crawler.crawl(task.url)
            
            # 更新统计
            self.stats['tasks_completed'] += 1
            execution_time = (datetime.now() - start_time).total_seconds()
            self.stats['total_time'] += execution_time
            self.stats['avg_time'] = self.stats['total_time'] / self.stats['tasks_completed']
            
            # 记录完成指标
            if self.metrics_collector:
                self.metrics_collector.increment_counter(
                    'executor_task_completed',
                    labels={
                        'platform': task.platform,
                        'priority': task.priority.name
                    }
                )
                self.metrics_collector.observe(
                    'executor_task_duration',
                    execution_time,
                    labels={
                        'platform': task.platform,
                        'priority': task.priority.name
                    }
                )
            
            return True, None
            
        except Exception as e:
            # 更新统计
            self.stats['tasks_failed'] += 1
            
            # 记录失败指标
            if self.metrics_collector:
                self.metrics_collector.increment_counter(
                    'executor_task_failed',
                    labels={
                        'platform': task.platform,
                        'priority': task.priority.name,
                        'error': type(e).__name__
                    }
                )
            
            logger.error(f"Task execution error: {e}", exc_info=True)
            return False, str(e)
    
    def get_stats(self) -> Dict:
        """获取执行统计信息"""
        return {
            **self.stats,
            'workers': len(self.workers),
            'is_running': self.running
        }
    
    async def health_check(self) -> tuple[bool, str]:
        """健康检查"""
        if not self.running:
            return False, "Executor is not running"
        
        # 检查工作协程状态
        active_workers = len([w for w in self.workers if not w.done()])
        if active_workers < self.max_workers:
            return False, f"Only {active_workers}/{self.max_workers} workers are active"
        
        # 检查失败率
        if self.stats['tasks_completed'] > 0:
            failure_rate = self.stats['tasks_failed'] / (
                self.stats['tasks_completed'] + self.stats['tasks_failed']
            )
            if failure_rate > 0.3:  # 30% 失败率阈值
                return False, f"High failure rate: {failure_rate:.2%}"
        
        return True, "Executor is healthy" 