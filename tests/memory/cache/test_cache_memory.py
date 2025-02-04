"""缓存内存测试模块"""

import pytest
import asyncio
import gc
import os
import psutil
import random
import string
import time
from typing import Dict, Any, List
from memory_profiler import profile
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

@profile
async def test_local_cache_memory_growth(local_cache):
    """测试本地缓存内存增长"""
    process = psutil.Process(os.getpid())
    
    # 记录初始内存
    gc.collect()
    start_mem = process.memory_info().rss
    
    # 写入数据（多次）
    for i in range(5):
        data = generate_random_data(1000)
        await local_cache.multi_set(data)
        
        # 等待GC
        gc.collect()
        await asyncio.sleep(0.1)
        
        # 记录内存
        current_mem = process.memory_info().rss
        mem_growth = (current_mem - start_mem) / 1024 / 1024
        print(f"第{i+1}轮后内存增长: {mem_growth:.2f} MB")
        
        # 验证内存增长
        assert mem_growth < 50, f"第{i+1}轮后内存增长超出预期"

@profile
async def test_local_cache_memory_cleanup(local_cache):
    """测试本地缓存内存清理"""
    process = psutil.Process(os.getpid())
    
    # 记录初始内存
    gc.collect()
    start_mem = process.memory_info().rss
    
    # 写入数据
    data = generate_random_data(5000)
    await local_cache.multi_set(data)
    
    # 记录写入后内存
    gc.collect()
    mid_mem = process.memory_info().rss
    mid_growth = (mid_mem - start_mem) / 1024 / 1024
    print(f"写入后内存增长: {mid_growth:.2f} MB")
    
    # 清空缓存
    await local_cache.clear()
    
    # 等待GC
    gc.collect()
    await asyncio.sleep(0.1)
    
    # 记录清理后内存
    end_mem = process.memory_info().rss
    end_growth = (end_mem - start_mem) / 1024 / 1024
    print(f"清理后内存增长: {end_growth:.2f} MB")
    
    # 验证内存释放
    assert end_growth < mid_growth * 0.5, "缓存清理后内存未有效释放"

@profile
async def test_local_cache_memory_eviction(local_cache):
    """测试本地缓存内存淘汰"""
    process = psutil.Process(os.getpid())
    
    # 记录初始内存
    gc.collect()
    start_mem = process.memory_info().rss
    
    # 写入超过最大容量的数据
    data = generate_random_data(15000)  # max_size = 10000
    await local_cache.multi_set(data)
    
    # 等待淘汰
    await asyncio.sleep(1)
    gc.collect()
    
    # 记录最终内存
    end_mem = process.memory_info().rss
    mem_growth = (end_mem - start_mem) / 1024 / 1024
    print(f"淘汰后内存增长: {mem_growth:.2f} MB")
    
    # 验证内存控制
    assert mem_growth < 100, "缓存淘汰后内存仍然过高"
    
    # 验证缓存大小
    metrics = await local_cache.get_metrics()
    assert metrics["size"] <= 10000, "缓存大小超过最大限制"

@profile
async def test_local_cache_memory_ttl(local_cache):
    """测试本地缓存TTL内存释放"""
    process = psutil.Process(os.getpid())
    
    # 记录初始内存
    gc.collect()
    start_mem = process.memory_info().rss
    
    # 写入带TTL的数据
    data = generate_random_data(5000)
    for key, value in data.items():
        await local_cache.set(key, value, ttl=1)
    
    # 记录写入后内存
    gc.collect()
    mid_mem = process.memory_info().rss
    mid_growth = (mid_mem - start_mem) / 1024 / 1024
    print(f"写入后内存增长: {mid_growth:.2f} MB")
    
    # 等待过期
    await asyncio.sleep(1.1)
    gc.collect()
    
    # 记录过期后内存
    end_mem = process.memory_info().rss
    end_growth = (end_mem - start_mem) / 1024 / 1024
    print(f"过期后内存增长: {end_growth:.2f} MB")
    
    # 验证内存释放
    assert end_growth < mid_growth * 0.5, "TTL过期后内存未有效释放"

