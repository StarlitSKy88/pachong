"""熔断器工具类"""

import time
import logging
from functools import wraps
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)

class CircuitBreaker:
    """熔断器类"""
    
    # 存储所有断路器实例
    breakers: Dict[str, 'CircuitBreaker'] = {}
    
    def __init__(self, failure_threshold: int = 5, reset_timeout: int = 60):
        """初始化
        
        Args:
            failure_threshold: 失败阈值
            reset_timeout: 重置超时时间（秒）
        """
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        
    def record_failure(self):
        """记录失败"""
        self.failures += 1
        self.last_failure_time = time.time()
        
        if self.failures >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"Circuit breaker opened after {self.failures} failures")
            
    def record_success(self):
        """记录成功"""
        self.failures = 0
        self.state = "CLOSED"
        
    def can_execute(self) -> bool:
        """是否可以执行"""
        if self.state == "CLOSED":
            return True
            
        if self.state == "OPEN":
            if time.time() - self.last_failure_time >= self.reset_timeout:
                self.state = "HALF_OPEN"
                return True
            return False
            
        # HALF_OPEN state
        return True
        
    def reset(self):
        """重置断路器状态"""
        self.failures = 0
        self.last_failure_time = 0
        self.state = "CLOSED"
        
    @classmethod
    def reset_all(cls):
        """重置所有断路器"""
        for breaker in cls.breakers.values():
            breaker.reset()
        cls.breakers.clear()

def circuit_breaker(failure_threshold: int = 5, reset_timeout: int = 60):
    """熔断器装饰器
    
    Args:
        failure_threshold: 失败阈值
        reset_timeout: 重置超时时间（秒）
    """
    breaker = CircuitBreaker(failure_threshold, reset_timeout)
    
    # 存储断路器实例
    func_name = f"breaker_{len(CircuitBreaker.breakers)}"
    CircuitBreaker.breakers[func_name] = breaker
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            if not breaker.can_execute():
                logger.error("Circuit breaker is OPEN, request rejected")
                raise RuntimeError("Circuit breaker is OPEN")
                
            try:
                result = await func(*args, **kwargs)
                breaker.record_success()
                return result
            except Exception as e:
                breaker.record_failure()
                raise
                
        return wrapper
    return decorator 