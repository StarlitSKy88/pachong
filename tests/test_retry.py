import pytest
import asyncio
from unittest.mock import Mock, patch
from datetime import datetime
from src.utils.retry import (
    retry,
    RetryPolicy,
    RetryError,
    exponential_backoff,
    DEFAULT_RETRY_POLICY,
    AGGRESSIVE_RETRY_POLICY,
    CONSERVATIVE_RETRY_POLICY
)

def test_exponential_backoff():
    """测试指数退避算法"""
    # 测试基本延迟计算
    assert 1.0 <= exponential_backoff(1, jitter=False) <= 1.0
    assert 2.0 <= exponential_backoff(2, jitter=False) <= 2.0
    assert 4.0 <= exponential_backoff(3, jitter=False) <= 4.0
    
    # 测试最大延迟限制
    assert exponential_backoff(10, max_delay=30.0, jitter=False) == 30.0
    
    # 测试随机抖动
    delays = [exponential_backoff(1) for _ in range(100)]
    assert not all(d == delays[0] for d in delays)  # 验证有随机性
    assert all(0.5 <= d <= 1.5 for d in delays)  # 验证在合理范围内

def test_retry_policy():
    """测试重试策略"""
    policy = RetryPolicy(
        max_attempts=3,
        retry_exceptions=(ValueError,)
    )
    
    # 测试异常重试判断
    assert policy.should_retry(1, error=ValueError())
    assert not policy.should_retry(1, error=TypeError())
    assert not policy.should_retry(3, error=ValueError())
    
    # 测试结果重试判断
    policy = RetryPolicy(
        max_attempts=3,
        retry_on_result=lambda x: x is None
    )
    assert policy.should_retry(1, result=None)
    assert not policy.should_retry(1, result="success")

@pytest.mark.asyncio
async def test_async_retry_on_exception():
    """测试异步函数异常重试"""
    mock_func = Mock(side_effect=[ValueError, ValueError, "success"])
    
    @retry(max_attempts=3)
    async def test_func():
        return mock_func()
    
    result = await test_func()
    assert result == "success"
    assert mock_func.call_count == 3

@pytest.mark.asyncio
async def test_async_retry_on_result():
    """测试异步函数结果重试"""
    mock_func = Mock(side_effect=[None, None, "success"])
    
    @retry(max_attempts=3, retry_on_result=lambda x: x is None)
    async def test_func():
        return mock_func()
    
    result = await test_func()
    assert result == "success"
    assert mock_func.call_count == 3

def test_sync_retry_on_exception():
    """测试同步函数异常重试"""
    mock_func = Mock(side_effect=[ValueError, ValueError, "success"])
    
    @retry(max_attempts=3)
    def test_func():
        return mock_func()
    
    result = test_func()
    assert result == "success"
    assert mock_func.call_count == 3

def test_sync_retry_on_result():
    """测试同步函数结果重试"""
    mock_func = Mock(side_effect=[None, None, "success"])
    
    @retry(max_attempts=3, retry_on_result=lambda x: x is None)
    def test_func():
        return mock_func()
    
    result = test_func()
    assert result == "success"
    assert mock_func.call_count == 3

@pytest.mark.asyncio
async def test_retry_error():
    """测试重试失败异常"""
    @retry(max_attempts=2)
    async def test_func():
        raise ValueError("test error")
    
    with pytest.raises(RetryError) as exc_info:
        await test_func()
    
    assert "Failed after 2 attempts" in str(exc_info.value)
    assert isinstance(exc_info.value.last_error, ValueError)

def test_retry_callback():
    """测试重试回调函数"""
    callback_mock = Mock()
    
    @retry(
        max_attempts=3,
        on_retry=callback_mock
    )
    def test_func():
        raise ValueError("test error")
    
    with pytest.raises(RetryError):
        test_func()
    
    assert callback_mock.call_count == 2  # 两次重试
    # 验证回调参数
    for args in callback_mock.call_args_list:
        attempt, error, delay = args[0]
        assert isinstance(attempt, int)
        assert isinstance(error, ValueError)
        assert isinstance(delay, float)

@pytest.mark.asyncio
async def test_predefined_policies():
    """测试预定义的重试策略"""
    # 测试默认策略
    @retry(policy=DEFAULT_RETRY_POLICY)
    async def test_default():
        raise ValueError()
    
    with pytest.raises(RetryError):
        await test_default()
    
    # 测试激进策略
    mock_func = Mock(side_effect=[ValueError] * 4 + ["success"])
    @retry(policy=AGGRESSIVE_RETRY_POLICY)
    async def test_aggressive():
        return mock_func()
    
    result = await test_aggressive()
    assert result == "success"
    assert mock_func.call_count == 5
    
    # 测试保守策略
    @retry(policy=CONSERVATIVE_RETRY_POLICY)
    async def test_conservative():
        raise ValueError()
    
    with pytest.raises(RetryError):
        await test_conservative()

@pytest.mark.asyncio
async def test_custom_policy():
    """测试自定义重试策略"""
    custom_policy = RetryPolicy(
        max_attempts=2,
        base_delay=0.1,
        max_delay=0.2,
        jitter=False,
        retry_exceptions=(ValueError,),
        retry_on_result=lambda x: x < 0
    )
    
    @retry(policy=custom_policy)
    async def test_func(return_value):
        return return_value
    
    # 测试结果重试
    result = await test_func(-1)  # 应该重试一次后失败
    assert result == -1
    
    # 测试异常重试
    with pytest.raises(TypeError):  # 不在重试异常列表中
        await test_func(1/0)
    
    # 测试成功情况
    result = await test_func(1)
    assert result == 1 