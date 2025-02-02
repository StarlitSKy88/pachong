"""B站爬虫测试"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from src.crawlers.bilibili_crawler import BiliBiliCrawler

@pytest.fixture
def crawler():
    """创建爬虫实例"""
    return BiliBiliCrawler(
        concurrent_limit=2,
        retry_limit=2,
        timeout=5
    )

@pytest.fixture
def mock_video_data():
    """模拟视频数据"""
    return {
        "data": {
            "bvid": "BV1xx411c7mD",
            "aid": 12345,
            "title": "测试视频",
            "desc": "这是一个测试视频 #测试",
            "owner": {
                "mid": 10001,
                "name": "测试用户",
                "face": "http://example.com/avatar.jpg"
            },
            "stat": {
                "view": 1000,
                "like": 100,
                "coin": 50,
                "favorite": 80,
                "share": 30,
                "reply": 60
            },
            "duration": 180,
            "pic": "http://example.com/cover.jpg",
            "pubdate": int(datetime.now().timestamp()),
            "tname": "科技",
            "tag": "编程,Python,测试"
        }
    }

@pytest.fixture
def mock_search_data():
    """模拟搜索结果数据"""
    return {
        "data": {
            "result": [
                {
                    "bvid": "BV1xx411c7mD",
                    "title": "测试视频",
                    "pubdate": int(datetime.now().timestamp())
                }
            ]
        }
    }

@pytest.mark.asyncio
async def test_search(crawler, mock_search_data):
    """测试搜索功能"""
    with patch.object(crawler, '_request') as mock_request:
        mock_request.return_value = mock_search_data
        
        result = await crawler.search("测试")
        
        assert result == mock_search_data
        mock_request.assert_called_once()
        args = mock_request.call_args[0]
        assert args[0] == crawler.search_api
        
@pytest.mark.asyncio
async def test_get_video_info(crawler, mock_video_data):
    """测试获取视频信息"""
    with patch.object(crawler, '_request') as mock_request:
        mock_request.return_value = mock_video_data
        
        result = await crawler.get_video_info("BV1xx411c7mD")
        
        assert result == mock_video_data
        mock_request.assert_called_once()
        
@pytest.mark.asyncio
async def test_parse(crawler, mock_video_data):
    """测试数据解析"""
    result = await crawler.parse(mock_video_data)
    
    assert result["content_id"] == "BV1xx411c7mD"
    assert result["title"] == "测试视频"
    assert result["author"]["id"] == "10001"
    assert result["author"]["nickname"] == "测试用户"
    assert len(result["tags"]) == 4  # 分区标签 + 3个视频标签
    
def test_calculate_quality_score(crawler, mock_video_data):
    """测试质量分数计算"""
    score = crawler.calculate_quality_score(mock_video_data["data"])
    
    assert 0 <= score <= 100
    
    # 测试边界情况
    zero_data = {
        "stat": {
            "view": 0,
            "like": 0,
            "coin": 0,
            "favorite": 0,
            "reply": 0
        }
    }
    score = crawler.calculate_quality_score(zero_data)
    assert score == 0
    
def test_extract_tags(crawler, mock_video_data):
    """测试标签提取"""
    tags = crawler.extract_tags(mock_video_data["data"])
    
    assert "科技" in tags
    assert "编程" in tags
    assert "Python" in tags
    assert "测试" in tags
    assert len(tags) == 4
    
@pytest.mark.asyncio
async def test_crawl_with_empty_result(crawler):
    """测试空结果处理"""
    with patch.object(crawler, 'search') as mock_search:
        mock_search.return_value = {"data": {"result": []}}
        
        results = await crawler.crawl(["测试"], limit=1)
        assert len(results) == 0
        
@pytest.mark.asyncio
async def test_crawl_with_error(crawler, mock_search_data, mock_video_data):
    """测试错误处理"""
    with patch.object(crawler, 'search') as mock_search, \
         patch.object(crawler, 'get_video_info') as mock_video:
        # 模拟第一次搜索失败，第二次成功
        mock_search.side_effect = [
            Exception("搜索失败"),
            mock_search_data
        ]
        mock_video.return_value = mock_video_data
        
        results = await crawler.crawl(["测试"], limit=1)
        assert len(results) == 1
        
@pytest.mark.asyncio
async def test_time_range_filter(crawler, mock_search_data, mock_video_data):
    """测试时间范围过滤"""
    # 修改发布时间为7天前
    old_time = int((datetime.now() - timedelta(days=7)).timestamp())
    mock_search_data["data"]["result"][0]["pubdate"] = old_time
    
    with patch.object(crawler, 'search') as mock_search:
        mock_search.return_value = mock_search_data
        
        # 测试24小时范围
        results = await crawler.crawl(["测试"], time_range="24h", limit=1)
        assert len(results) == 0
        
        # 测试7天范围
        results = await crawler.crawl(["测试"], time_range="7d", limit=1)
        assert len(results) == 1
        
@pytest.mark.asyncio
async def test_metrics_recording(crawler, mock_video_data):
    """测试指标记录"""
    with patch.object(crawler.metrics, 'observe') as mock_observe:
        await crawler.parse(mock_video_data)
        
        # 验证是否记录了所有指标
        assert mock_observe.call_count == 3
        
        # 验证指标名称
        metric_names = [
            call[0][0]
            for call in mock_observe.call_args_list
        ]
        assert "video_quality" in metric_names
        assert "video_duration" in metric_names
        assert "reply_count" in metric_names 