@profile
async def test_local_cache_memory_stress(local_cache):
    """测试本地缓存内存压力"""
    process = psutil.Process(os.getpid())
    
    # 记录初始内存
    gc.collect()
    start_mem = process.memory_info().rss
    
    # 持续写入和删除数据
    for i in range(10):
        # 写入数据
        data = generate_random_data(1000)
        await local_cache.multi_set(data)
        
        # 删除一半数据
        keys = list(data.keys())[:500]
        for key in keys:
            await local_cache.delete(key)
        
        # 等待GC
        gc.collect()
        await asyncio.sleep(0.1)
        
        # 记录内存
        current_mem = process.memory_info().rss
        mem_growth = (current_mem - start_mem) / 1024 / 1024
        print(f"第{i+1}轮后内存增长: {mem_growth:.2f} MB")
        
        # 验证内存增长
        assert mem_growth < 100, f"第{i+1}轮后内存增长超出预期"

@profile
async def test_local_cache_memory_concurrent(local_cache):
    """测试本地缓存并发内存使用"""
    process = psutil.Process(os.getpid())
    
    # 记录初始内存
    gc.collect()
    start_mem = process.memory_info().rss
    
    async def worker(worker_id: int):
        """工作协程"""
        for i in range(100):
            # 写入数据
            data = {
                f"worker{worker_id}_key{j}": generate_random_string()
                for j in range(100)
            }
            await local_cache.multi_set(data)
            
            # 读取数据
            await local_cache.multi_get(list(data.keys()))
            
            # 删除数据
            for key in data:
                await local_cache.delete(key)
    
    # 启动多个worker
    workers = [worker(i) for i in range(10)]
    await asyncio.gather(*workers)
    
    # 等待GC
    gc.collect()
    await asyncio.sleep(0.1)
    
    # 记录最终内存
    end_mem = process.memory_info().rss
    mem_growth = (end_mem - start_mem) / 1024 / 1024
    print(f"并发操作后内存增长: {mem_growth:.2f} MB")
    
    # 验证内存增长
    assert mem_growth < 100, "并发操作后内存增长超出预期"

@profile
async def test_local_cache_memory_large_values(local_cache):
    """测试本地缓存大值内存使用"""
    process = psutil.Process(os.getpid())
    
    # 记录初始内存
    gc.collect()
    start_mem = process.memory_info().rss
    
    # 生成大值数据
    data = {
        f"key{i}": generate_random_string(1024 * 10)  # 10KB
        for i in range(100)
    }
    
    # 写入数据
    await local_cache.multi_set(data)
    
    # 等待GC
    gc.collect()
    await asyncio.sleep(0.1)
    
    # 记录最终内存
    end_mem = process.memory_info().rss
    mem_growth = (end_mem - start_mem) / 1024 / 1024
    print(f"大值数据后内存增长: {mem_growth:.2f} MB")
    
    # 验证内存增长
    assert mem_growth < 100, "大值数据后内存增长超出预期"
    
    # 验证缓存大小
    metrics = await local_cache.get_metrics()
    print(f"缓存条目数: {metrics['size']}")
    print(f"缓存命中率: {metrics['hit_rate']:.2%}")
    print(f"缓存淘汰数: {metrics['evictions']}")

@profile
async def test_local_cache_memory_leak(local_cache):
    """测试本地缓存内存泄漏"""
    process = psutil.Process(os.getpid())
    memory_samples = []
    
    # 记录初始内存
    gc.collect()
    start_mem = process.memory_info().rss
    memory_samples.append(start_mem)
    
    # 多轮操作
    for i in range(10):
        # 写入数据
        data = generate_random_data(1000)
        await local_cache.multi_set(data)
        
        # 读取数据
        await local_cache.multi_get(list(data.keys()))
        
        # 删除数据
        await local_cache.clear()
        
        # 等待GC
        gc.collect()
        await asyncio.sleep(0.1)
        
        # 记录内存
        current_mem = process.memory_info().rss
        memory_samples.append(current_mem)
        
        # 计算增长
        mem_growth = (current_mem - start_mem) / 1024 / 1024
        print(f"第{i+1}轮后内存增长: {mem_growth:.2f} MB")
    
    # 计算内存增长趋势
    growth_trend = [
        (memory_samples[i] - memory_samples[i-1]) / 1024 / 1024
        for i in range(1, len(memory_samples))
    ]
    
    # 验证是否存在持续增长
    trend_sum = sum(growth_trend)
    print(f"内存增长趋势: {trend_sum:.2f} MB")
    assert trend_sum < 10, "检测到可能的内存泄漏" 