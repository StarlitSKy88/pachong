import asyncio
import functools
import logging
import random
from datetime import datetime
from typing import Type, Callable, Optional, Union, Tuple, List

logger = logging.getLogger(__name__)

class RetryError(Exception):
    """重试失败异常"""
    def __init__(self, message: str, last_error: Optional[Exception] = None):
        super().__init__(message)
        self.last_error = last_error

def exponential_backoff(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0, jitter: bool = True) -> float:
    """
    计算指数退避延迟时间
    
    Args:
        attempt: 当前重试次数
        base_delay: 基础延迟时间（秒）
        max_delay: 最大延迟时间（秒）
        jitter: 是否添加随机抖动
    
    Returns:
        延迟时间（秒）
    """
    delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
    if jitter:
        delay *= random.uniform(0.5, 1.5)
    return delay

class RetryPolicy:
    """重试策略配置"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        jitter: bool = True,
        retry_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
        retry_on_result: Optional[Callable[[any], bool]] = None,
        on_retry: Optional[Callable[[int, Exception, float], None]] = None
    ):
        """
        初始化重试策略
        
        Args:
            max_attempts: 最大重试次数
            base_delay: 基础延迟时间（秒）
            max_delay: 最大延迟时间（秒）
            jitter: 是否添加随机抖动
            retry_exceptions: 需要重试的异常类型
            retry_on_result: 基于返回结果判断是否需要重试的函数
            on_retry: 重试回调函数，参数为(尝试次数, 异常, 延迟时间)
        """
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter
        self.retry_exceptions = retry_exceptions or (Exception,)
        self.retry_on_result = retry_on_result
        self.on_retry = on_retry or self._default_on_retry
    
    def _default_on_retry(self, attempt: int, error: Exception, delay: float):
        """默认的重试回调函数"""
        logger.warning(
            f"Retry attempt {attempt}/{self.max_attempts} after error: {str(error)}. "
            f"Waiting {delay:.2f} seconds..."
        )
    
    def should_retry(self, attempt: int, error: Optional[Exception] = None, result: any = None) -> bool:
        """
        判断是否应该重试
        
        Args:
            attempt: 当前重试次数
            error: 捕获的异常
            result: 函数返回结果
        
        Returns:
            是否需要重试
        """
        # 超过最大重试次数
        if attempt >= self.max_attempts:
            return False
        
        # 有异常且异常类型匹配
        if error is not None:
            return isinstance(error, self.retry_exceptions)
        
        # 检查返回结果
        if self.retry_on_result is not None:
            return self.retry_on_result(result)
        
        return False
    
    def get_delay(self, attempt: int) -> float:
        """获取重试延迟时间"""
        return exponential_backoff(
            attempt,
            self.base_delay,
            self.max_delay,
            self.jitter
        )

def retry(
    max_attempts: Optional[int] = None,
    base_delay: Optional[float] = None,
    max_delay: Optional[float] = None,
    jitter: Optional[bool] = None,
    retry_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    retry_on_result: Optional[Callable[[any], bool]] = None,
    on_retry: Optional[Callable[[int, Exception, float], None]] = None,
    policy: Optional[RetryPolicy] = None
):
    """
    重试装饰器
    
    Args:
        max_attempts: 最大重试次数
        base_delay: 基础延迟时间（秒）
        max_delay: 最大延迟时间（秒）
        jitter: 是否添加随机抖动
        retry_exceptions: 需要重试的异常类型
        retry_on_result: 基于返回结果判断是否需要重试的函数
        on_retry: 重试回调函数
        policy: 重试策略，如果提供则忽略其他参数
    """
    def decorator(func):
        # 确定使用的重试策略
        retry_policy = policy or RetryPolicy(
            max_attempts=max_attempts if max_attempts is not None else 3,
            base_delay=base_delay if base_delay is not None else 1.0,
            max_delay=max_delay if max_delay is not None else 60.0,
            jitter=jitter if jitter is not None else True,
            retry_exceptions=retry_exceptions,
            retry_on_result=retry_on_result,
            on_retry=on_retry
        )
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            attempt = 1
            last_error = None
            
            while True:
                try:
                    result = await func(*args, **kwargs)
                    
                    # 检查返回结果是否需要重试
                    if retry_policy.should_retry(attempt, result=result):
                        delay = retry_policy.get_delay(attempt)
                        retry_policy.on_retry(attempt, last_error, delay)
                        await asyncio.sleep(delay)
                        attempt += 1
                        continue
                    
                    return result
                    
                except Exception as e:
                    last_error = e
                    
                    # 检查是否需要重试
                    if retry_policy.should_retry(attempt, error=e):
                        delay = retry_policy.get_delay(attempt)
                        retry_policy.on_retry(attempt, e, delay)
                        await asyncio.sleep(delay)
                        attempt += 1
                        continue
                    
                    raise RetryError(
                        f"Failed after {attempt} attempts. Last error: {str(e)}",
                        last_error=e
                    ) from e
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            attempt = 1
            last_error = None
            
            while True:
                try:
                    result = func(*args, **kwargs)
                    
                    # 检查返回结果是否需要重试
                    if retry_policy.should_retry(attempt, result=result):
                        delay = retry_policy.get_delay(attempt)
                        retry_policy.on_retry(attempt, last_error, delay)
                        time.sleep(delay)
                        attempt += 1
                        continue
                    
                    return result
                    
                except Exception as e:
                    last_error = e
                    
                    # 检查是否需要重试
                    if retry_policy.should_retry(attempt, error=e):
                        delay = retry_policy.get_delay(attempt)
                        retry_policy.on_retry(attempt, e, delay)
                        time.sleep(delay)
                        attempt += 1
                        continue
                    
                    raise RetryError(
                        f"Failed after {attempt} attempts. Last error: {str(e)}",
                        last_error=e
                    ) from e
        
        # 根据函数类型返回对应的包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator

# 预定义的重试策略
DEFAULT_RETRY_POLICY = RetryPolicy()

AGGRESSIVE_RETRY_POLICY = RetryPolicy(
    max_attempts=5,
    base_delay=2.0,
    max_delay=120.0,
    jitter=True
)

CONSERVATIVE_RETRY_POLICY = RetryPolicy(
    max_attempts=2,
    base_delay=1.0,
    max_delay=30.0,
    jitter=True
) 