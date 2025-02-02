import time
import random
import logging
from functools import wraps
from typing import Callable, Any, Optional
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)

def retry_request(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (RequestException,)
):
    """
    请求重试装饰器
    
    参数:
        max_retries: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff: 延迟时间的增长倍数
        exceptions: 需要重试的异常类型
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            retry_count = 0
            current_delay = delay

            while retry_count < max_retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    retry_count += 1
                    if retry_count == max_retries:
                        logger.error(f"重试{max_retries}次后仍然失败: {str(e)}")
                        raise

                    # 添加随机抖动，避免同时请求
                    jitter = random.uniform(0, 0.1 * current_delay)
                    sleep_time = current_delay + jitter
                    
                    logger.warning(
                        f"请求失败 ({str(e)}), "
                        f"将在 {sleep_time:.2f} 秒后进行第 {retry_count + 1} 次重试"
                    )
                    
                    time.sleep(sleep_time)
                    current_delay *= backoff

        return wrapper
    return decorator

def retry_with_proxy(
    proxy_getter: Callable[[], Optional[dict]],
    max_retries: int = 3,
    delay: float = 1.0,
    exceptions: tuple = (RequestException,)
):
    """
    带代理切换的重试装饰器
    
    参数:
        proxy_getter: 获取代理的函数
        max_retries: 最大重试次数
        delay: 重试延迟时间（秒）
        exceptions: 需要重试的异常类型
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            retry_count = 0
            
            while retry_count < max_retries:
                proxy = proxy_getter()
                if proxy:
                    kwargs['proxies'] = proxy
                
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    retry_count += 1
                    if retry_count == max_retries:
                        logger.error(f"使用代理重试{max_retries}次后仍然失败: {str(e)}")
                        raise

                    sleep_time = delay * (1 + random.random())
                    logger.warning(
                        f"使用代理 {proxy} 请求失败 ({str(e)}), "
                        f"将在 {sleep_time:.2f} 秒后切换代理重试"
                    )
                    time.sleep(sleep_time)

        return wrapper
    return decorator 