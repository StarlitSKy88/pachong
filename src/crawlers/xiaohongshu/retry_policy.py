"""重试策略模块"""

import asyncio
import logging
from typing import Any, Optional

import aiohttp


class RetryPolicy:
    """重试策略类"""

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        """初始化重试策略

        Args:
            max_retries: 最大重试次数
            base_delay: 基础延迟时间(秒)
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.logger = logging.getLogger(__name__)

    def should_retry(self, error: Exception) -> bool:
        """判断是否需要重试

        Args:
            error: 异常对象

        Returns:
            是否需要重试
        """
        # 对于网络错误和服务器错误进行重试
        if isinstance(error, (aiohttp.ClientError, aiohttp.ServerTimeoutError)):
            return True

        # 对于HTTP错误,只重试特定状态码
        if isinstance(error, aiohttp.ClientResponseError):
            return error.status in {500, 502, 503, 504}

        return False

    def get_delay(self, retry_count: int) -> float:
        """获取重试延迟时间

        Args:
            retry_count: 当前重试次数

        Returns:
            延迟时间(秒)
        """
        # 使用指数退避策略
        delay = self.base_delay * (2 ** retry_count)
        # 添加随机抖动
        jitter = delay * 0.1
        delay += jitter
        return delay 