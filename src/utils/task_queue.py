import asyncio
from typing import Dict, Any, List, Optional, Callable, Awaitable
from datetime import datetime
from .logger import get_logger
from .exceptions import CrawlerException

logger = get_logger(__name__)

class Task:
    """任务类"""
    
    def __init__(
        self,
        task_id: str,
        func: Callable[..., Awaitable[Any]],
        args: tuple = (),
        kwargs: Dict[str, Any] = None,
        priority: int = 0,
        retry_times: int = 3,
        retry_delay: float = 1.0
    ):
        """初始化任务
        
        Args:
            task_id: 任务ID
            func: 异步函数
            args: 位置参数
            kwargs: 关键字参数
            priority: 优先级（数字越大优先级越高）
            retry_times: 重试次数
            retry_delay: 重试延迟（秒）
        """
        self.task_id = task_id
        self.func = func
        self.args = args
        self.kwargs = kwargs or {}
        self.priority = priority
        self.retry_times = retry_times
        self.retry_delay = retry_delay
        self.retried = 0
        self.status = "pending"  # pending, running, completed, failed
        self.result = None
        self.error = None
        self.create_time = datetime.now()
        self.start_time = None
        self.end_time = None
        
    def __lt__(self, other):
        """优先级比较"""
        return self.priority > other.priority  # 优先级高的排在前面
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            Dict[str, Any]: 任务信息字典
        """
        return {
            "task_id": self.task_id,
            "status": self.status,
            "priority": self.priority,
            "retried": self.retried,
            "create_time": self.create_time.isoformat(),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "error": str(self.error) if self.error else None
        }

class TaskQueue:
    """任务队列管理器"""
    
    def __init__(
        self,
        max_workers: int = 3,
        max_queue_size: int = 1000
    ):
        """初始化任务队列
        
        Args:
            max_workers: 最大工作线程数
            max_queue_size: 最大队列大小
        """
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        self.queue = asyncio.PriorityQueue(maxsize=max_queue_size)
        self.tasks: Dict[str, Task] = {}
        self.workers: List[asyncio.Task] = []
        self.running = False
        self.completed_tasks: List[Task] = []
        self.failed_tasks: List[Task] = []
        
    async def start(self):
        """启动任务队列"""
        if self.running:
            return
            
        self.running = True
        
        # 启动工作线程
        for _ in range(self.max_workers):
            worker = asyncio.create_task(self._worker())
            self.workers.append(worker)
            
        logger.info(f"任务队列已启动，工作线程数：{self.max_workers}")
        
    async def stop(self):
        """停止任务队列"""
        if not self.running:
            return
            
        self.running = False
        
        # 等待所有任务完成
        if self.tasks:
            logger.info(f"等待 {len(self.tasks)} 个任务完成...")
            await self.queue.join()
            
        # 取消所有工作线程
        for worker in self.workers:
            worker.cancel()
            
        # 等待工作线程结束
        await asyncio.gather(*self.workers, return_exceptions=True)
        
        logger.info("任务队列已停止")
        
    async def add_task(
        self,
        task: Task
    ) -> None:
        """添加任务
        
        Args:
            task: 任务对象
        """
        if not self.running:
            raise CrawlerException("任务队列未启动")
            
        if len(self.tasks) >= self.max_queue_size:
            raise CrawlerException("任务队列已满")
            
        self.tasks[task.task_id] = task
        await self.queue.put((task.priority, task))
        
        logger.debug(f"添加任务：{task.task_id}，优先级：{task.priority}")
        
    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[Task]: 任务对象
        """
        return self.tasks.get(task_id)
        
    def get_tasks(
        self,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Task]:
        """获取任务列表
        
        Args:
            status: 任务状态
            limit: 返回数量限制
            
        Returns:
            List[Task]: 任务列表
        """
        tasks = list(self.tasks.values())
        
        if status:
            tasks = [t for t in tasks if t.status == status]
            
        return sorted(tasks, key=lambda x: x.create_time, reverse=True)[:limit]
        
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        stats = {
            "total": len(self.tasks),
            "pending": len([t for t in self.tasks.values() if t.status == "pending"]),
            "running": len([t for t in self.tasks.values() if t.status == "running"]),
            "completed": len(self.completed_tasks),
            "failed": len(self.failed_tasks),
            "workers": len(self.workers),
            "queue_size": self.queue.qsize()
        }
        
        # 计算平均执行时间
        completed_times = []
        for task in self.completed_tasks:
            if task.start_time and task.end_time:
                duration = (task.end_time - task.start_time).total_seconds()
                completed_times.append(duration)
                
        if completed_times:
            stats["avg_time"] = sum(completed_times) / len(completed_times)
        else:
            stats["avg_time"] = 0
            
        return stats
        
    async def _worker(self):
        """工作线程"""
        while self.running:
            try:
                # 获取任务
                _, task = await self.queue.get()
                
                # 更新任务状态
                task.status = "running"
                task.start_time = datetime.now()
                
                try:
                    # 执行任务
                    task.result = await task.func(*task.args, **task.kwargs)
                    task.status = "completed"
                    self.completed_tasks.append(task)
                    
                except Exception as e:
                    # 处理任务异常
                    task.error = e
                    
                    # 是否需要重试
                    if task.retried < task.retry_times:
                        task.retried += 1
                        task.status = "pending"
                        # 重新加入队列
                        await asyncio.sleep(task.retry_delay)
                        await self.queue.put((task.priority, task))
                        logger.warning(
                            f"任务 {task.task_id} 执行失败，"
                            f"重试 ({task.retried}/{task.retry_times})"
                        )
                    else:
                        task.status = "failed"
                        self.failed_tasks.append(task)
                        logger.error(f"任务 {task.task_id} 执行失败：{str(e)}")
                        
                finally:
                    task.end_time = datetime.now()
                    self.queue.task_done()
                    
            except asyncio.CancelledError:
                break
                
            except Exception as e:
                logger.error(f"工作线程异常：{str(e)}")
                continue 