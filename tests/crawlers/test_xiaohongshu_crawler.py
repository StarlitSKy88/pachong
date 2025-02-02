"""小红书爬虫测试"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from src.crawlers.xiaohongshu_crawler import XiaoHongShuCrawler

@pytest.fixture
def crawler():
    """创建爬虫实例"""
    return XiaoHongShuCrawler(
        concurrent_limit=2,
        retry_limit=2,
        timeout=5
    )

@pytest.fixture
def mock_note_data():
    """模拟笔记数据"""
    return {
        "note": {
            "id": "123456789",
            "title": "测试笔记",
            "desc": "这是一个测试笔记 #测试标签",
            "user": {
                "user_id": "10001",
                "nickname": "测试用户",
                "avatar": "http://example.com/avatar.jpg"
            },
            "images": [
                {"url": "http://example.com/image1.jpg"},
                {"url": "http://example.com/image2.jpg"}
            ],
            "video": {
                "url": "http://example.com/video.mp4"
            },
            "likes": 1000,
            "comments": 100,
            "shares": 50,
            "time": int(datetime.now().timestamp() * 1000),
            "hash_tags": [
                {"name": "测试标签"},
                {"name": "小红书"}
            ]
        }
    }

@pytest.fixture
def mock_search_data():
    """模拟搜索结果数据"""
    return {
        "data": {
            "notes": [
                {
                    "id": "123456789",
                    "title": "测试笔记",
                    "time": int(datetime.now().timestamp() * 1000)
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
async def test_get_note(crawler, mock_note_data):
    """测试获取笔记详情"""
    with patch.object(crawler, '_request') as mock_request:
        mock_request.return_value = mock_note_data
        
        result = await crawler.get_note("123456789")
        
        assert result == mock_note_data
        mock_request.assert_called_once()
        
@pytest.mark.asyncio
async def test_get_user(crawler):
    """测试获取用户信息"""
    mock_user_data = {
        "user": {
            "user_id": "10001",
            "nickname": "测试用户",
            "avatar": "http://example.com/avatar.jpg"
        }
    }
    
    with patch.object(crawler, '_request') as mock_request:
        mock_request.return_value = mock_user_data
        
        result = await crawler.get_user("10001")
        
        assert result == mock_user_data
        mock_request.assert_called_once()
        
@pytest.mark.asyncio
async def test_parse(crawler, mock_note_data):
    """测试数据解析"""
    result = await crawler.parse(mock_note_data)
    
    assert result["content_id"] == "123456789"
    assert result["title"] == "测试笔记"
    assert result["author"]["id"] == "10001"
    assert result["author"]["nickname"] == "测试用户"
    assert len(result["images"]) == 2
    assert result["video_url"] == "http://example.com/video.mp4"
    assert len(result["tags"]) == 2
    
def test_extract_tags(crawler, mock_note_data):
    """测试标签提取"""
    tags = crawler.extract_tags(mock_note_data["note"])
    
    assert "测试标签" in tags
    assert "小红书" in tags
    assert len(tags) == 2
    
@pytest.mark.asyncio
async def test_crawl_with_empty_result(crawler):
    """测试空结果处理"""
    with patch.object(crawler, 'search') as mock_search:
        mock_search.return_value = {"data": {"notes": []}}
        
        results = await crawler.crawl(["测试"], limit=1)
        assert len(results) == 0
        
@pytest.mark.asyncio
async def test_crawl_with_error(crawler, mock_search_data, mock_note_data):
    """测试错误处理"""
    with patch.object(crawler, 'search') as mock_search, \
         patch.object(crawler, 'get_note') as mock_note:
        # 模拟第一次搜索失败，第二次成功
        mock_search.side_effect = [
            Exception("搜索失败"),
            mock_search_data
        ]
        mock_note.return_value = mock_note_data
        
        results = await crawler.crawl(["测试"], limit=1)
        assert len(results) == 1
        
@pytest.mark.asyncio
async def test_time_range_filter(crawler, mock_search_data, mock_note_data):
    """测试时间范围过滤"""
    # 修改发布时间为7天前
    old_time = int((datetime.now() - timedelta(days=7)).timestamp() * 1000)
    mock_search_data["data"]["notes"][0]["time"] = old_time
    
    with patch.object(crawler, 'search') as mock_search:
        mock_search.return_value = mock_search_data
        
        # 测试24小时范围
        results = await crawler.crawl(["测试"], time_range="24h", limit=1)
        assert len(results) == 0
        
        # 测试7天范围
        results = await crawler.crawl(["测试"], time_range="7d", limit=1)
        assert len(results) == 1
        
@pytest.mark.asyncio
async def test_metrics_recording(crawler, mock_note_data):
    """测试指标记录"""
    with patch.object(crawler.metrics, 'observe') as mock_observe:
        await crawler.parse(mock_note_data)
        
        # 验证是否记录了所有指标
        assert mock_observe.call_count == 2  # note_count 和 image_count
        
        # 验证指标名称
        metric_names = [
            call[0][0]
            for call in mock_observe.call_args_list
        ]
        assert "note_count" in metric_names
        assert "image_count" in metric_names
        
@pytest.mark.asyncio
async def test_process_items(crawler, mock_note_data):
    """测试数据处理"""
    parsed_data = await crawler.parse(mock_note_data)
    processed_data = await crawler.process_items([parsed_data])
    
    assert len(processed_data) == 1
    assert processed_data[0]["content_id"] == parsed_data["content_id"]
    # 验证数据脱敏
    assert processed_data[0]["author"]["nickname"] != "测试用户" 