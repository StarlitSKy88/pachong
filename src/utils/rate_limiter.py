import time
import random
import logging
import asyncio
from typing import Dict, Optional
from datetime import datetime, timedelta
from threading import Lock
from collections import deque

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
    """请求频率限制器"""
    
    def __init__(self, max_requests: int = 100, time_window: int = 60):
        """初始化
        
        Args:
            max_requests: 时间窗口内最大请求数
            time_window: 时间窗口大小(秒)
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()  # 请求时间队列
        self.last_request_time = {}  # 每个域名的最后请求时间
        self.min_interval = 1  # 最小请求间隔(秒)
        
    async def acquire(self, domain: str = 'default') -> bool:
        """获取请求许可
        
        Args:
            domain: 请求域名
            
        Returns:
            是否允许请求
        """
        now = time.time()
        
        # 清理过期请求
        while self.requests and now - self.requests[0] > self.time_window:
            self.requests.popleft()
            
        # 检查请求数量
        if len(self.requests) >= self.max_requests:
            return False
            
        # 检查请求间隔
        last_time = self.last_request_time.get(domain, 0)
        if now - last_time < self.min_interval:
            await asyncio.sleep(self.min_interval - (now - last_time))
            
        # 记录请求
        self.requests.append(now)
        self.last_request_time[domain] = now
        
        return True
        
    def update_limits(self, success: bool):
        """更新限制
        
        Args:
            success: 请求是否成功
        """
        if success:
            # 成功则适当放宽限制
            self.min_interval = max(1, self.min_interval * 0.9)
        else:
            # 失败则收紧限制
            self.min_interval = min(10, self.min_interval * 2)
            
class TokenBucket:
    """令牌桶限流器"""
    
    def __init__(self, capacity: int = 100, fill_rate: float = 1.0):
        """初始化
        
        Args:
            capacity: 桶容量
            fill_rate: 令牌填充速率(个/秒)
        """
        self.capacity = capacity
        self.fill_rate = fill_rate
        self.tokens = capacity
        self.last_fill = time.time()
        self.lock = asyncio.Lock()
        
    async def acquire(self, tokens: int = 1) -> bool:
        """获取令牌
        
        Args:
            tokens: 需要的令牌数
            
        Returns:
            是否获取成功
        """
        async with self.lock:
            now = time.time()
            
            # 添加令牌
            elapsed = now - self.last_fill
            new_tokens = elapsed * self.fill_rate
            self.tokens = min(self.capacity, self.tokens + new_tokens)
            self.last_fill = now
            
            # 获取令牌
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
                
            return False
            
class SlidingWindow:
    """滑动窗口限流器"""
    
    def __init__(self, window_size: int = 60, max_requests: int = 100):
        """初始化
        
        Args:
            window_size: 窗口大小(秒)
            max_requests: 窗口内最大请求数
        """
        self.window_size = window_size
        self.max_requests = max_requests
        self.requests = deque()
        self.lock = asyncio.Lock()
        
    async def acquire(self) -> bool:
        """获取请求许可
        
        Returns:
            是否允许请求
        """
        async with self.lock:
            now = time.time()
            
            # 清理过期请求
            while self.requests and now - self.requests[0] > self.window_size:
                self.requests.popleft()
                
            # 检查请求数量
            if len(self.requests) >= self.max_requests:
                return False
                
            # 记录请求
            self.requests.append(now)
            return True

# 创建全局实例
rate_limiter = RateLimiter() 