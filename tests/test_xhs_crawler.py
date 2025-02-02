import string
import time
import os
import json
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, UTC

from src.crawlers.xiaohongshu.crawler import XiaoHongShuCrawler
from src.models.content import Content
from src.models.platform import Platform
from src.database.session import async_session_factory as Session
from src.crawlers.xiaohongshu.sign import XHSSign
from .utils.langsmith_helper import LangSmithHelper

@pytest.fixture
def crawler():
    """创建爬虫实例"""
    return XiaoHongShuCrawler()

@pytest.fixture
def sign_generator():
    """创建签名生成器实例"""
    return XHSSign(device_id="test_device_id", salt="test_salt")

@pytest.fixture
def mock_response():
    """模拟响应数据"""
    return {
        "success": True,
        "data": {
            "id": "note1",
            "title": "测试笔记",
            "content": "测试内容",
            "time": "2024-03-27T12:00:00+00:00",
            "user": {
                "id": "user1",
                "nickname": "测试用户"
            },
            "images": ["image1.jpg", "image2.jpg"],
            "video": "video.mp4",
            "stats": {
                "likes": 100,
                "comments": 50,
                "shares": 20,
                "collects": 30
            }
        }
    }

@pytest.fixture
def langsmith():
    """LangSmith工具类实例"""
    return LangSmithHelper()

@pytest_asyncio.fixture
async def crawler():
    """爬虫实例"""
    async with XiaoHongShuCrawler() as crawler:
        yield crawler

