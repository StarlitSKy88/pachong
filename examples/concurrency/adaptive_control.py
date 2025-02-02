"""自适应并发控制示例"""

from collections import deque
from typing import Callable, Any
import asyncio
import time
from functools import wraps

class AdaptiveConcurrency:
    """自适应并发控制器"""
    
    def __init__(
        self,
        initial_workers: int = 10,
        min_workers: int = 1,
        max_workers: int = 50,
        window_size: int = 100,
        error_threshold: float = 0.05,
        increase_step: int = 2,
        decrease_step: int = 5
    ):
        """初始化并发控制器
        
        Args:
            initial_workers: 初始工作线程数
            min_workers: 最小工作线程数
            max_workers: 最大工作线程数
            window_size: 错误率计算窗口大小
            error_threshold: 错误率阈值
            increase_step: 增加步长
            decrease_step: 减少步长
        """
        self.max_workers = initial_workers
        self.min_workers = min_workers
        self.max_limit = max_workers
        self.error_window = deque(maxlen=window_size)
        self.error_threshold = error_threshold
        self.increase_step = increase_step
        self.decrease_step = decrease_step
        self.semaphore = asyncio.Semaphore(initial_workers)
        
    def adjust_concurrency(self):
        """调整并发数"""
        if not self.error_window:
            return
            
        error_rate = sum(self.error_window) / len(self.error_window)
        
        if error_rate < self.error_threshold:
            self.max_workers = min(
                self.max_workers + self.increase_step,
                self.max_limit
            )
        else:
            self.max_workers = max(
                self.max_workers - self.decrease_step,
                self.min_workers
            )
            
        # 更新信号量
        self.semaphore = asyncio.Semaphore(self.max_workers)
        
    def record_result(self, success: bool):
        """记录执行结果
        
        Args:
            success: 是否成功
        """
        self.error_window.append(0 if success else 1)
        self.adjust_concurrency()
        
    def __call__(self, func: Callable) -> Callable:
        """装饰器实现
        
        Args:
            func: 被装饰的函数
            
        Returns:
            Callable: 装饰后的函数
        """
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            async with self.semaphore:
                try:
                    result = await func(*args, **kwargs)
                    self.record_result(True)
                    return result
                except Exception as e:
                    self.record_result(False)
                    raise e
                    
        return wrapper

# 使用示例
if __name__ == "__main__":
    # 创建并发控制器
    concurrency = AdaptiveConcurrency(
        initial_workers=5,
        min_workers=1,
        max_workers=20
    )
    
    # 模拟任务
    @concurrency
    async def task(task_id: int, fail_probability: float = 0.1):
        """模拟任务
        
        Args:
            task_id: 任务ID
            fail_probability: 失败概率
        """
        print(f"Task {task_id} started, workers: {concurrency.max_workers}")
        await asyncio.sleep(0.1)  # 模拟工作
        
        # 模拟随机失败
        if time.time() % 1 < fail_probability:
            raise Exception(f"Task {task_id} failed")
            
        print(f"Task {task_id} completed")
        
    async def main():
        """主函数"""
        tasks = [
            task(i)
            for i in range(100)
        ]
        await asyncio.gather(*tasks, return_exceptions=True)
        
    # 运行示例
    asyncio.run(main()) 