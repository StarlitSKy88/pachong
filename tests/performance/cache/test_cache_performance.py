"""缓存性能测试模块"""

import pytest
import asyncio
import time
import random
import string
from typing import Dict, Any, List
from src.cache.local_cache import LRUCache
from src.cache.redis_cache import RedisCache
from redis.asyncio import Redis

pytestmark = pytest.mark.asyncio

def generate_random_string(length: int = 10) -> str:
    """生成随机字符串"""
    return ''.join(random.choices(
        string.ascii_letters + string.digits,
        k=length
    ))

def generate_random_data(count: int = 1000) -> Dict[str, str]:
    """生成随机数据"""
    return {
        f"key{i}": generate_random_string()
        for i in range(count)
    }

@pytest.fixture
async def redis_client():
    """Redis客户端"""
    client = Redis(
        host="localhost",
        port=6379,
        db=0,
        decode_responses=True
    )
    yield client
    await client.close()

@pytest.fixture
async def local_cache():
    """本地缓存"""
    cache = LRUCache(
        name="local",
        max_size=10000,
        cleanup_interval=60
    )
    await cache.start()
    yield cache
    await cache.stop()

@pytest.fixture
async def redis_cache(redis_client):
    """Redis缓存"""
    cache = RedisCache(
        name="redis",
        redis=redis_client,
        prefix="perf:",
        default_ttl=60
    )
    yield cache
    await cache.clear()

async def benchmark_set(cache, data: Dict[str, str]) -> float:
    """测试设置性能"""
    start_time = time.time()
    for key, value in data.items():
        await cache.set(key, value)
    end_time = time.time()
    return end_time - start_time

async def benchmark_get(cache, keys: List[str]) -> float:
    """测试获取性能"""
    start_time = time.time()
    for key in keys:
        await cache.get(key)
    end_time = time.time()
    return end_time - start_time

async def benchmark_multi_set(cache, data: Dict[str, str]) -> float:
    """测试批量设置性能"""
    start_time = time.time()
    await cache.multi_set(data)
    end_time = time.time()
    return end_time - start_time

async def benchmark_multi_get(cache, keys: List[str]) -> float:
    """测试批量获取性能"""
    start_time = time.time()
    await cache.multi_get(keys)
    end_time = time.time()
    return end_time - start_time

@pytest.mark.benchmark
@pytest.mark.timeout(30)
async def test_local_cache_performance(local_cache):
    """测试本地缓存性能"""
    # 准备数据
    data = generate_random_data(1000)
    keys = list(data.keys())
    
    # 测试单个操作
    set_time = await benchmark_set(local_cache, data)
    get_time = await benchmark_get(local_cache, keys)
    
    # 测试批量操作
    multi_set_time = await benchmark_multi_set(local_cache, data)
    multi_get_time = await benchmark_multi_get(local_cache, keys)
    
    # 计算性能指标
    set_ops = len(data) / set_time
    get_ops = len(keys) / get_time
    multi_set_ops = len(data) / multi_set_time
    multi_get_ops = len(keys) / multi_get_time
    
    # 输出结果
    print(f"\n本地缓存性能测试结果:")
    print(f"单个设置: {set_ops:.2f} ops/s")
    print(f"单个获取: {get_ops:.2f} ops/s")
    print(f"批量设置: {multi_set_ops:.2f} ops/s")
    print(f"批量获取: {multi_get_ops:.2f} ops/s")
    
    # 验证性能要求
    assert set_ops > 1000, "单个设置性能不达标"
    assert get_ops > 1000, "单个获取性能不达标"
    assert multi_set_ops > 5000, "批量设置性能不达标"
    assert multi_get_ops > 5000, "批量获取性能不达标"

