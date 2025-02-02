"""B站爬虫测试"""

import os
import json
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.crawlers.bilibili.crawler import BiliBiliCrawler
from src.models.content import Content
from src.models.platform import Platform
from src.database.session import get_db

@pytest.fixture
def mock_db():
    """Mock数据库会话"""
    mock = AsyncMock()
    mock.commit = AsyncMock()
    mock.rollback = AsyncMock()
    mock.close = AsyncMock()
    mock.add = MagicMock()
    mock.refresh = AsyncMock()
    
    # 设置执行结果
    execute_result = MagicMock()
    execute_result.scalar_one_or_none = MagicMock(return_value=Platform(
        id=2,
        name="bilibili",
        is_active=True,
        rate_limit=1.0,
        retry_limit=3
    ))
    mock.execute = AsyncMock(return_value=execute_result)
    
    return mock

@pytest.fixture
def mock_get_db(mock_db):
    """Mock数据库会话获取函数"""
    class AsyncContextManager:
        async def __aenter__(self):
            return mock_db
            
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            if exc_type is not None:
                await mock_db.rollback()
            else:
                await mock_db.commit()
                
    return AsyncContextManager()

@pytest_asyncio.fixture
async def crawler(mock_db, mock_get_db):
    """创建爬虫实例"""
    crawler = BiliBiliCrawler()
    with patch('src.database.session.get_db', new=lambda: mock_get_db):
        await crawler.initialize()
    return crawler

@pytest.fixture
def mock_search_response():
    """Mock搜索响应"""
    return {
        "code": 0,
        "data": {
            "result": [
                {
                    "bvid": "BV1xx411",
                    "title": "测试视频1",
                    "description": "测试描述1",
                    "author": "测试UP主1",
                    "pubdate": 1711468800,  # 2024-03-27 12:00:00
                    "stat": {
                        "view": 1000,
                        "like": 100,
                        "coin": 50,
                        "favorite": 30,
                        "share": 20,
                        "reply": 40
                    },
                    "pic": "cover1.jpg",
                    "duration": 180
                },
                {
                    "bvid": "BV2xx411",
                    "title": "测试视频2",
                    "description": "测试描述2",
                    "author": "测试UP主2",
                    "pubdate": 1711472400,  # 2024-03-27 13:00:00
                    "stat": {
                        "view": 2000,
                        "like": 200,
                        "coin": 100,
                        "favorite": 60,
                        "share": 40,
                        "reply": 80
                    },
                    "pic": "cover2.jpg",
                    "duration": 360
                }
            ]
        }
    }

@pytest.fixture
def mock_detail_response():
    """Mock详情响应"""
    return {
        "code": 0,
        "data": {
            "bvid": "BV1xx411",
            "title": "测试视频1",
            "desc": "测试描述1",
            "owner": {
                "name": "测试UP主1",
                "face": "avatar1.jpg",
                "mid": "12345"
            },
            "pubdate": 1711468800,  # 2024-03-27 12:00:00
            "stat": {
                "view": 1000,
                "like": 100,
                "coin": 50,
                "favorite": 30,
                "share": 20,
                "reply": 40
            },
            "pic": "cover1.jpg",
            "duration": 180,
            "dynamic": "测试动态",
            "tags": ["标签1", "标签2"]
        }
    }

class TestBiliBiliCrawler:
    """B站爬虫测试"""
    
    @pytest.mark.asyncio
    async def test_search(self, crawler, mock_search_response):
        """测试搜索功能"""
        with patch.object(crawler, '_make_request') as mock_request:
            mock_request.return_value = AsyncMock()
            mock_request.return_value.json = AsyncMock(return_value=mock_search_response)
            
            urls = await crawler.search("测试")
            assert len(urls) == 2
            assert urls[0] == "https://www.bilibili.com/video/BV1xx411"
            assert urls[1] == "https://www.bilibili.com/video/BV2xx411"
            
    @pytest.mark.asyncio
    async def test_get_detail(self, crawler, mock_detail_response):
        """测试获取详情"""
        with patch.object(crawler, '_make_request') as mock_request:
            mock_request.return_value = AsyncMock()
            mock_request.return_value.json = AsyncMock(return_value=mock_detail_response)
            
            data = await crawler.get_detail("https://www.bilibili.com/video/BV1xx411")
            assert isinstance(data, dict)
            assert data["title"] == "测试视频1"
            assert data["desc"] == "测试描述1"
            assert data["owner"]["name"] == "测试UP主1"
            
    @pytest.mark.asyncio
    async def test_parse(self, crawler, mock_detail_response):
        """测试解析数据"""
        data = mock_detail_response["data"]
        content = await crawler.parse(data)
        
        assert isinstance(content, Content)
        assert content.title == "测试视频1"
        assert content.content == "测试描述1"
        assert content.author["name"] == "测试UP主1"
        assert content.publish_time == datetime.fromtimestamp(1711468800)
        assert content.views == 1000
        assert content.likes == 100
        assert content.coins == 50
        assert content.shares == 20
        assert content.comments == 40
        assert content.collects == 30
        
    @pytest.mark.asyncio
    async def test_crawl(self, crawler, mock_search_response, mock_detail_response):
        """测试批量爬取"""
        with patch.object(crawler, '_make_request') as mock_request:
            mock_request.return_value = AsyncMock()
            mock_request.return_value.json = AsyncMock(side_effect=[
                mock_search_response,
                mock_detail_response,
                mock_detail_response
            ])
            
            results = await crawler.crawl(["测试"], limit=2)
            assert len(results) == 2
            assert all(isinstance(r, Content) for r in results)
            
    @pytest.mark.asyncio
    async def test_error_handling(self, crawler):
        """测试错误处理"""
        with patch.object(crawler, '_make_request', side_effect=Exception("Test error")):
            result = await crawler.get_detail("https://www.bilibili.com/video/BV1xx411")
            assert result == {}
            
    @pytest.mark.asyncio
    async def test_api_error_handling(self, crawler):
        """测试API错误处理"""
        error_response = {"code": -404, "message": "视频不存在"}
        with patch.object(crawler, '_make_request') as mock_request:
            mock_request.return_value = AsyncMock()
            mock_request.return_value.json = AsyncMock(return_value=error_response)
            
            result = await crawler.get_detail("https://www.bilibili.com/video/BV1xx411")
            assert result == {} 