"""命令行工具"""

import os
import sys
import json
import click
import asyncio
from datetime import datetime
from typing import List

from .crawlers.xiaohongshu.crawler import XiaoHongShuCrawler
from .crawlers.bilibili.crawler import BiliBiliCrawler
from .utils.logger import get_logger

logger = get_logger(__name__)

@click.group()
def cli():
    """内容采集工具"""
    pass

@cli.command()
@click.option('--platform', '-p', type=click.Choice(['xiaohongshu', 'bilibili', 'all']), 
              default='all', help='目标平台')
@click.option('--keywords', '-k', required=True, help='搜索关键词，多个关键词用逗号分隔')
@click.option('--time-range', '-t', type=click.Choice(['24h', '1w', '1m']), 
              default='24h', help='时间范围')
@click.option('--limit', '-l', type=int, default=100, help='每个关键词的最大采集数量')
@click.option('--output', '-o', type=click.Path(), default='output', help='输出目录')
def crawl(platform: str, keywords: str, time_range: str, limit: int, output: str):
    """采集内容"""
    try:
        # 1. 准备关键词列表
        keyword_list = [k.strip() for k in keywords.split(',') if k.strip()]
        if not keyword_list:
            logger.error("No valid keywords provided")
            sys.exit(1)
            
        # 2. 准备输出目录
        os.makedirs(output, exist_ok=True)
        
        # 3. 创建爬虫实例
        crawlers = []
        if platform in ['all', 'xiaohongshu']:
            crawlers.append(XiaoHongShuCrawler())
        if platform in ['all', 'bilibili']:
            crawlers.append(BiliBiliCrawler())
            
        if not crawlers:
            logger.error(f"No crawler available for platform: {platform}")
            sys.exit(1)
            
        # 4. 运行爬虫
        asyncio.run(run_crawlers(crawlers, keyword_list, time_range, limit, output))
        
    except Exception as e:
        logger.error(f"Error running crawlers: {str(e)}")
        sys.exit(1)
        
async def run_crawlers(crawlers: List, keywords: List[str], time_range: str, 
                      limit: int, output: str):
    """运行爬虫
    
    Args:
        crawlers: 爬虫实例列表
        keywords: 关键词列表
        time_range: 时间范围
        limit: 数量限制
        output: 输出目录
    """
    try:
        # 1. 初始化爬虫
        init_tasks = []
        for crawler in crawlers:
            init_tasks.append(crawler.initialize())
        await asyncio.gather(*init_tasks)
        
        # 2. 运行爬虫
        for crawler in crawlers:
            platform_dir = os.path.join(output, crawler.platform_name)
            os.makedirs(platform_dir, exist_ok=True)
            
            # 采集内容
            contents = await crawler.crawl(keywords, time_range, limit)
            
            # 保存结果
            result_file = os.path.join(
                platform_dir, 
                f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(
                    [c.to_dict() for c in contents],
                    f,
                    ensure_ascii=False,
                    indent=2
                )
                
            logger.info(f"Saved {len(contents)} contents to {result_file}")
            
    except Exception as e:
        logger.error(f"Error running crawlers: {str(e)}")
        raise e
        
if __name__ == '__main__':
    cli() 