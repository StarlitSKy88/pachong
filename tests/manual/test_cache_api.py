import asyncio
import aiohttp
import json
from src.cache.local_cache import LRUCache

async def fetch_api(url: str, cache: LRUCache) -> dict:
    """获取API响应，优先从缓存获取"""
    # 尝试从缓存获取
    cached_data = await cache.get(url)
    if cached_data is not None:
        print(f"从缓存获取: {url}")
        return cached_data
        
    # 从API获取
    print(f"从API获取: {url}")
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            # 存入缓存，设置30秒过期
            await cache.set(url, data, ttl=30.0)
            return data

async def main():
    # 创建缓存实例
    cache = LRUCache("api_cache", max_size=100)
    await cache.start()
    
    try:
        # 基础URL
        base_url = "https://jsonplaceholder.typicode.com"
        
        # 测试不同的API端点
        endpoints = [
            "/posts/1",      # 单个文章
            "/posts/1/comments",  # 文章评论
            "/users/1",      # 用户信息
            "/todos/1"       # 待办事项
        ]
        
        print("第一轮：从API获取数据")
        print("-" * 50)
        
        # 第一轮：从API获取
        for endpoint in endpoints:
            url = base_url + endpoint
            data = await fetch_api(url, cache)
            print(f"端点: {endpoint}")
            print(f"数据: {json.dumps(data, indent=2)}\n")
            
        # 查看缓存指标
        metrics = await cache.get_metrics()
        print("\n缓存指标:")
        for key, value in metrics.items():
            print(f"{key}: {value}")
            
        print("\n第二轮：从缓存获取数据")
        print("-" * 50)
        
        # 第二轮：从缓存获取
        for endpoint in endpoints:
            url = base_url + endpoint
            data = await fetch_api(url, cache)
            print(f"端点: {endpoint}")
            print(f"数据: {json.dumps(data, indent=2)}\n")
            
        # 再次查看缓存指标
        metrics = await cache.get_metrics()
        print("\n缓存指标:")
        for key, value in metrics.items():
            print(f"{key}: {value}")
            
        # 查看所有URL的TTL
        print("\n各端点的缓存TTL:")
        for endpoint in endpoints:
            url = base_url + endpoint
            ttl = await cache.ttl(url)
            print(f"{endpoint}: {ttl:.2f}秒")
            
    finally:
        await cache.stop()

if __name__ == "__main__":
    asyncio.run(main()) 