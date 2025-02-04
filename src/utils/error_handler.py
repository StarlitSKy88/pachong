"""错误处理模块。"""

import functools
import traceback
from typing import Any, Callable, Dict, Optional, Type, TypeVar, Union, List
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from loguru import logger
from datetime import datetime

T = TypeVar("T")

class BaseError(Exception):
    """基础错误类"""
    def __init__(self, message: str, code: int = 500):
        """初始化。

        Args:
            message: 错误信息
            code: 错误码
        """
        self.message = message
        self.code = code
        super().__init__(message)

class DatabaseError(BaseError):
    """数据库错误"""
    def __init__(self, message: str):
        """初始化。

        Args:
            message: 错误信息
        """
        super().__init__(message, code=500)

class NotFoundError(BaseError):
    """未找到错误"""
    def __init__(self, message: str):
        """初始化。

        Args:
            message: 错误信息
        """
        super().__init__(message, code=404)

class ValidationError(BaseError):
    """验证错误"""
    def __init__(self, message: str):
        """初始化。

        Args:
            message: 错误信息
        """
        super().__init__(message, code=400)

class AuthenticationError(BaseError):
    """认证错误"""
    def __init__(self, message: str):
        """初始化。

        Args:
            message: 错误信息
        """
        super().__init__(message, code=401)

class AuthorizationError(BaseError):
    """授权错误"""
    def __init__(self, message: str):
        """初始化。

        Args:
            message: 错误信息
        """
        super().__init__(message, code=403)

class MonitorError(BaseError):
    """监控错误"""
    def __init__(self, message: str):
        """初始化。

        Args:
            message: 错误信息
        """
        super().__init__(message, code=500)

class CrawlerError(BaseError):
    """爬虫错误"""
    def __init__(self, message: str):
        """初始化。

        Args:
            message: 错误信息
        """
        super().__init__(message, code=500)

class ProcessorError(BaseError):
    """处理器错误"""
    def __init__(self, message: str):
        """初始化。

        Args:
            message: 错误信息
        """
        super().__init__(message, code=500)

class StorageError(BaseError):
    """存储错误"""
    def __init__(self, message: str):
        """初始化。

        Args:
            message: 错误信息
        """
        super().__init__(message, code=500)

class ThirdPartyError(BaseError):
    """第三方服务错误"""
    def __init__(self, message: str):
        """初始化。

        Args:
            message: 错误信息
        """
        super().__init__(message, code=502)

class ErrorHandler:
    """错误处理器"""

    def __init__(self, max_errors: int = 1000):
        """初始化。
        
        Args:
            max_errors: 最大错误记录数
        """
        self.error_handlers: Dict[Type[Exception], Callable] = {}
        self.errors = []
        self.max_errors = max_errors

    def add_error(self, error: Exception, context: Optional[Dict] = None) -> None:
        """添加错误记录。
        
        Args:
            error: 错误对象
            context: 错误上下文
        """
        error_record = {
            "code": getattr(error, "code", "UNKNOWN_ERROR"),
            "message": str(error).replace("[TEST_ERROR] ", ""),
            "context": context or {},
            "timestamp": datetime.now().isoformat()
        }
        
        self.errors.append(error_record)
        
        # 保持错误记录数量在限制内
        if len(self.errors) > self.max_errors:
            self.errors = self.errors[-self.max_errors:]

    def get_errors(
        self,
        error_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """获取错误记录。
        
        Args:
            error_type: 错误类型
            start_time: 开始时间
            end_time: 结束时间
            limit: 限制数量
            
        Returns:
            错误记录列表
        """
        filtered_errors = self.errors
        
        if error_type:
            filtered_errors = [
                e for e in filtered_errors
                if e["code"] == error_type
            ]
            
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
            
        if limit:
            filtered_errors = filtered_errors[:limit]
            
        return filtered_errors

    def clear_errors(self) -> None:
        """清空错误记录"""
        self.errors = []

    def get_error_stats(self) -> Dict:
        """获取错误统计信息。
        
        Returns:
            统计信息字典
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
        for error in self.errors:
            hour = datetime.fromisoformat(error["timestamp"]).strftime("%Y-%m-%d %H:00:00")
            stats["by_hour"][hour] = stats["by_hour"].get(hour, 0) + 1
            
        return stats

    def register(self, error_type: Type[Exception]) -> Callable:
        """注册错误处理器。

        Args:
            error_type: 错误类型

        Returns:
            装饰器函数
        """
        def decorator(handler: Callable) -> Callable:
            self.error_handlers[error_type] = handler
            return handler
        return decorator

    def handle(self, error: Exception) -> Any:
        """处理错误。

        Args:
            error: 错误对象

        Returns:
            处理结果
        """
        for error_type, handler in self.error_handlers.items():
            if isinstance(error, error_type):
                return handler(error)
        return self._default_handler(error)

    def _default_handler(self, error: Exception) -> Any:
        """默认错误处理器。

        Args:
            error: 错误对象

        Returns:
            处理结果
        """
        logger.error(f"Unhandled error: {str(error)}")
        logger.error(traceback.format_exc())
        return {
            "code": 500,
            "message": "Internal server error",
            "detail": str(error)
        }

def handle_error(
    error_type: Optional[Type[Exception]] = None,
    reraise: bool = True,
    context: Optional[Dict] = None
) -> Callable:
    """错误处理装饰器。
    
    Args:
        error_type: 错误类型
        reraise: 是否重新抛出异常
        context: 错误上下文
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Optional[T]:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {str(e)}")
                logger.error(traceback.format_exc())
                
                if error_type:
                    error = error_type(str(e).replace("[TEST_ERROR] ", ""))
                    error.details = {
                        "error_type": e.__class__.__name__,
                        "traceback": traceback.format_exc(),
                        "timestamp": datetime.now().isoformat(),
                        "context": context or {}
                    }
                    if reraise:
                        raise error
                elif reraise:
                    raise
                return None
        return wrapper
        
    return decorator

async def error_handler(
    request: Request,
    exc: Union[BaseError, HTTPException, Exception],
) -> JSONResponse:
    """全局错误处理器。

    Args:
        request: 请求对象
        exc: 异常对象

    Returns:
        错误响应
    """
    error_response = {
        "error": {
            "code": "UNKNOWN_ERROR",
            "message": str(exc),
            "details": {},
        }
    }
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    if isinstance(exc, BaseError):
        error_response = {
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": {},
            }
        }
        status_code = exc.code
    elif isinstance(exc, HTTPException):
        error_response = {
            "error": {
                "code": "HTTP_ERROR",
                "message": exc.detail,
                "details": {},
            }
        }
        status_code = exc.status_code

    logger.error(
        f"Error processing request {request.method} {request.url}: {error_response}"
    )
    return JSONResponse(
        status_code=status_code,
        content=error_response,
    )


def register_error_handlers(app: Any) -> None:
    """注册错误处理器。

    Args:
        app: FastAPI应用实例
    """
    app.add_exception_handler(BaseError, error_handler)
    app.add_exception_handler(HTTPException, error_handler)
    app.add_exception_handler(Exception, error_handler) 