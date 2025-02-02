"""错误处理模块测试"""
import pytest
import asyncio
from datetime import datetime, timedelta
from src.utils.error_handler import ErrorHandler, handle_error
from src.utils.exceptions import CrawlerException

class TestException(CrawlerException):
    """测试用异常类"""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            code="TEST_ERROR",
            message=message,
            **kwargs
        )

@pytest.fixture
def error_handler():
    """错误处理器fixture"""
    return ErrorHandler()

def test_error_handler_initialization(error_handler):
    """测试错误处理器初始化"""
    assert error_handler.errors == []
    assert error_handler.max_errors == 1000

def test_add_error(error_handler):
    """测试添加错误记录"""
    error = TestException("测试错误")
    context = {"test": "context"}
    
    error_handler.add_error(error, context)
    
    assert len(error_handler.errors) == 1
    error_record = error_handler.errors[0]
    assert error_record["code"] == "TEST_ERROR"
    assert error_record["message"] == "测试错误"
    assert error_record["context"] == context
    assert "timestamp" in error_record

def test_max_errors_limit(error_handler):
    """测试最大错误记录限制"""
    for i in range(1100):
        error = TestException(f"错误 {i}")
        error_handler.add_error(error)
    
    assert len(error_handler.errors) == 1000
    assert error_handler.errors[-1]["message"] == "错误 1099"

def test_get_errors_filtering(error_handler):
    """测试错误记录过滤"""
    # 添加不同类型的错误
    error1 = TestException("错误1")
    error2 = TestException("错误2")
    
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    
    error_handler.add_error(error1)
    error_handler.add_error(error2)
    
    # 测试类型过滤
    errors = error_handler.get_errors(error_type="TEST_ERROR")
    assert len(errors) == 2
    
    # 测试时间过滤
    errors = error_handler.get_errors(start_time=yesterday)
    assert len(errors) == 2
    
    errors = error_handler.get_errors(end_time=now + timedelta(hours=1))
    assert len(errors) == 2
    
    # 测试限制数量
    errors = error_handler.get_errors(limit=1)
    assert len(errors) == 1

def test_clear_errors(error_handler):
    """测试清空错误记录"""
    error = TestException("测试错误")
    error_handler.add_error(error)
    
    error_handler.clear_errors()
    assert len(error_handler.errors) == 0

def test_error_stats(error_handler):
    """测试错误统计"""
    error1 = TestException("错误1")
    error2 = TestException("错误2")
    
    error_handler.add_error(error1)
    error_handler.add_error(error2)
    
    stats = error_handler.get_error_stats()
    
    assert stats["total"] == 2
    assert stats["by_type"]["TEST_ERROR"] == 2
    assert len(stats["by_hour"]) > 0

@pytest.mark.asyncio
async def test_handle_error_decorator_async():
    """测试异步错误处理装饰器"""
    @handle_error(TestException)
    async def async_func():
        raise ValueError("测试错误")
    
    with pytest.raises(TestException) as exc_info:
        await async_func()
    
    assert str(exc_info.value) == "[TEST_ERROR] 测试错误"
    assert exc_info.value.details["error_type"] == "ValueError"
    assert "traceback" in exc_info.value.details
    assert "timestamp" in exc_info.value.details

def test_handle_error_decorator_sync():
    """测试同步错误处理装饰器"""
    @handle_error(TestException)
    def sync_func():
        raise ValueError("测试错误")
    
    with pytest.raises(TestException) as exc_info:
        sync_func()
    
    assert str(exc_info.value) == "[TEST_ERROR] 测试错误"
    assert exc_info.value.details["error_type"] == "ValueError"
    assert "traceback" in exc_info.value.details
    assert "timestamp" in exc_info.value.details

def test_handle_error_no_reraise():
    """测试不重新抛出异常的情况"""
    @handle_error(TestException, reraise=False)
    def func():
        raise ValueError("测试错误")
    
    result = func()
    assert result is None

def test_handle_error_with_context():
    """测试带上下文的错误处理"""
    @handle_error(TestException, context={"test": "value"})
    def func():
        raise ValueError("测试错误")
    
    with pytest.raises(TestException) as exc_info:
        func()
    
    assert exc_info.value.details["context"]["test"] == "value"
    assert exc_info.value.details["error_type"] == "ValueError"
    assert "traceback" in exc_info.value.details
    assert "timestamp" in exc_info.value.details 