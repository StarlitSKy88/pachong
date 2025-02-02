import asyncio
from xhs_crawler import XHSCrawler
from bilibili_crawler import BiliBiliCrawler

async def test_xhs_crawler():
    """测试小红书爬虫"""
    print("Testing XHS Crawler...")
    crawler = XHSCrawler()
    await crawler.crawl(keyword="Python编程", max_pages=2)

async def test_bilibili_crawler():
    """测试B站爬虫"""
    print("Testing Bilibili Crawler...")
    crawler = BiliBiliCrawler()
    await crawler.crawl(keyword="Python教程", max_pages=2)

async def main():
    """主函数"""
    # 测试小红书爬虫
    await test_xhs_crawler()
    
    # 测试B站爬虫
    await test_bilibili_crawler()

if __name__ == "__main__":
    asyncio.run(main()) 