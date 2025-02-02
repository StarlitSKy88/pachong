import asyncio
import logging
from datetime import datetime
from .xhs_crawler import XHSCrawler
from .xhs_sign import XHSSign

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_sign_generator():
    """测试签名生成器"""
    print("\nTesting Sign Generator...")
    sign_generator = XHSSign()
    
    # 测试搜索签名
    search_params = sign_generator.generate_search_sign('Python编程')
    print("\nSearch Params:")
    print(search_params)
    
    # 测试笔记签名
    note_params = sign_generator.generate_note_sign('64a123b5000000001f00a2e1')
    print("\nNote Params:")
    print(note_params)
    
    # 测试用户签名
    user_params = sign_generator.generate_user_sign('5ff0e6550000000001008400')
    print("\nUser Params:")
    print(user_params)

async def test_crawler():
    """测试爬虫"""
    print("\nTesting XHS Crawler...")
    crawler = XHSCrawler()
    
    # 测试搜索笔记
    print("\nSearching notes...")
    notes = await crawler.search_notes('Python编程', page=1)
    print(f"Found {len(notes)} notes")
    
    if notes:
        # 测试解析数据
        print("\nParsing first note...")
        note = notes[0]
        content_data = await crawler.parse(note)
        print("Parsed data:")
        print(content_data)
        
        # 测试提取标签
        print("\nExtracting tags...")
        tags = crawler.extract_tags(note)
        print("Tags:", tags)
    
    # 测试完整爬取流程
    print("\nTesting full crawl process...")
    await crawler.crawl('Python编程', max_pages=1)

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