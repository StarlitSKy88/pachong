"""爬虫系统集成测试"""

import pytest
import asyncio
from datetime import datetime, timedelta
from src.crawlers.bilibili_crawler import BiliBiliCrawler
from src.crawlers.xiaohongshu_crawler import XiaoHongShuCrawler
from src.database import content_dao, platform_dao
from src.models.content import Content

@pytest.fixture
async def crawlers():
    """创建爬虫实例"""
    bilibili = BiliBiliCrawler(
        concurrent_limit=2,
        retry_limit=2,
        timeout=5
    )
    xiaohongshu = XiaoHongShuCrawler(
        concurrent_limit=2,
        retry_limit=2,
        timeout=5
    )
    
    async with bilibili, xiaohongshu:
        yield {
            "bilibili": bilibili,
            "xiaohongshu": xiaohongshu
        }

@pytest.mark.asyncio
async def test_concurrent_crawling(crawlers):
    """测试并发爬取"""
    keywords = ["Python", "AI"]
    tasks = []
    
    # 创建爬取任务
    for crawler in crawlers.values():
        task = asyncio.create_task(
            crawler.crawl(
                keywords=keywords,
                time_range="24h",
                limit=5
            )
        )
        tasks.append(task)
    
    # 等待所有任务完成
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 验证结果
    for result in results:
        assert not isinstance(result, Exception)
        assert isinstance(result, list)
        
@pytest.mark.asyncio
async def test_data_consistency(crawlers):
    """测试数据一致性"""
    # 清理测试数据
    await content_dao.delete_many({
        "create_time": {
            "$gte": datetime.now() - timedelta(hours=1)
        }
    })
    
    # 执行爬取
    results = await crawlers["bilibili"].crawl(
        keywords=["测试"],
        limit=1
    )
    
    # 验证数据保存
    assert len(results) == 1
    content = results[0]
    
    # 从数据库查询
    saved = await content_dao.get_by_id(content["content_id"])
    assert saved is not None
    assert saved.title == content["title"]
    assert saved.platform == "bilibili"
    
@pytest.mark.asyncio
async def test_error_recovery(crawlers):
    """测试错误恢复"""
    # 模拟网络错误
    async def unstable_crawl():
        try:
            await crawlers["xiaohongshu"].crawl(
                keywords=["测试"],
                limit=1
            )
        except Exception as e:
            return str(e)
        return "success"
    
    # 执行多次爬取
    results = await asyncio.gather(*[
        unstable_crawl()
        for _ in range(3)
    ])
    
    # 验证至少有一次成功
    assert "success" in results
    
@pytest.mark.asyncio
async def test_performance(crawlers):
    """测试性能"""
    start_time = datetime.now()
    
    # 执行大量并发请求
    tasks = []
    for crawler in crawlers.values():
        for keyword in ["Python", "AI", "数据"]:
            task = asyncio.create_task(
                crawler.crawl(
                    keywords=[keyword],
                    limit=3
                )
            )
            tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    
    # 计算总耗时
    duration = (datetime.now() - start_time).total_seconds()
    
    # 验证性能
    assert duration < 30  # 总耗时不超过30秒
    
    # 验证结果数量
    total_items = sum(len(result) for result in results)
    assert total_items > 0
    
@pytest.mark.asyncio
async def test_data_deduplication(crawlers):
    """测试数据去重"""
    # 使用相同关键词执行多次爬取
    results1 = await crawlers["bilibili"].crawl(
        keywords=["测试"],
        limit=5
    )
    results2 = await crawlers["bilibili"].crawl(
        keywords=["测试"],
        limit=5
    )
    
    # 获取内容ID
    ids1 = {item["content_id"] for item in results1}
    ids2 = {item["content_id"] for item in results2}
    
    # 验证重复数据
    duplicates = ids1.intersection(ids2)
    assert len(duplicates) > 0  # 应该有重复数据
    
    # 验证数据库中没有重复
    for content_id in duplicates:
        count = await content_dao.count({
            "content_id": content_id
        })
        assert count == 1  # 每个ID只应该有一条记录
        
@pytest.mark.asyncio
async def test_data_validation(crawlers):
    """测试数据验证"""
    results = await crawlers["xiaohongshu"].crawl(
        keywords=["测试"],
        limit=1
    )
    
    assert len(results) == 1
    content = results[0]
    
    # 验证必填字段
    assert content["content_id"]
    assert content["title"]
    assert content["author"]
    assert content["publish_time"]
    
    # 验证时间格式
    publish_time = datetime.strptime(
        content["publish_time"],
        "%Y-%m-%d %H:%M:%S"
    )
    assert publish_time <= datetime.now()
    
    # 验证数值字段
    assert isinstance(content["likes"], int)
    assert isinstance(content["comments"], int)
    assert content["likes"] >= 0
    assert content["comments"] >= 0
    
@pytest.mark.asyncio
async def test_metrics_aggregation(crawlers):
    """测试指标聚合"""
    # 执行爬取
    await asyncio.gather(
        crawlers["bilibili"].crawl(
            keywords=["测试"],
            limit=3
        ),
        crawlers["xiaohongshu"].crawl(
            keywords=["测试"],
            limit=3
        )
    )
    
    # 获取指标数据
    bilibili_metrics = crawlers["bilibili"].metrics.get_metrics()
    xiaohongshu_metrics = crawlers["xiaohongshu"].metrics.get_metrics()
    
    # 验证B站特有指标
    assert "video_quality" in bilibili_metrics
    assert "video_duration" in bilibili_metrics
    
    # 验证小红书特有指标
    assert "note_count" in xiaohongshu_metrics
    assert "image_count" in xiaohongshu_metrics
    
    # 验证通用指标
    for metrics in [bilibili_metrics, xiaohongshu_metrics]:
        assert "request_latency" in metrics
        assert "request_result" in metrics
        assert "concurrent_requests" in metrics 