class TestXiaoHongShuCrawler:
    """小红书爬虫测试类"""

    @pytest.mark.asyncio
    async def test_search(self, crawler, mock_search_response, langsmith):
        """测试搜索功能"""
        # 开始追踪
        trace = langsmith.start_trace("test_search")
        
        try:
            # 模拟请求
            crawler._make_request = AsyncMock(return_value=mock_search_response)
            
            # 执行搜索
            results = await crawler.search("测试关键词")
            
            # 记录请求
            langsmith.log_request(
                trace,
                "https://www.xiaohongshu.com/search",
                mock_search_response
            )
            
            # 记录解析
            langsmith.log_parse(
                trace,
                mock_search_response,
                {"results": results}
            )
            
            # 验证结果
            assert len(results) == 2
            assert all(isinstance(item, dict) for item in results)
            
            # 结束追踪
            langsmith.end_trace(trace, success=True)
            
        except Exception as e:
            # 记录错误
            langsmith.log_error(trace, e)
            langsmith.end_trace(trace, success=False)
            raise

    @pytest.mark.asyncio
    async def test_get_detail(self, crawler, mock_detail_response, langsmith):
        """测试获取笔记详情功能"""
        # 开始追踪
        trace = langsmith.start_trace("test_get_detail")
        
        try:
            # 模拟请求
            crawler._make_request = AsyncMock(return_value=mock_detail_response)
            
            # 执行获取详情
            result = await crawler.get_detail("test_note_id")
            
            # 记录请求
            langsmith.log_request(
                trace,
                "https://www.xiaohongshu.com/note/test_note_id",
                mock_detail_response
            )
            
            # 记录解析
            langsmith.log_parse(
                trace,
                mock_detail_response,
                {"result": result}
            )
            
            # 验证结果
            assert isinstance(result, dict)
            assert "content" in result
            
            # 结束追踪
            langsmith.end_trace(trace, success=True)
            
        except Exception as e:
            # 记录错误
            langsmith.log_error(trace, e)
            langsmith.end_trace(trace, success=False)
            raise

    def test_parse(self, mock_detail_response, langsmith):
        """测试解析功能"""
        # 开始追踪
        trace = langsmith.start_trace("test_parse")
        
        try:
            # 执行解析
            content = Content.from_response(mock_detail_response)
            
            # 记录解析
            langsmith.log_parse(
                trace,
                mock_detail_response,
                content.to_dict()
            )
            
            # 验证结果
            assert isinstance(content, Content)
            assert content.title == mock_detail_response["data"]["note"]["title"]
            
            # 结束追踪
            langsmith.end_trace(trace, success=True)
            
        except Exception as e:
            # 记录错误
            langsmith.log_error(trace, e)
            langsmith.end_trace(trace, success=False)
            raise

    @pytest.mark.asyncio
    async def test_crawl(self, crawler, mock_search_response, mock_detail_response, langsmith):
        """测试批量爬取功能"""
        # 开始追踪
        trace = langsmith.start_trace("test_crawl")
        
        try:
            # 模拟请求
            crawler._make_request = AsyncMock(side_effect=[
                mock_search_response,
                mock_detail_response,
                mock_detail_response
            ])
            
            # 执行批量爬取
            results = await crawler.crawl("测试关键词", max_pages=1)
            
            # 记录搜索请求
            langsmith.log_request(
                trace,
                "https://www.xiaohongshu.com/search",
                mock_search_response
            )
            
            # 记录详情请求
            for i in range(2):
                langsmith.log_request(
                    trace,
                    f"https://www.xiaohongshu.com/note/test_note_id_{i}",
                    mock_detail_response
                )
            
            # 记录解析
            langsmith.log_parse(
                trace,
                {"search": mock_search_response, "details": [mock_detail_response] * 2},
                {"results": results}
            )
            
            # 验证结果
            assert len(results) == 2
            assert all(isinstance(item, Content) for item in results)
            
            # 结束追踪
            langsmith.end_trace(trace, success=True)
            
        except Exception as e:
            # 记录错误
            langsmith.log_error(trace, e)
            langsmith.end_trace(trace, success=False)
            raise

    def test_validate_url(self, crawler):
        """测试URL验证功能"""
        # 有效URL
        valid_url = "https://www.xiaohongshu.com/explore/123456"
        assert crawler._validate_url(valid_url) is True
        
        # 无效URL
        invalid_url = "https://www.example.com/123456"
        assert crawler._validate_url(invalid_url) is False

    def test_sign_generator(self, sign_generator):
        """测试签名生成器"""
        # 测试搜索签名
        search_params = sign_generator.generate_search_sign("测试")
        assert "sign" in search_params
        assert "device_id" in search_params
        assert "timestamp" in search_params
        assert "nonce" in search_params
        
        # 测试笔记签名
        note_params = sign_generator.generate_note_sign("note1")
        assert "sign" in note_params
        assert "device_id" in note_params
        assert "timestamp" in note_params
        assert "nonce" in note_params

    @pytest.mark.asyncio
    async def test_error_handling(self, crawler, langsmith):
        """测试错误处理"""
        # 开始追踪
        trace = langsmith.start_trace("test_error_handling")
        
        try:
            # 模拟网络错误
            crawler._make_request = AsyncMock(side_effect=Exception("网络错误"))
            
            # 执行搜索
            with pytest.raises(Exception) as exc_info:
                await crawler.search("测试关键词")
            
            # 记录错误
            langsmith.log_error(trace, exc_info.value)
            
            # 验证错误信息
            assert str(exc_info.value) == "网络错误"
            
            # 结束追踪
            langsmith.end_trace(trace, success=True)
            
        except Exception as e:
            # 记录错误
            langsmith.log_error(trace, e)
            langsmith.end_trace(trace, success=False)
            raise

@pytest.fixture
async def mock_db():
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
        name="xiaohongshu",
        is_active=True,
        rate_limit=2.0,
        retry_limit=3
    ))
    mock.execute = AsyncMock(return_value=execute_result)
    
    return mock

@pytest.fixture
async def mock_get_db(mock_db):
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

