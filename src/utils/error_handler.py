import functools
import traceback
import asyncio
from typing import Callable, Any, Dict, Optional, Type, List
from datetime import datetime
from .logger import get_logger
from .exceptions import CrawlerException

logger = get_logger(__name__)

def handle_error(
    error_type: Type[CrawlerException],
    reraise: bool = True,
    log_level: str = "error",
    **kwargs
) -> Callable:
    """错误处理装饰器
    
    Args:
        error_type: 异常类型
        reraise: 是否重新抛出异常
        log_level: 日志级别
        **kwargs: 传递给异常的额外参数
    
    Returns:
        Callable: 装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kw) -> Any:
            try:
                return await func(*args, **kw)
            except Exception as e:
                # 获取错误信息
                error_info = _get_error_info(e)
                
                # 创建自定义异常
                custom_error = error_type(
                    message=str(e),
                    details={**kwargs, **error_info}
                )
                
                # 记录日志
                _log_error(custom_error, log_level)
                
                # 重新抛出异常
                if reraise:
                    raise custom_error from e
                    
                return None
                
        @functools.wraps(func)
        def sync_wrapper(*args, **kw) -> Any:
            try:
                return func(*args, **kw)
            except Exception as e:
                # 获取错误信息
                error_info = _get_error_info(e)
                
                # 创建自定义异常
                custom_error = error_type(
                    message=str(e),
                    details={**kwargs, **error_info}
                )
                
                # 记录日志
                _log_error(custom_error, log_level)
                
                # 重新抛出异常
                if reraise:
                    raise custom_error from e
                    
                return None
                
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

def _get_error_info(error: Exception) -> Dict[str, Any]:
    """获取错误信息
    
    Args:
        error: 异常对象
    
    Returns:
        Dict[str, Any]: 错误信息字典
    """
    return {
        "error_type": error.__class__.__name__,
        "traceback": traceback.format_exc(),
        "timestamp": datetime.now().isoformat()
    }

def _log_error(
    error: CrawlerException,
    level: str = "error"
) -> None:
    """记录错误日志
    
    Args:
        error: 异常对象
        level: 日志级别
    """
    log_func = getattr(logger, level)
    log_func(
        f"{error}\n"
        f"Details: {error.details}\n"
        f"Traceback: {error.details.get('traceback')}"
    )

class ErrorHandler:
    """错误处理器"""
    
    def __init__(self):
        """初始化错误处理器"""
        self.errors: List[Dict[str, Any]] = []
        self.max_errors = 1000  # 最多保存1000条错误记录
        
    def add_error(
        self,
        error: CrawlerException,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """添加错误记录
        
        Args:
            error: 异常对象
            context: 上下文信息
        """
        error_info = {
            "code": error.code,
            "message": error.message,
            "details": error.details,
            "context": context or {},
            "timestamp": datetime.now().isoformat()
        }
        
        self.errors.append(error_info)
        
        # 如果错误记录超过最大数量，删除最早的记录
        if len(self.errors) > self.max_errors:
            self.errors = self.errors[-self.max_errors:]
            
    def get_errors(
        self,
        error_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取错误记录
        
        Args:
            error_type: 错误类型
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回数量限制
            
        Returns:
            List[Dict[str, Any]]: 错误记录列表
        """
        filtered_errors = self.errors
        
        # 按错误类型过滤
        if error_type:
            filtered_errors = [
                e for e in filtered_errors
                if e["code"] == error_type
            ]
            
        # 按时间范围过滤
        if start_time:
            filtered_errors = [
                e for e in filtered_errors
                if datetime.fromisoformat(e["timestamp"]) >= start_time
            ]
            
        if end_time:
            filtered_errors = [
                e for e in filtered_errors
                if datetime.fromisoformat(e["timestamp"]) <= end_time
            ]
            
        # 返回最新的记录
        return filtered_errors[-limit:]
        
    def clear_errors(self) -> None:
        """清空错误记录"""
        self.errors = []
        
    def get_error_stats(self) -> Dict[str, Any]:
        """获取错误统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        stats = {
            "total": len(self.errors),
            "by_type": {},
            "by_hour": {}
        }
        
        # 按类型统计
        for error in self.errors:
            error_type = error["code"]
            stats["by_type"][error_type] = stats["by_type"].get(error_type, 0) + 1
            
        # 按小时统计
        now = datetime.now()
        for error in self.errors:
            error_time = datetime.fromisoformat(error["timestamp"])
            if (now - error_time).total_seconds() <= 3600:  # 一小时内
                hour = error_time.strftime("%Y-%m-%d %H:00:00")
                stats["by_hour"][hour] = stats["by_hour"].get(hour, 0) + 1
                
        return stats 