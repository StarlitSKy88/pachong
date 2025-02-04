import asyncio
import aiohttp
import json
from datetime import datetime
from src.cache.local_cache import LRUCache

class CachedCrawler:
    """带缓存的爬虫"""
    
    def __init__(self, name: str, cache_size: int = 1000, cache_ttl: float = 300):
        """初始化爬虫
        
        Args:
            name: 爬虫名称
            cache_size: 缓存大小
            cache_ttl: 缓存过期时间（秒）
        """
        self.name = name
        self.cache_size = cache_size
        self.cache_ttl = cache_ttl
        self.cache = LRUCache(f"{name}_cache", max_size=cache_size)
        self.session = None
        
    async def start(self):
        """启动爬虫"""
        await self.cache.start()
        self.session = aiohttp.ClientSession()
        print(f"爬虫 {self.name} 已启动")
        
    async def stop(self):
        """停止爬虫"""
        await self.cache.stop()
        if self.session:
            await self.session.close()
        print(f"爬虫 {self.name} 已停止")
        
    async def fetch(self, url: str) -> dict:
        """获取数据，优先从缓存获取
        
        Args:
            url: 请求URL
            
        Returns:
            响应数据
        """
        # 尝试从缓存获取
        cached_data = await self.cache.get(url)
        if cached_data is not None:
            print(f"[缓存] {url}")
            return cached_data
            
        # 从网络获取
        print(f"[网络] {url}")
        async with self.session.get(url) as response:
            data = await response.json()
            # 存入缓存
            await self.cache.set(url, data, ttl=self.cache_ttl)
            return data
            
    async def get_stats(self) -> dict:
        """获取爬虫统计信息"""
        cache_metrics = await self.cache.get_metrics()
        return {
            "name": self.name,
            "cache_size": self.cache_size,
            "cache_ttl": self.cache_ttl,
            "cache_metrics": cache_metrics,
            "timestamp": datetime.now().isoformat()
        }

async def main():
    # 创建爬虫实例
    crawler = CachedCrawler("demo", cache_size=100, cache_ttl=60)
    await crawler.start()
    
    try:
        # 基础URL
        base_url = "https://jsonplaceholder.typicode.com"
        
        # 模拟爬取用户数据
        print("\n1. 爬取用户数据")
        print("-" * 50)
        for user_id in range(1, 4):
            url = f"{base_url}/users/{user_id}"
            user = await crawler.fetch(url)
            print(f"用户 {user_id}: {user['name']} ({user['email']})")
            
        # 模拟爬取文章数据
        print("\n2. 爬取文章数据")
        print("-" * 50)
        for post_id in range(1, 4):
            url = f"{base_url}/posts/{post_id}"
            post = await crawler.fetch(url)
            print(f"文章 {post_id}: {post['title'][:50]}...")
            
            # 获取评论
            comments_url = f"{url}/comments"
            comments = await crawler.fetch(comments_url)
            print(f"评论数: {len(comments)}")
            
        # 重复获取一些数据（测试缓存）
        print("\n3. 重复获取数据（测试缓存）")
        print("-" * 50)
        repeat_urls = [
            f"{base_url}/users/1",
            f"{base_url}/posts/1",
            f"{base_url}/posts/1/comments"
        ]
        for url in repeat_urls:
            await crawler.fetch(url)
            
        # 显示统计信息
        print("\n4. 爬虫统计")
        print("-" * 50)
        stats = await crawler.get_stats()
        print(json.dumps(stats, indent=2))
        
    finally:
        await crawler.stop()

if __name__ == "__main__":
    asyncio.run(main()) 