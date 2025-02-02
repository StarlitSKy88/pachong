import asyncio
import logging
from datetime import datetime
from .bilibili_crawler import BiliBiliCrawler
from .bilibili_sign import BilibiliSign

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_sign_generator():
    """测试签名生成器"""
    print("\nTesting Sign Generator...")
    sign_generator = BilibiliSign()
    
    # 测试搜索签名
    search_params = sign_generator.generate_search_sign('Python教程')
    print("\nSearch Params:")
    print(search_params)
    
    # 测试视频签名
    video_params = sign_generator.generate_video_sign('BV1ex411J7GE')
    print("\nVideo Params:")
    print(video_params)
    
    # 测试用户签名
    user_params = sign_generator.generate_user_sign('546195')
    print("\nUser Params:")
    print(user_params)

async def test_crawler():
    """测试爬虫"""
    print("\nTesting Bilibili Crawler...")
    crawler = BiliBiliCrawler()
    
    # 测试搜索视频
    print("\nSearching videos...")
    videos = await crawler.search_videos('Python教程', page=1)
    print(f"Found {len(videos)} videos")
    
    if videos:
        # 测试解析数据
        print("\nParsing first video...")
        video = videos[0]
        content_data = await crawler.parse(video)
        print("Parsed data:")
        print(content_data)
        
        # 测试提取标签
        print("\nExtracting tags...")
        tags = crawler.extract_tags(video)
        print("Tags:", tags)
    
    # 测试完整爬取流程
    print("\nTesting full crawl process...")
    await crawler.crawl('Python教程', max_pages=1)

async def main():
    """主函数"""
    try:
        # 测试签名生成
        await test_sign_generator()
        
        # 测试爬虫
        await test_crawler()
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 