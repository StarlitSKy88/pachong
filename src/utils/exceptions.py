from typing import Optional, Dict, Any

class CrawlerException(Exception):
    """爬虫异常基类"""
    
    def __init__(
        self,
        message: str,
        code: str = "UNKNOWN",
        details: Optional[Dict[str, Any]] = None
    ):
        """初始化异常
        
        Args:
            message: 错误信息
            code: 错误代码
            details: 详细信息
        """
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)
        
    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            Dict[str, Any]: 异常信息字典
        """
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details
        }

class RequestError(CrawlerException):
    """请求错误"""
    
    def __init__(
        self,
        message: str,
        url: str,
        status: Optional[int] = None,
        response: Optional[str] = None,
        **kwargs
    ):
        """初始化请求错误
        
        Args:
            message: 错误信息
            url: 请求URL
            status: HTTP状态码
            response: 响应内容
        """
        details = {
            "url": url,
            "status": status,
            "response": response,
            **kwargs
        }
        super().__init__(message, "REQUEST_ERROR", details)

class ProxyError(CrawlerException):
    """代理错误"""
    
    def __init__(
        self,
        message: str,
        proxy: Optional[str] = None,
        **kwargs
    ):
        """初始化代理错误
        
        Args:
            message: 错误信息
            proxy: 代理地址
        """
        details = {
            "proxy": proxy,
            **kwargs
        }
        super().__init__(message, "PROXY_ERROR", details)

class CookieError(CrawlerException):
    """Cookie错误"""
    
    def __init__(
        self,
        message: str,
        platform: str,
        cookie_id: Optional[str] = None,
        **kwargs
    ):
        """初始化Cookie错误
        
        Args:
            message: 错误信息
            platform: 平台名称
            cookie_id: CookieID
        """
        details = {
            "platform": platform,
            "cookie_id": cookie_id,
            **kwargs
        }
        super().__init__(message, "COOKIE_ERROR", details)

class ParseError(CrawlerException):
    """解析错误"""
    
    def __init__(
        self,
        message: str,
        content: Optional[str] = None,
        **kwargs
    ):
        """初始化解析错误
        
        Args:
            message: 错误信息
            content: 待解析内容
        """
        details = {
            "content": content[:1000] if content else None,  # 只保留前1000个字符
            **kwargs
        }
        super().__init__(message, "PARSE_ERROR", details)

class DatabaseError(CrawlerException):
    """数据库错误"""
    
    def __init__(
        self,
        message: str,
        operation: str,
        collection: Optional[str] = None,
        **kwargs
    ):
        """初始化数据库错误
        
        Args:
            message: 错误信息
            operation: 操作类型
            collection: 集合名称
        """
        details = {
            "operation": operation,
            "collection": collection,
            **kwargs
        }
        super().__init__(message, "DATABASE_ERROR", details)

class ConfigError(CrawlerException):
    """配置错误"""
    
    def __init__(
        self,
        message: str,
        config_key: str,
        **kwargs
    ):
        """初始化配置错误
        
        Args:
            message: 错误信息
            config_key: 配置键名
        """
        details = {
            "config_key": config_key,
            **kwargs
        }
        super().__init__(message, "CONFIG_ERROR", details)

class MonitorError(CrawlerException):
    """监控错误"""
    
    def __init__(
        self,
        message: str,
        monitor: str,
        operation: Optional[str] = None,
        **kwargs
    ):
        """初始化监控错误
        
        Args:
            message: 错误信息
            monitor: 监控器名称
            operation: 操作类型
        """
        details = {
            "monitor": monitor,
            "operation": operation,
            **kwargs
        }
        super().__init__(message, "MONITOR_ERROR", details) 