@pytest.mark.benchmark
@pytest.mark.timeout(30)
async def test_redis_cache_performance(redis_cache):
    """测试Redis缓存性能"""
    # 准备数据
    data = generate_random_data(1000)
    keys = list(data.keys())
    
    # 测试单个操作
    set_time = await benchmark_set(redis_cache, data)
    get_time = await benchmark_get(redis_cache, keys)
    
    # 测试批量操作
    multi_set_time = await benchmark_multi_set(redis_cache, data)
    multi_get_time = await benchmark_multi_get(redis_cache, keys)
    
    # 计算性能指标
    set_ops = len(data) / set_time
    get_ops = len(keys) / get_time
    multi_set_ops = len(data) / multi_set_time
    multi_get_ops = len(keys) / multi_get_time
    
    # 输出结果
    print(f"\nRedis缓存性能测试结果:")
    print(f"单个设置: {set_ops:.2f} ops/s")
    print(f"单个获取: {get_ops:.2f} ops/s")
    print(f"批量设置: {multi_set_ops:.2f} ops/s")
    print(f"批量获取: {multi_get_ops:.2f} ops/s")
    
    # 验证性能要求
    assert set_ops > 500, "单个设置性能不达标"
    assert get_ops > 500, "单个获取性能不达标"
    assert multi_set_ops > 2000, "批量设置性能不达标"
    assert multi_get_ops > 2000, "批量获取性能不达标"

@pytest.mark.benchmark
@pytest.mark.timeout(60)
async def test_cache_concurrent_performance(local_cache, redis_cache):
    """测试并发性能"""
    # 准备数据
    data = generate_random_data(100)
    keys = list(data.keys())
    
    async def worker(cache, worker_id: int):
        """工作协程"""
        for i in range(100):
            key = f"worker{worker_id}_key{i}"
            value = generate_random_string()
            
            # 写入
            await cache.set(key, value)
            
            # 读取
            cached = await cache.get(key)
            assert cached == value
            
            # 删除
            await cache.delete(key)
    
    # 测试本地缓存并发性能
    start_time = time.time()
    workers = [
        worker(local_cache, i)
        for i in range(10)
    ]
    await asyncio.gather(*workers)
    local_time = time.time() - start_time
    
    # 测试Redis缓存并发性能
    start_time = time.time()
    workers = [
        worker(redis_cache, i)
        for i in range(10)
    ]
    await asyncio.gather(*workers)
    redis_time = time.time() - start_time
    
    # 计算性能指标
    local_ops = 1000 / local_time  # 10个worker * 100次操作
    redis_ops = 1000 / redis_time
    
    # 输出结果
    print(f"\n并发性能测试结果:")
    print(f"本地缓存: {local_ops:.2f} ops/s")
    print(f"Redis缓存: {redis_ops:.2f} ops/s")
    
    # 验证性能要求
    assert local_ops > 1000, "本地缓存并发性能不达标"
    assert redis_ops > 500, "Redis缓存并发性能不达标"

@pytest.mark.benchmark
@pytest.mark.timeout(30)
async def test_cache_memory_usage(local_cache):
    """测试内存使用"""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    
    # 记录初始内存
    start_mem = process.memory_info().rss
    
    # 写入大量数据
    data = generate_random_data(10000)
    await local_cache.multi_set(data)
    
    # 记录最终内存
    end_mem = process.memory_info().rss
    
    # 计算内存增长
    mem_growth = (end_mem - start_mem) / 1024 / 1024  # MB
    
    # 输出结果
    print(f"\n内存使用测试结果:")
    print(f"初始内存: {start_mem/1024/1024:.2f} MB")
    print(f"最终内存: {end_mem/1024/1024:.2f} MB")
    print(f"内存增长: {mem_growth:.2f} MB")
    
    # 验证内存要求
    assert mem_growth < 100, "内存增长超出预期"

@pytest.mark.benchmark
@pytest.mark.timeout(30)
async def test_cache_ttl_performance(local_cache, redis_cache):
    """测试TTL性能"""
    # 准备数据
    data = {
        key: value
        for key, value in generate_random_data(1000).items()
    }
    
    async def benchmark_ttl_set(cache):
        """测试TTL设置性能"""
        start_time = time.time()
        for key, value in data.items():
            ttl = random.randint(1, 60)
            await cache.set(key, value, ttl=ttl)
        return time.time() - start_time
    
    # 测试本地缓存
    local_time = await benchmark_ttl_set(local_cache)
    local_ops = len(data) / local_time
    
    # 测试Redis缓存
    redis_time = await benchmark_ttl_set(redis_cache)
    redis_ops = len(data) / redis_time
    
    # 输出结果
    print(f"\nTTL性能测试结果:")
    print(f"本地缓存: {local_ops:.2f} ops/s")
    print(f"Redis缓存: {redis_ops:.2f} ops/s")
    
    # 验证性能要求
    assert local_ops > 500, "本地缓存TTL性能不达标"
    assert redis_ops > 200, "Redis缓存TTL性能不达标" 