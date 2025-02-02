"""熔断器示例"""

import time
from enum import Enum
from typing import Callable, Any, Optional
from functools import wraps

class CircuitState(Enum):
    """熔断器状态"""
    CLOSED = "CLOSED"        # 关闭状态（正常）
    OPEN = "OPEN"           # 开启状态（熔断）
    HALF_OPEN = "HALF_OPEN" # 半开启状态（尝试恢复）

class CircuitBreaker:
    """熔断器"""
    
    def __init__(
        self,
        fail_max: int = 5,
        reset_timeout: int = 60,
        half_open_timeout: int = 30,
        exclude_exceptions: Optional[tuple] = None
    ):
        """初始化熔断器
        
        Args:
            fail_max: 最大失败次数
            reset_timeout: 重置超时时间（秒）
            half_open_timeout: 半开启超时时间（秒）
            exclude_exceptions: 不计入失败的异常类型
        """
        self.fail_max = fail_max
        self.reset_timeout = reset_timeout
        self.half_open_timeout = half_open_timeout
        self.exclude_exceptions = exclude_exceptions or ()
        
        self.state = CircuitState.CLOSED
        self.last_failure_time = 0
        self.failure_count = 0
        
    def _can_try(self) -> bool:
        """是否可以尝试执行
        
        Returns:
            bool: 是否可以尝试
        """
        if self.state == CircuitState.CLOSED:
            return True
            
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.reset_timeout:
                self.state = CircuitState.HALF_OPEN
                return True
            return False
            
        # HALF_OPEN状态
        if time.time() - self.last_failure_time >= self.half_open_timeout:
            return True
        return False
        
    def _handle_success(self):
        """处理成功情况"""
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        
    def _handle_failure(self, exception: Exception):
        """处理失败情况
        
        Args:
            exception: 异常对象
        """
        if isinstance(exception, self.exclude_exceptions):
            return
            
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            return
            
        self.failure_count += 1
        if self.failure_count >= self.fail_max:
            self.state = CircuitState.OPEN
            
    def __call__(self, func: Callable) -> Callable:
        """装饰器实现
        
        Args:
            func: 被装饰的函数
            
        Returns:
            Callable: 装饰后的函数
        """
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            if not self._can_try():
                raise Exception(
                    f"Circuit breaker is {self.state.value}, "
                    f"wait {self.reset_timeout}s"
                )
                
            try:
                result = await func(*args, **kwargs)
                self._handle_success()
                return result
            except Exception as e:
                self._handle_failure(e)
                raise e
                
        return wrapper

# 使用示例
if __name__ == "__main__":
    import asyncio
    import random
    
    # 创建熔断器
    breaker = CircuitBreaker(
        fail_max=3,
        reset_timeout=5,
        half_open_timeout=2
    )
    
    # 模拟不稳定的API
    @breaker
    async def unstable_api(request_id: int):
        """模拟不稳定的API
        
        Args:
            request_id: 请求ID
        """
        print(f"Request {request_id} started, state: {breaker.state.value}")
        
        # 模拟随机失败
        if random.random() < 0.6:
            raise Exception(f"Request {request_id} failed")
            
        await asyncio.sleep(0.1)  # 模拟API调用
        print(f"Request {request_id} completed")
        
    async def main():
        """主函数"""
        for i in range(10):
            try:
                await unstable_api(i)
            except Exception as e:
                print(f"Error: {str(e)}")
            await asyncio.sleep(1)  # 等待1秒
            
    # 运行示例
    asyncio.run(main()) 