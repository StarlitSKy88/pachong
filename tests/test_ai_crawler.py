"""AI爬虫测试"""

import os
import json
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.crawlers.ai_crawler import AICrawler
from src.models.content import Content
from src.models.platform import Platform
from src.database.session import get_db

class TestAICrawler(AICrawler):
    """测试用AI爬虫"""
    
    def __init__(self, config=None):
        """初始化"""
        super().__init__(config or {
            "platform_name": "test",
            "rate_limit": 1.0,
            "retry_limit": 3
        })
        
    async def search(self, keyword: str, time_range: str = '24h'):
        """测试搜索方法"""
        return [
            "https://test.com/1",
            "https://test.com/2"
        ]
        
    async def get_html(self, url: str):
        """测试获取HTML方法"""
        return "<html><body>Test content</body></html>"
        
    async def parse(self, data):
        """测试解析方法"""
        return Content(
            platform_id=self.platform.id,
            url="https://test.com/1",
            title=data["title"],
            content=data["content"],
            author=data["author"],
            publish_time=datetime.fromisoformat(data["publish_time"]),
            images=data["media"]["images"],
            video_url=data["media"]["video"],
            stats=data["stats"]
        )

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
        id=1,
        name="test",
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
    crawler = TestAICrawler()
    with patch('src.database.session.get_db', new=lambda: mock_get_db):
        await crawler.initialize()
    return crawler

@pytest.fixture
def mock_response():
    """Mock响应"""
    mock = AsyncMock()
    mock.text = AsyncMock(return_value="<html><body>Test content</body></html>")
    return mock

@pytest.fixture
def mock_ai_response():
    """Mock AI响应"""
    return {
        "choices": [{
            "message": {
                "content": json.dumps({
                    "title": "Test title",
                    "content": "Test content",
                    "author": {"name": "test_author"},
                    "publish_time": "2024-03-27T12:00:00",
                    "stats": {"likes": 100, "comments": 50},
                    "media": {
                        "images": ["https://test.com/image1.jpg"],
                        "video": "https://test.com/video1.mp4"
                    }
                })
            }
        }]
    }

@pytest.fixture
def mock_quality_response():
    """Mock质量评估响应"""
    return {
        "choices": [{
            "message": {
                "content": "0.85"
            }
        }]
    }

class TestAICrawlerImplementation:
    """AI爬虫实现测试"""
    
    @pytest.mark.asyncio
    async def test_analyze_page_structure(self, crawler, mock_response, mock_ai_response):
        """测试页面结构分析"""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_ai_response
            )
            
            result = await crawler.analyze_page_structure("<html>Test</html>")
            assert isinstance(result, dict)
            assert "title" in result
            
    @pytest.mark.asyncio
    async def test_extract_content(self, crawler, mock_response, mock_ai_response):
        """测试内容提取"""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_ai_response
            )
            
            result = await crawler.extract_content(
                "<html>Test</html>",
                {"main_content": "div.content"}
            )
            assert isinstance(result, dict)
            assert result["title"] == "Test title"
            
    @pytest.mark.asyncio
    async def test_evaluate_quality(self, crawler, mock_response, mock_quality_response):
        """测试质量评估"""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_quality_response
            )
            
            result = await crawler.evaluate_quality({
                "title": "Test title",
                "content": "Test content"
            })
            assert isinstance(result, float)
            assert 0 <= result <= 1
            
    @pytest.mark.asyncio
    async def test_crawl_with_ai(self, crawler, mock_response, mock_ai_response, mock_quality_response):
        """测试AI辅助爬取"""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.json = AsyncMock(
                side_effect=[mock_ai_response, mock_ai_response, mock_quality_response]
            )
            
            result = await crawler.crawl_with_ai("https://test.com/1")
            assert isinstance(result, Content)
            assert result.title == "Test title"
            assert result.content == "Test content"
            
    @pytest.mark.asyncio
    async def test_crawl_with_ai_low_quality(self, crawler, mock_response):
        """测试低质量内容过滤"""
        mock_quality_response = {
            "choices": [{
                "message": {
                    "content": "0.5"
                }
            }]
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_quality_response
            )
            
            result = await crawler.crawl_with_ai("https://test.com/1")
            assert result is None
            
    @pytest.mark.asyncio
    async def test_crawl(self, crawler, mock_response, mock_ai_response, mock_quality_response):
        """测试批量爬取"""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.json = AsyncMock(
                side_effect=[mock_ai_response, mock_ai_response, mock_quality_response] * 2
            )
            
            results = await crawler.crawl(["test"], limit=2)
            assert len(results) == 2
            assert all(isinstance(r, Content) for r in results)
            
    @pytest.mark.asyncio
    async def test_error_handling(self, crawler, mock_response):
        """测试错误处理"""
        with patch.object(crawler, 'get_html', side_effect=Exception("Test error")):
            result = await crawler.crawl_with_ai("https://test.com/1")
            assert result is None 