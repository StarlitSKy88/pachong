"""错误处理模块。"""

from typing import Any, Dict, Optional, Type, Union

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

from src.utils.logger import get_logger

logger = get_logger(__name__)


class BaseError(Exception):
    """基础错误类。"""

    def __init__(
        self,
        message: str,
        code: str = "UNKNOWN_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """初始化错误。

        Args:
            message: 错误消息
            code: 错误代码
            status_code: HTTP状态码
            details: 错误详情
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class ValidationError(BaseError):
    """验证错误。"""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """初始化验证错误。

        Args:
            message: 错误消息
            details: 错误详情
        """
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class AuthenticationError(BaseError):
    """认证错误。"""

    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """初始化认证错误。

        Args:
            message: 错误消息
            details: 错误详情
        """
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


class AuthorizationError(BaseError):
    """授权错误。"""

    def __init__(
        self,
        message: str = "Permission denied",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """初始化授权错误。

        Args:
            message: 错误消息
            details: 错误详情
        """
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR",
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class NotFoundError(BaseError):
    """资源不存在错误。"""

    def __init__(
        self,
        message: str = "Resource not found",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """初始化资源不存在错误。

        Args:
            message: 错误消息
            details: 错误详情
        """
        super().__init__(
            message=message,
            code="NOT_FOUND_ERROR",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class ConflictError(BaseError):
    """资源冲突错误。"""

    def __init__(
        self,
        message: str = "Resource conflict",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """初始化资源冲突错误。

        Args:
            message: 错误消息
            details: 错误详情
        """
        super().__init__(
            message=message,
            code="CONFLICT_ERROR",
            status_code=status.HTTP_409_CONFLICT,
            details=details,
        )


class RateLimitError(BaseError):
    """请求频率限制错误。"""

    def __init__(
        self,
        message: str = "Too many requests",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """初始化请求频率限制错误。

        Args:
            message: 错误消息
            details: 错误详情
        """
        super().__init__(
            message=message,
            code="RATE_LIMIT_ERROR",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details,
        )


class DatabaseError(BaseError):
    """数据库错误。"""

    def __init__(
        self,
        message: str = "Database error",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """初始化数据库错误。

        Args:
            message: 错误消息
            details: 错误详情
        """
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class CrawlerError(BaseError):
    """爬虫错误。"""

    def __init__(
        self,
        message: str = "Crawler error",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """初始化爬虫错误。

        Args:
            message: 错误消息
            details: 错误详情
        """
        super().__init__(
            message=message,
            code="CRAWLER_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class ProcessorError(BaseError):
    """处理器错误。"""

    def __init__(
        self,
        message: str = "Processor error",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """初始化处理器错误。

        Args:
            message: 错误消息
            details: 错误详情
        """
        super().__init__(
            message=message,
            code="PROCESSOR_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class StorageError(BaseError):
    """存储错误。"""

    def __init__(
        self,
        message: str = "Storage error",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """初始化存储错误。

        Args:
            message: 错误消息
            details: 错误详情
        """
        super().__init__(
            message=message,
            code="STORAGE_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class ThirdPartyError(BaseError):
    """第三方服务错误。"""

    def __init__(
        self,
        message: str = "Third party service error",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """初始化第三方服务错误。

        Args:
            message: 错误消息
            details: 错误详情
        """
        super().__init__(
            message=message,
            code="THIRD_PARTY_ERROR",
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details,
        )


async def error_handler(
    request: Request,
    exc: Union[BaseError, HTTPException, Exception],
) -> JSONResponse:
    """统一错误处理器。

    Args:
        request: 请求对象
        exc: 异常对象

    Returns:
        JSONResponse: JSON响应
    """
    if isinstance(exc, BaseError):
        error_response = {
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        }
        status_code = exc.status_code
    elif isinstance(exc, HTTPException):
        error_response = {
            "error": {
                "code": "HTTP_ERROR",
                "message": exc.detail,
                "details": {},
            }
        }
        status_code = exc.status_code
    else:
        error_response = {
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": str(exc),
                "details": {},
            }
        }
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    # 记录错误日志
    logger.error(
        f"Error occurred while processing request",
        extra={
            "error_response": error_response,
            "status_code": status_code,
            "request_method": request.method,
            "request_url": str(request.url),
            "client_host": request.client.host if request.client else None,
        },
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