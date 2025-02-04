import asyncio
import aiohttp
from src.cache.local_cache import LRUCache

async def fetch_page(url: str, cache: LRUCache) -> str:
    """获取页面内容，优先从缓存获取"""
    # 尝试从缓存获取
    content = await cache.get(url)
    if content is not None:
        print(f"从缓存获取: {url}")
        return content
        
    # 从网络获取
    print(f"从网络获取: {url}")
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            content = await response.text()
            # 存入缓存，设置60秒过期
            await cache.set(url, content, ttl=60.0)
            return content

async def main():
    # 创建缓存实例
    cache = LRUCache("github_cache", max_size=100)
    await cache.start()
    
    try:
        # 测试URL
        url = "https://github.com/microsoft/TypeScript"
        
        # 第一次获取（从网络）
        content1 = await fetch_page(url, cache)
        print(f"第一次获取内容长度: {len(content1)}")
        
        # 查看缓存指标
        metrics = await cache.get_metrics()
        print("\n缓存指标:")
        for key, value in metrics.items():
            print(f"{key}: {value}")
            
        # 第二次获取（从缓存）
        content2 = await fetch_page(url, cache)
        print(f"\n第二次获取内容长度: {len(content2)}")
        
        # 再次查看缓存指标
        metrics = await cache.get_metrics()
        print("\n缓存指标:")
        for key, value in metrics.items():
            print(f"{key}: {value}")
            
        # 验证内容一致性
        print(f"\n两次获取内容是否一致: {content1 == content2}")
        
        # 查看TTL
        ttl = await cache.ttl(url)
        print(f"缓存TTL: {ttl}秒")
        
    finally:
        await cache.stop()

if __name__ == "__main__":
    asyncio.run(main()) 