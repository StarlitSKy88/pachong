import pytest
from datetime import datetime, timedelta
from src.utils.exceptions import (
    CrawlerException,
    RequestError,
    ProxyError,
    CookieError
)
from src.utils.error_handler import (
    handle_error,
    ErrorHandler,
    _get_error_info,
    _log_error
)

@pytest.fixture
def error_handler():
    """创建错误处理器实例"""
    return ErrorHandler()

def test_crawler_exception():
    """测试爬虫异常基类"""
    error = CrawlerException(
        message="测试错误",
        code="TEST_ERROR",
        details={"key": "value"}
    )
    
    assert str(error) == "[TEST_ERROR] 测试错误"
    assert error.to_dict() == {
        "code": "TEST_ERROR",
        "message": "测试错误",
        "details": {"key": "value"}
    }

def test_request_error():
    """测试请求错误"""
    error = RequestError(
        message="请求失败",
        url="http://example.com",
        status=404,
        response="Not Found"
    )
    
    assert error.code == "REQUEST_ERROR"
    assert "请求失败" in str(error)
    assert error.details["url"] == "http://example.com"
    assert error.details["status"] == 404
    assert error.details["response"] == "Not Found"

def test_proxy_error():
    """测试代理错误"""
    error = ProxyError(
        message="代理不可用",
        proxy="http://proxy.example.com:8080"
    )
    
    assert error.code == "PROXY_ERROR"
    assert "代理不可用" in str(error)
    assert error.details["proxy"] == "http://proxy.example.com:8080"

def test_cookie_error():
    """测试Cookie错误"""
    error = CookieError(
        message="Cookie无效",
        platform="test_platform",
        cookie_id="123"
    )
    
    assert error.code == "COOKIE_ERROR"
    assert "Cookie无效" in str(error)
    assert error.details["platform"] == "test_platform"
    assert error.details["cookie_id"] == "123"

@pytest.mark.asyncio
async def test_handle_error_decorator():
    """测试错误处理装饰器"""
    
    @handle_error(RequestError, url="http://test.com")
    async def test_func():
        raise ValueError("测试错误")
        
    with pytest.raises(RequestError) as exc_info:
        await test_func()
        
    error = exc_info.value
    assert error.code == "REQUEST_ERROR"
    assert "测试错误" in str(error)
    assert error.details["url"] == "http://test.com"
    assert "traceback" in error.details

def test_error_handler_add_error(error_handler):
    """测试添加错误记录"""
    error = CrawlerException("测试错误")
    context = {"test": "value"}
    
    error_handler.add_error(error, context)
    
    assert len(error_handler.errors) == 1
    assert error_handler.errors[0]["message"] == "测试错误"
    assert error_handler.errors[0]["context"] == context

def test_error_handler_max_errors(error_handler):
    """测试错误记录数量限制"""
    # 添加超过限制的错误记录
    for i in range(error_handler.max_errors + 10):
        error = CrawlerException(f"错误 {i}")
        error_handler.add_error(error)
        
    assert len(error_handler.errors) == error_handler.max_errors
    assert error_handler.errors[-1]["message"] == f"错误 {error_handler.max_errors + 9}"

def test_error_handler_get_errors(error_handler):
    """测试获取错误记录"""
    # 添加不同类型的错误
    error_handler.add_error(RequestError("请求错误", url="http://test.com"))
    error_handler.add_error(ProxyError("代理错误", proxy="http://proxy.com"))
    error_handler.add_error(CookieError("Cookie错误", platform="test"))
    
    # 测试按类型过滤
    request_errors = error_handler.get_errors(error_type="REQUEST_ERROR")
    assert len(request_errors) == 1
    assert request_errors[0]["code"] == "REQUEST_ERROR"
    
    # 测试按时间范围过滤
    now = datetime.now()
    recent_errors = error_handler.get_errors(
        start_time=now - timedelta(minutes=1)
    )
    assert len(recent_errors) == 3

def test_error_handler_clear_errors(error_handler):
    """测试清空错误记录"""
    error_handler.add_error(CrawlerException("测试错误"))
    assert len(error_handler.errors) == 1
    
    error_handler.clear_errors()
    assert len(error_handler.errors) == 0

def test_error_handler_get_error_stats(error_handler):
    """测试获取错误统计信息"""
    # 添加不同类型的错误
    error_handler.add_error(RequestError("请求错误1", url="http://test1.com"))
    error_handler.add_error(RequestError("请求错误2", url="http://test2.com"))
    error_handler.add_error(ProxyError("代理错误", proxy="http://proxy.com"))
    
    stats = error_handler.get_error_stats()
    
    assert stats["total"] == 3
    assert stats["by_type"]["REQUEST_ERROR"] == 2
    assert stats["by_type"]["PROXY_ERROR"] == 1
    assert len(stats["by_hour"]) > 0  # 应该有当前小时的统计

def test_get_error_info():
    """测试获取错误信息"""
    try:
        raise ValueError("测试错误")
    except Exception as e:
        error_info = _get_error_info(e)
        
    assert error_info["error_type"] == "ValueError"
    assert "traceback" in error_info
    assert "timestamp" in error_info

def test_log_error(caplog):
    """测试记录错误日志"""
    error = CrawlerException(
        message="测试错误",
        code="TEST_ERROR",
        details={"traceback": "测试跟踪信息"}
    )
    
    _log_error(error)
    
    assert "测试错误" in caplog.text
    assert "TEST_ERROR" in caplog.text
    assert "测试跟踪信息" in caplog.text 