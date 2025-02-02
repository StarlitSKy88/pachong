import pytest
import asyncio
import time
from src.utils.rate_limiter import TokenBucket, RateLimiter

def test_token_bucket():
    """测试令牌桶"""
    # 创建令牌桶：容量5，每秒2个令牌
    bucket = TokenBucket(capacity=5, fill_rate=2)
    
    # 初始状态应该是满的
    assert bucket.tokens == 5
    
    # 消费3个令牌
    assert bucket.consume(3) == True
    assert bucket.tokens == 2
    
    # 尝试消费3个令牌（应该失败）
    assert bucket.consume(3) == False
    assert bucket.tokens == 2
    
    # 等待1秒，应该新增2个令牌
    time.sleep(1)
    bucket._fill_tokens()
    assert abs(bucket.tokens - 4) < 0.1  # 允许小误差
    
    # 消费1个令牌
    assert bucket.consume(1) == True
    assert abs(bucket.tokens - 3) < 0.1

@pytest.mark.asyncio
async def test_rate_limiter():
    """测试频率限制器"""
    limiter = RateLimiter()
    
    # 测试小红书限流
    platform = 'xhs'
    
    # 第一次请求应该成功
    assert await limiter.acquire(platform) == True
    
    # 快速发起5个请求，应该有一些失败
    results = []
    for _ in range(5):
        results.append(await limiter.acquire(platform))
    
    # 应该有请求被限流
    assert False in results
    
    # 等待令牌恢复
    await asyncio.sleep(3)
    
    # 现在应该可以请求了
    assert await limiter.acquire(platform) == True
    
    # 测试不同平台独立限流
    assert await limiter.acquire('bilibili') == True
    
    # 测试获取等待时间
    wait_time = limiter.get_wait_time(platform, tokens=2)
    assert wait_time >= 0
    
    # 测试获取剩余令牌
    remaining = limiter.get_remaining_tokens(platform)
    assert remaining >= 0

@pytest.mark.asyncio
async def test_rate_limiter_jitter():
    """测试随机延迟"""
    limiter = RateLimiter()
    platform = 'xhs'
    
    # 记录请求时间
    start_time = time.time()
    await limiter.acquire(platform)
    first_request = time.time() - start_time
    
    # 立即发起第二个请求
    start_time = time.time()
    await limiter.acquire(platform)
    second_request = time.time() - start_time
    
    # 第二个请求应该有延迟
    assert second_request > first_request
    
    # 延迟应该在合理范围内
    min_interval = 1.0 / limiter.buckets[platform].fill_rate
    assert second_request >= min_interval * 0.9  # 允许10%误差

if __name__ == '__main__':
    pytest.main(['-v', 'test_rate_limiter.py']) 