"""限流中间件"""

import time
from typing import Dict, Tuple, Optional, Callable
from fastapi import Request, HTTPException
from ..config import Config

config = Config()

class RateLimiter:
    """限流器"""
    
    def __init__(self):
        """初始化限流器"""
        # 从配置加载限流规则
        self.rules = config.get("rate_limit", {
            "default": {
                "requests": 100,    # 请求数
                "period": 60        # 时间窗口（秒）
            },
            "api": {
                "requests": 1000,
                "period": 3600
            },
            "crawler": {
                "requests": 10,
                "period": 60
            }
        })
        
        # 存储请求记录
        self.requests: Dict[str, Dict[str, Tuple[int, float]]] = {
            "ip": {},      # IP限流
            "user": {},    # 用户限流
            "api": {}      # 接口限流
        }
        
    def _clean_old_requests(self, key: str, rule_name: str):
        """清理过期的请求记录
        
        Args:
            key: 限流键（IP/用户ID/API路径）
            rule_name: 规则名称
        """
        now = time.time()
        period = self.rules[rule_name]["period"]
        
        # 删除超过时间窗口的记录
        self.requests[rule_name] = {
            k: v for k, v in self.requests[rule_name].items()
            if now - v[1] < period
        }
        
    def is_allowed(
        self,
        key: str,
        rule_name: str = "default"
    ) -> Tuple[bool, Optional[int]]:
        """检查请求是否允许
        
        Args:
            key: 限流键（IP/用户ID/API路径）
            rule_name: 规则名称
            
        Returns:
            Tuple[bool, Optional[int]]: (是否允许, 剩余等待时间)
        """
        if rule_name not in self.rules:
            rule_name = "default"
            
        rule = self.rules[rule_name]
        now = time.time()
        
        # 清理过期记录
        self._clean_old_requests(key, rule_name)
        
        # 获取当前记录
        if key not in self.requests[rule_name]:
            self.requests[rule_name][key] = (0, now)
            
        count, start_time = self.requests[rule_name][key]
        
        # 如果在时间窗口内
        if now - start_time < rule["period"]:
            if count >= rule["requests"]:
                wait_time = int(rule["period"] - (now - start_time))
                return False, wait_time
            else:
                self.requests[rule_name][key] = (count + 1, start_time)
                return True, None
        else:
            # 开始新的时间窗口
            self.requests[rule_name][key] = (1, now)
            return True, None

class RateLimitMiddleware:
    """限流中间件"""
    
    def __init__(self):
        """初始化限流中间件"""
        self.limiter = RateLimiter()
        
    async def __call__(
        self,
        request: Request,
        call_next: Callable
    ):
        """处理请求
        
        Args:
            request: 请求对象
            call_next: 下一个处理器
            
        Returns:
            响应对象
            
        Raises:
            HTTPException: 请求被限流
        """
        # 获取客户端IP
        client_ip = request.client.host
        
        # 获取用户ID（如果已认证）
        user_id = None
        if hasattr(request.state, "user"):
            user_id = request.state.user.id
            
        # 获取API路径
        api_path = request.url.path
        
        # 检查IP限流
        allowed, wait_time = self.limiter.is_allowed(client_ip, "default")
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail=f"Too many requests. Please try again in {wait_time} seconds."
            )
            
        # 检查用户限流
        if user_id:
            allowed, wait_time = self.limiter.is_allowed(
                f"user:{user_id}",
                "api"
            )
            if not allowed:
                raise HTTPException(
                    status_code=429,
                    detail=f"Too many requests. Please try again in {wait_time} seconds."
                )
                
        # 检查API限流
        if "crawler" in api_path:
            allowed, wait_time = self.limiter.is_allowed(
                f"api:{api_path}",
                "crawler"
            )
            if not allowed:
                raise HTTPException(
                    status_code=429,
                    detail=f"Too many requests. Please try again in {wait_time} seconds."
                )
                
        # 继续处理请求
        response = await call_next(request)
        return response

# 创建全局限流中间件实例
rate_limit_middleware = RateLimitMiddleware() 