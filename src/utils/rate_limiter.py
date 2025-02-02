import time
import random
import logging
import asyncio
from typing import Dict, Optional
from datetime import datetime, timedelta
from threading import Lock

class TokenBucket:
    """令牌桶实现"""
    
    def __init__(self, capacity: int, fill_rate: float):
        """
        初始化令牌桶
        
        Args:
            capacity: 桶容量（最大令牌数）
            fill_rate: 令牌填充速率（每秒）
        """
        self.capacity = capacity
        self.fill_rate = fill_rate
        self.tokens = capacity
        self.last_fill_time = time.time()
        self.lock = Lock()
    
    def _fill_tokens(self):
        """填充令牌"""
        now = time.time()
        delta = now - self.last_fill_time
        new_tokens = delta * self.fill_rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_fill_time = now
    
    def consume(self, tokens: int = 1) -> bool:
        """
        消费令牌
        
        Args:
            tokens: 需要消费的令牌数

        Returns:
            是否获取到足够的令牌
        """
        with self.lock:
            self._fill_tokens()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

class RateLimiter:
    """速率限制器"""
    
    def __init__(self, rate: float = 1.0):
        """初始化
        
        Args:
            rate: 每秒请求次数
        """
        self.rate = rate
        self.last_request_time = 0
        self._lock = asyncio.Lock()
        
    async def set_rate(self, rate: float):
        """设置速率
        
        Args:
            rate: 每秒请求次数
        """
        async with self._lock:
            self.rate = rate
            
    async def acquire(self):
        """获取令牌"""
        async with self._lock:
            now = time.time()
            if self.last_request_time > 0:
                wait_time = (1 / self.rate) - (now - self.last_request_time)
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
            self.last_request_time = time.time()
            
    async def __aenter__(self):
        """进入上下文"""
        await self.acquire()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        pass

# 创建全局实例
rate_limiter = RateLimiter() 