@pytest.fixture
def mock_search_response():
    """Mock搜索响应"""
    return {
        "data": {
            "notes": [
                {
                    "id": "note1",
                    "title": "测试笔记1",
                    "desc": "测试内容1",
                    "user": {"nickname": "测试用户1"},
                    "time": "2024-03-27T12:00:00",
                    "likes": 100,
                    "comments": 50,
                    "images": ["image1.jpg"],
                    "video": "video1.mp4"
                },
                {
                    "id": "note2",
                    "title": "测试笔记2",
                    "desc": "测试内容2",
                    "user": {"nickname": "测试用户2"},
                    "time": "2024-03-27T13:00:00",
                    "likes": 200,
                    "comments": 100,
                    "images": ["image2.jpg"],
                    "video": None
                }
            ]
        }
    }

@pytest.fixture
def mock_detail_response():
    """Mock详情响应"""
    return {
        "success": True,
        "data": {
            "note": {
                "id": "note1",
                "title": "测试笔记1",
                "content": "测试内容1",
                "user": {
                    "nickname": "测试用户1",
                    "avatar": "avatar1.jpg",
                    "id": "user1"
                },
                "time": "2024-03-27T12:00:00",
                "stats": {
                    "likes": 100,
                    "comments": 50,
                    "shares": 20,
                    "collects": 30
                },
                "images": ["image1.jpg"],
                "video": "video1.mp4"
            }
        }
    }

@pytest.mark.asyncio
async def test_error_handling(crawler):
    """测试错误处理"""
    # 测试搜索错误处理
    with patch('aiohttp.ClientSession.request', new_callable=AsyncMock) as mock_request:
        mock_request.side_effect = Exception("测试异常")
        results = await crawler.search("测试")
        assert len(results) == 0

    # 测试获取详情错误处理
    with patch('aiohttp.ClientSession.request', new_callable=AsyncMock) as mock_request:
        mock_request.side_effect = Exception("测试异常")
        result = await crawler.get_detail("https://www.xiaohongshu.com/explore/note1")
        assert result is None

class TestXiaoHongShuCrawler:
    """小红书爬虫测试"""
    
    @pytest.mark.asyncio
    async def test_search(self, crawler, mock_search_response):
        """测试搜索功能"""
        with patch.object(crawler, '_make_request') as mock_request:
            mock_request.return_value = AsyncMock()
            mock_request.return_value.json = AsyncMock(return_value=mock_search_response)
            
            urls = await crawler.search("测试")
            assert len(urls) == 2
            assert urls[0] == "https://www.xiaohongshu.com/explore/note1"
            assert urls[1] == "https://www.xiaohongshu.com/explore/note2"
            
    @pytest.mark.asyncio
    async def test_get_detail(self, crawler, mock_detail_response):
        """测试获取详情"""
        with patch.object(crawler, '_make_request') as mock_request:
            mock_request.return_value = AsyncMock()
            mock_request.return_value.json = AsyncMock(return_value=mock_detail_response)
            
            data = await crawler.get_detail("https://www.xiaohongshu.com/explore/note1")
            assert isinstance(data, dict)
            assert data["title"] == "测试笔记1"
            assert data["content"] == "测试内容1"
            assert data["user"]["nickname"] == "测试用户1"
            
    @pytest.mark.asyncio
    async def test_parse(self, crawler, mock_detail_response):
        """测试解析数据"""
        data = {
            "id": "note1",
            "title": "测试笔记1",
            "content": "测试内容1",
            "user": {
                "nickname": "测试用户1",
                "avatar": "avatar1.jpg",
                "id": "user1"
            },
            "time": "2024-03-27T12:00:00",
            "stats": {
                "likes": 100,
                "comments": 50,
                "shares": 20,
                "collects": 30
            },
            "images": ["image1.jpg"],
            "video": "video1.mp4"
        }
        content = await crawler.parse(data)
        
        assert isinstance(content, Content)
        assert content.title == "测试笔记1"
        assert content.content == "测试内容1"
        assert content.author["name"] == "测试用户1"
        assert content.publish_time == datetime.fromisoformat("2024-03-27T12:00:00")
        assert content.likes == 100
        assert content.comments == 50
        
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