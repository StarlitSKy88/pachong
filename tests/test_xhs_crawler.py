import string
import time
import os
import json
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from datetime import datetime, UTC, timedelta
import asyncio
from typing import Dict, Any
import aiohttp

from src.crawlers.xiaohongshu.crawler import XiaoHongShuCrawler
from src.models.content import Content
from src.models.platform import Platform
from src.database.session import async_session_factory as Session
from src.crawlers.xiaohongshu.sign import XHSSign
from tests.utils.langsmith_helper import LangSmithHelper

@pytest.fixture
async def crawler(langsmith):
    """创建爬虫实例"""
    async with XiaoHongShuCrawler(langsmith=langsmith) as crawler:
        yield crawler

@pytest.fixture
def sign_generator():
    """创建签名生成器实例"""
    return XHSSign(device_id="test_device_id", salt="test_salt")

@pytest.fixture
def mock_response():
    """模拟响应"""
    return {
        "success": True,
        "data": {
            "items": [
                {
            "id": "note1",
                    "title": "测试笔记1",
                    "desc": "测试内容1",
                    "images": ["image1.jpg"],
            "user": {
                        "nickname": "测试用户1",
                        "avatar": "avatar1.jpg",
                        "id": "user1"
            },
            "stats": {
                "likes": 100,
                "comments": 50,
                "shares": 20,
                "collects": 30
            }
                }
            ]
        }
    }

@pytest.fixture
def mock_session():
    """创建模拟会话"""
    session = MagicMock()
    response = MagicMock()
    response.status = 200
    response.json = AsyncMock(return_value={
        "success": True,
        "data": {
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
    })
    session.request = AsyncMock(return_value=response)
    return session

@pytest.fixture
def langsmith():
    """LangSmith工具类实例"""
    return LangSmithHelper()

@pytest_asyncio.fixture
async def crawler(sign_generator, mock_session, langsmith):
    """爬虫实例"""
    crawler = XiaoHongShuCrawler(
        sign_generator=sign_generator
    )
    crawler.session = mock_session
    return crawler

class TestXiaoHongShuCrawler:
    """小红书爬虫测试类"""

    @pytest.mark.asyncio
    async def test_search(self, crawler, langsmith):
        """测试搜索功能"""
        trace = langsmith.start_trace("test_search")
        
        try:
            # Mock the response
            mock_response = {
                "success": True,
                "data": {
                    "notes": [
                        {
                            "id": "test_note_1",
                            "title": "Test Note 1",
                            "desc": "Test Description 1"
                        },
                        {
                            "id": "test_note_2",
                            "title": "Test Note 2",
                            "desc": "Test Description 2"
                        }
                    ],
                    "has_more": True,
                    "cursor": "next_page"
                }
            }

            # 创建mock响应对象
            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.json = AsyncMock(return_value=mock_response)
            mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
            mock_resp.__aexit__ = AsyncMock()

            # 创建mock session
            mock_session = AsyncMock()
            mock_session.get = AsyncMock(return_value=mock_resp)
            crawler.session = mock_session

            result = await crawler.search("test")
            langsmith.log_request(trace, "search", result)

            assert result["success"] is True
            assert len(result["data"]["notes"]) > 0
            assert result["data"]["has_more"] is True
            assert result["data"]["cursor"] == "next_page"
            assert len(result["data"]["notes"]) == 2
        finally:
            await langsmith.end_trace(trace)

    @pytest.mark.asyncio
    async def test_get_detail(self, crawler, langsmith):
        """测试获取笔记详情功能"""
        trace = langsmith.start_trace("test_get_detail")
        
        try:
            # Mock the response
            mock_response = {
                "success": True,
                "data": {
                    "note": {
                        "id": "test_note_1",
                        "title": "Test Note 1",
                        "desc": "Test Description 1",
                        "content": "Test Content 1",
                        "user": {
                            "id": "test_user_1",
                            "nickname": "Test User 1",
                            "avatar": "test_avatar_1.jpg"
                        },
                        "images": ["image1.jpg", "image2.jpg"],
                        "stats": {
                            "likes": 100,
                            "comments": 50,
                            "shares": 20,
                            "collects": 30
                        }
                    }
                }
            }

            # 创建mock响应对象
            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.json = AsyncMock(return_value=mock_response)
            mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
            mock_resp.__aexit__ = AsyncMock()

            # 创建mock session
            mock_session = AsyncMock()
            mock_session.get = AsyncMock(return_value=mock_resp)
            crawler.session = mock_session

            result = await crawler.get_detail("test_id")
            langsmith.log_request(trace, "get_detail", result)

            assert result["success"] is True
            assert result["data"]["note"]["id"] == "test_note_1"
            assert result["data"]["note"]["title"] == "Test Note 1"
            assert result["data"]["note"]["desc"] == "Test Description 1"
            assert len(result["data"]["note"]["images"]) == 2
        finally:
            await langsmith.end_trace(trace)

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
        assert content.user["nickname"] == "测试用户1"
        assert content.stats["likes"] == 100
        assert content.stats["comments"] == 50
        assert content.images == ["image1.jpg"]

    @pytest.mark.asyncio
    async def test_crawl(self, crawler, mock_search_response, mock_detail_response):
        """测试批量爬取"""
        with patch.object(crawler, '_make_request') as mock_request:
            # 准备足够的mock响应
            mock_request.side_effect = [
                mock_search_response,  # 第一次搜索
                mock_detail_response,  # 第一个详情
                mock_detail_response,  # 第二个详情
                mock_search_response,  # 第二次搜索（如果需要）
                mock_detail_response,  # 第三个详情（如果需要）
                mock_detail_response   # 第四个详情（如果需要）
            ]
            
            # 修改mock_search_response中的notes字段
            mock_search_response["data"]["notes"] = [
                {
                    "id": "note1",
                    "title": "测试笔记1",
                    "desc": "测试内容1",
                    "images": ["image1.jpg"],
                    "user": {
                        "nickname": "测试用户1",
                        "avatar": "avatar1.jpg",
                        "id": "user1"
                    },
                    "stats": {
                        "likes": 100,
                        "comments": 50,
                        "shares": 20,
                        "collects": 30
                    }
                },
                {
                    "id": "note2",
                    "title": "测试笔记2",
                    "desc": "测试内容2",
                    "images": ["image2.jpg"],
                    "user": {
                        "nickname": "测试用户2",
                        "avatar": "avatar2.jpg",
                        "id": "user2"
                    },
                    "stats": {
                        "likes": 200,
                        "comments": 100,
                        "shares": 40,
                        "collects": 60
                    }
                }
            ]
            
            results = await crawler.crawl(["测试"], max_items=2)
            
            # 验证结果
            assert len(results) == 2
            assert all(isinstance(r, Content) for r in results)
            
            # 验证调用次数
            expected_calls = 3  # 1次搜索 + 2次详情
            assert mock_request.call_count == expected_calls

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
        # Mock aiohttp.ClientSession.get to raise an exception
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(side_effect=aiohttp.ClientError("Test error"))
        crawler.session = mock_session
        
        # Call search method
        result = await crawler.search("test")
        
        # Verify error handling
        assert result == {
            "success": False,
            "data": {
                "notes": [],
                "has_more": False,
                "cursor": ""
            }
        }
        
        # Verify the request was attempted
        assert mock_session.get.call_count == 1

    @pytest.mark.asyncio
    async def test_concurrent_error_handling(self, crawler):
        """测试并发错误处理"""
        # Mock aiohttp.ClientSession.get to raise an exception
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.side_effect = aiohttp.ClientError("Test error")

            # Call search method multiple times concurrently
            tasks = [crawler.search("test") for _ in range(3)]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Verify all requests resulted in error handling
            expected_result = {
                "success": False,
                "data": {
                    "notes": [],
                    "has_more": False,
                    "cursor": ""
                }
            }
            
            # Check if all results match the expected error response
            for result in results:
                assert isinstance(result, dict)  # Ensure no exceptions were propagated
                assert result == expected_result

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
    """搜索响应数据"""
    return {
        "success": True,
        "data": {
            "notes": [
                {
                    "id": "note1",
                    "title": "测试笔记1",
                    "desc": "测试内容1",
                    "images": ["image1.jpg"],
                    "user": {
                        "nickname": "测试用户1",
                        "avatar": "avatar1.jpg",
                        "id": "user1"
                    },
                    "stats": {
                    "likes": 100,
                    "comments": 50,
                        "shares": 20,
                        "collects": 30
                    }
                },
                {
                    "id": "note2",
                    "title": "测试笔记2",
                    "desc": "测试内容2",
                    "images": ["image2.jpg"],
                    "user": {
                        "nickname": "测试用户2",
                        "avatar": "avatar2.jpg",
                        "id": "user2"
                    },
                    "stats": {
                    "likes": 200,
                    "comments": 100,
                        "shares": 40,
                        "collects": 60
                }
                }
            ],
            "has_more": True,
            "cursor": "next_cursor"
        }
    }

@pytest.fixture
def mock_detail_response():
    """详情响应数据"""
    return {
        "success": True,
        "data": {
            "note": {
                "id": "note1",
                "title": "测试笔记1",
                "content": "测试内容1",
                "desc": "测试描述1",
                "images": ["image1.jpg"],
                "user": {
                    "nickname": "测试用户1",
                    "avatar": "avatar1.jpg",
                    "id": "user1"
                },
                "stats": {
                    "likes": 100,
                    "comments": 50,
                    "shares": 20,
                    "collects": 30
                },
                "type": "normal"
            }
        }
    }

@pytest.fixture
def mock_proxy_manager():
    """代理管理器"""
    manager = MagicMock()
    manager.get_proxy = AsyncMock(return_value="http://127.0.0.1:8080")
    manager.report_success = AsyncMock()
    manager.report_failure = AsyncMock()
    return manager

@pytest.mark.asyncio
async def test_proxy_usage(crawler, mock_proxy_manager, langsmith):
    """测试代理使用"""
    trace = langsmith.start_trace("test_proxy_usage")
    
    try:
        crawler.proxy_manager = mock_proxy_manager
        result = await crawler.search("test")
        
        mock_proxy_manager.get_proxy.assert_called_once()
        mock_proxy_manager.report_success.assert_called_once()
        
        langsmith.log_request(trace, "search_with_proxy", result)
        await langsmith.end_trace(trace)
    except Exception as e:
        langsmith.log_error(trace, e)
        await langsmith.end_trace(trace)
        raise
    
    @pytest.mark.asyncio
async def test_proxy_error_handling(crawler, mock_proxy_manager, mock_search_response, langsmith):
    """测试代理错误处理"""
    trace = langsmith.start_trace("test_proxy_error_handling")

    try:
        crawler.proxy_manager = mock_proxy_manager
        mock_retry_policy = MagicMock()
        mock_retry_policy.should_retry = Mock(return_value=True)
        mock_retry_policy.get_delay = Mock(return_value=0.1)
        mock_retry_policy.max_retries = 3
        crawler.retry_policy = mock_retry_policy

        # 模拟代理错误
        mock_proxy_manager.get_proxy = AsyncMock(side_effect=[
            "http://proxy1",
            "http://proxy2",
            "http://proxy3"
        ])
        mock_proxy_manager.report_failure = AsyncMock()

        # 模拟请求失败
        crawler.session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_search_response)
        crawler.session.request = AsyncMock(side_effect=[
            aiohttp.ClientError("代理错误1"),
            aiohttp.ClientError("代理错误2"),
            mock_response
        ])

        result = await crawler.search("test")
        assert result == mock_search_response

        # 验证代理失败报告
        assert mock_proxy_manager.report_failure.call_count == 2

    except Exception as e:
        langsmith.log_error(trace, e)
        raise
    finally:
        langsmith.end_trace(trace)
            
    @pytest.mark.asyncio
async def test_proxy_rotation(crawler, mock_proxy_manager, langsmith):
    """测试代理轮换"""
    trace = langsmith.start_trace("test_proxy_rotation")
    
    try:
        crawler.proxy_manager = mock_proxy_manager
        proxies = ["http://127.0.0.1:8080", "http://127.0.0.1:8081"]
        mock_proxy_manager.get_proxy.side_effect = proxies
        
        for _ in range(2):
            await crawler.search("test")
        
        assert mock_proxy_manager.get_proxy.call_count == 2
        assert mock_proxy_manager.report_success.call_count == 2
        
        await langsmith.end_trace(trace)
    except Exception as e:
        langsmith.log_error(trace, e)
        await langsmith.end_trace(trace)
        raise
            
    @pytest.mark.asyncio
async def test_proxy_performance(crawler, mock_proxy_manager, langsmith):
    """测试代理性能"""
    trace = langsmith.start_trace("test_proxy_performance")
    
    try:
        crawler.proxy_manager = mock_proxy_manager
        start_time = datetime.now()
        
        await crawler.search("test")
        
        duration = datetime.now() - start_time
        assert duration < timedelta(seconds=5)  # 确保请求在5秒内完成
        
        await langsmith.end_trace(trace)
    except Exception as e:
        langsmith.log_error(trace, e)
        await langsmith.end_trace(trace)
        raise

@pytest.fixture
def mock_cookie_manager():
    """Cookie管理器"""
    manager = MagicMock()
    manager.get_cookie = AsyncMock(return_value={
        "sessionid": "test_session",
        "userid": "test_user"
    })
    manager.report_success = AsyncMock()
    manager.report_failure = AsyncMock()
    manager.is_valid = AsyncMock(return_value=True)
    return manager

class TestXiaoHongShuCrawlerCookie:
    """小红书爬虫Cookie测试类"""
    
    @pytest.mark.asyncio
    async def test_cookie_usage(self, crawler, mock_cookie_manager, langsmith):
        """测试Cookie使用"""
        trace = langsmith.start_trace("test_cookie_usage")

        try:
            # Mock cookie manager
            crawler.cookie_manager = mock_cookie_manager
            mock_cookie_manager.get_cookie = AsyncMock(return_value="test_cookie")
            mock_cookie_manager.report_success = AsyncMock()

            # Mock session
            mock_response = {
                "success": True,
                "data": {
                    "notes": [
                        {
                            "id": "test_note_1",
                            "title": "Test Note 1",
                            "desc": "Test Description 1"
                        }
                    ],
                    "has_more": False,
                    "cursor": ""
                }
            }

            mock_session = AsyncMock()
            mock_session.get = AsyncMock()
            mock_session.get.return_value.__aenter__.return_value.status = 200
            mock_session.get.return_value.__aenter__.return_value.json = AsyncMock(return_value=mock_response)
            crawler.session = mock_session

            result = await crawler.search("test")
            langsmith.log_request(trace, "search", result)

            mock_cookie_manager.get_cookie.assert_called_once()
            mock_cookie_manager.report_success.assert_called_once()
            assert result["success"] is True
            assert len(result["data"]["notes"]) == 1
        finally:
            await langsmith.end_trace(trace)
        
    @pytest.mark.asyncio
    async def test_cookie_error_handling(self, crawler, mock_cookie_manager, langsmith):
        """测试Cookie错误处理"""
        trace = langsmith.start_trace("test_cookie_error_handling")

        try:
            crawler.cookie_manager = mock_cookie_manager
            mock_cookie_manager.get_cookie = AsyncMock(side_effect=aiohttp.ClientError("Cookie error"))
            mock_cookie_manager.report_failure = AsyncMock()

            # Call search method
            result = await crawler.search("test")
            
            # Verify error handling
            assert result == {
                "success": False,
                "data": {
                    "notes": [],
                    "has_more": False,
                    "cursor": ""
                }
            }
            
            # Verify cookie was attempted to be retrieved
            mock_cookie_manager.get_cookie.assert_called_once()

        finally:
            await langsmith.end_trace(trace)
    
    @pytest.mark.asyncio
    async def test_cookie_rotation(self, crawler, mock_cookie_manager, langsmith):
        """测试Cookie轮换"""
        trace = langsmith.start_trace("test_cookie_rotation")
        
        try:
            crawler.cookie_manager = mock_cookie_manager
            cookies = [
                {"sessionid": "session1", "userid": "user1"},
                {"sessionid": "session2", "userid": "user2"}
            ]
            mock_cookie_manager.get_cookie.side_effect = cookies
            
            for _ in range(2):
                await crawler.search("test")
            
            assert mock_cookie_manager.get_cookie.call_count == 2
            assert mock_cookie_manager.report_success.call_count == 2
            
            await langsmith.end_trace(trace)
        except Exception as e:
            langsmith.log_error(trace, e)
            await langsmith.end_trace(trace)
            raise
    
    @pytest.mark.asyncio
    async def test_cookie_expiration(self, crawler, mock_cookie_manager, langsmith):
        """测试Cookie过期处理"""
        trace = langsmith.start_trace("test_cookie_expiration")
        
        try:
            crawler.cookie_manager = mock_cookie_manager
            mock_cookie_manager.is_valid.side_effect = [True, False]
            
            # 第一次请求成功
            await crawler.search("test")
            mock_cookie_manager.report_success.assert_called_once()
            
            # 第二次请求Cookie过期
            mock_cookie_manager.get_cookie.reset_mock()
            mock_cookie_manager.report_success.reset_mock()
            await crawler.search("test")
            
            # 验证获取新Cookie
            assert mock_cookie_manager.get_cookie.call_count == 1
            
            await langsmith.end_trace(trace)
        except Exception as e:
            langsmith.log_error(trace, e)
            await langsmith.end_trace(trace)
            raise

    @pytest.mark.asyncio
    async def test_cookie_management(self, crawler, mock_cookie_manager, langsmith):
        """测试Cookie管理"""
        trace = langsmith.start_trace("test_cookie_management")

        try:
            # Mock cookie manager
            crawler.cookie_manager = mock_cookie_manager
            mock_cookie_manager.get_cookie = AsyncMock(return_value="test_cookie")
            mock_cookie_manager.report_success = AsyncMock()
            mock_cookie_manager.report_failure = AsyncMock()

            # Mock response for success
            success_response = {
                "success": True,
                "data": {
                    "notes": [
                        {
                            "id": "test_note_1",
                            "title": "Test Note 1",
                            "desc": "Test Description 1"
                        }
                    ],
                    "has_more": False,
                    "cursor": ""
                }
            }

            # Mock response for cookie error
            cookie_error_response = {
                "success": False,
                "msg": "Invalid cookie"
            }

            # 创建成功的响应
            success_resp = AsyncMock()
            success_resp.status = 200
            success_resp.json = AsyncMock(return_value=success_response)
            success_resp.__aenter__ = AsyncMock(return_value=success_resp)
            success_resp.__aexit__ = AsyncMock()

            # 创建Cookie错误的响应
            cookie_error_resp = AsyncMock()
            cookie_error_resp.status = 401
            cookie_error_resp.json = AsyncMock(return_value=cookie_error_response)
            cookie_error_resp.__aenter__ = AsyncMock(return_value=cookie_error_resp)
            cookie_error_resp.__aexit__ = AsyncMock()

            # Mock session
            mock_session = AsyncMock()
            mock_session.get = AsyncMock()
            mock_session.get.side_effect = [cookie_error_resp, success_resp]
            crawler.session = mock_session

            # 第一次请求（Cookie错误）
            result1 = await crawler.search("test")
            assert result1["success"] is False
            assert mock_cookie_manager.report_failure.call_count == 1

            # 第二次请求（成功）
            result2 = await crawler.search("test")
            assert result2["success"] is True
            assert len(result2["data"]["notes"]) == 1

            # 验证Cookie管理器调用
            assert mock_cookie_manager.get_cookie.call_count == 2
        finally:
            await langsmith.end_trace(trace)

    @pytest.mark.asyncio
    async def test_proxy_management(self, crawler, mock_proxy_manager, mock_cookie_manager, langsmith):
        """测试代理管理"""
        trace = langsmith.start_trace("test_proxy_management")

        try:
            # Mock cookie manager
            crawler.cookie_manager = mock_cookie_manager
            mock_cookie_manager.get_cookie = AsyncMock(return_value="test_cookie")
            mock_cookie_manager.report_success = AsyncMock()
            mock_cookie_manager.report_failure = AsyncMock()

            # Mock proxy manager
            crawler.proxy_manager = mock_proxy_manager
            mock_proxy_manager.get_proxy = AsyncMock(return_value="http://test.proxy:8080")
            mock_proxy_manager.report_success = AsyncMock()
            mock_proxy_manager.report_failure = AsyncMock()

            # Mock response for success
            success_response = {
                "success": True,
                "data": {
                    "notes": [
                        {
                            "id": "test_note_1",
                            "title": "Test Note 1",
                            "desc": "Test Description 1"
                        }
                    ],
                    "has_more": False,
                    "cursor": ""
                }
            }

            # Mock response for proxy error
            proxy_error_response = {
                "success": False,
                "msg": "Proxy error"
            }

            # 创建成功的响应
            success_resp = AsyncMock()
            success_resp.status = 200
            success_resp.json = AsyncMock(return_value=success_response)
            success_resp.__aenter__ = AsyncMock(return_value=success_resp)
            success_resp.__aexit__ = AsyncMock()

            # 创建代理错误的响应
            proxy_error_resp = AsyncMock()
            proxy_error_resp.status = 407
            proxy_error_resp.json = AsyncMock(return_value=proxy_error_response)
            proxy_error_resp.__aenter__ = AsyncMock(return_value=proxy_error_resp)
            proxy_error_resp.__aexit__ = AsyncMock()

            # Mock session
            mock_session = AsyncMock()
            mock_session.get = AsyncMock()
            mock_session.get.side_effect = [proxy_error_resp, success_resp]
            crawler.session = mock_session

            # 第一次请求（代理错误）
            result1 = await crawler.search("test")
            assert result1["success"] is False
            assert mock_proxy_manager.report_failure.call_count == 1

            # 第二次请求（成功）
            result2 = await crawler.search("test")
            assert result2["success"] is True
            assert len(result2["data"]["notes"]) == 1

            # 验证代理管理器调用
            assert mock_proxy_manager.get_proxy.call_count == 2
            
            # 验证Cookie管理器调用
            assert mock_cookie_manager.get_cookie.call_count == 2
            assert mock_cookie_manager.report_success.call_count == 1
            assert mock_cookie_manager.report_failure.call_count == 1
        finally:
            await langsmith.end_trace(trace)

    @pytest.mark.asyncio
    async def test_network_error_handling(self, crawler, mock_cookie_manager, mock_proxy_manager, langsmith):
        """测试网络错误处理"""
        trace = langsmith.start_trace("test_network_error_handling")

        try:
            # Mock managers
            crawler.cookie_manager = mock_cookie_manager
            mock_cookie_manager.get_cookie = AsyncMock(return_value="test_cookie")
            mock_cookie_manager.report_failure = AsyncMock()

            crawler.proxy_manager = mock_proxy_manager
            mock_proxy_manager.get_proxy = AsyncMock(return_value="http://test.proxy:8080")
            mock_proxy_manager.report_failure = AsyncMock()

            # Mock session with network error
            mock_session = AsyncMock()
            mock_session.get = AsyncMock(side_effect=aiohttp.ClientError("Network error"))
            crawler.session = mock_session

            # 测试搜索
            result = await crawler.search("test")
            assert result["success"] is False
            assert result["data"]["notes"] == []
            assert result["data"]["has_more"] is False
            assert result["data"]["cursor"] == ""

            # 验证错误报告
            assert mock_cookie_manager.report_failure.call_count == 1
            assert mock_proxy_manager.report_failure.call_count == 1

            # 测试获取详情
            result = await crawler.get_detail("test_id")
            assert result["success"] is False
            assert "note" not in result["data"]

            # 验证错误报告
            assert mock_cookie_manager.report_failure.call_count == 2
            assert mock_proxy_manager.report_failure.call_count == 2
        finally:
            await langsmith.end_trace(trace)

    @pytest.mark.asyncio
    async def test_timeout_handling(self, crawler, mock_cookie_manager, mock_proxy_manager, langsmith):
        """测试超时处理"""
        trace = langsmith.start_trace("test_timeout_handling")

        try:
            # Mock managers
            crawler.cookie_manager = mock_cookie_manager
            mock_cookie_manager.get_cookie = AsyncMock(return_value="test_cookie")
            mock_cookie_manager.report_failure = AsyncMock()

            crawler.proxy_manager = mock_proxy_manager
            mock_proxy_manager.get_proxy = AsyncMock(return_value="http://test.proxy:8080")
            mock_proxy_manager.report_failure = AsyncMock()

            # Mock session with timeout
            mock_session = AsyncMock()
            mock_session.get = AsyncMock(side_effect=asyncio.TimeoutError())
            crawler.session = mock_session

            # 测试搜索
            result = await crawler.search("test")
            assert result["success"] is False
            assert result["data"]["notes"] == []
            assert result["data"]["has_more"] is False
            assert result["data"]["cursor"] == ""

            # 验证错误报告
            assert mock_cookie_manager.report_failure.call_count == 1
            assert mock_proxy_manager.report_failure.call_count == 1

            # 测试获取详情
            result = await crawler.get_detail("test_id")
            assert result["success"] is False
            assert "note" not in result["data"]

            # 验证错误报告
            assert mock_cookie_manager.report_failure.call_count == 2
            assert mock_proxy_manager.report_failure.call_count == 2
        finally:
            await langsmith.end_trace(trace)

    @pytest.mark.asyncio
    async def test_retry_on_failure(self, crawler, mock_cookie_manager, mock_proxy_manager, langsmith):
        """测试失败重试机制"""
        trace = langsmith.start_trace("test_retry_on_failure")

        try:
            # Mock managers
            crawler.cookie_manager = mock_cookie_manager
            mock_cookie_manager.get_cookie = AsyncMock(return_value="test_cookie")
            mock_cookie_manager.report_success = AsyncMock()
            mock_cookie_manager.report_failure = AsyncMock()

            crawler.proxy_manager = mock_proxy_manager
            mock_proxy_manager.get_proxy = AsyncMock(return_value="http://test.proxy:8080")
            mock_proxy_manager.report_success = AsyncMock()
            mock_proxy_manager.report_failure = AsyncMock()

            # Mock response for success
            success_response = {
                "success": True,
                "data": {
                    "notes": [
                        {
                            "id": "test_note_1",
                            "title": "Test Note 1",
                            "desc": "Test Description 1"
                        }
                    ],
                    "has_more": False,
                    "cursor": ""
                }
            }

            # 创建成功的响应
            success_resp = AsyncMock()
            success_resp.status = 200
            success_resp.json = AsyncMock(return_value=success_response)
            success_resp.__aenter__ = AsyncMock(return_value=success_resp)
            success_resp.__aexit__ = AsyncMock()

            # Mock session with failures and success
            mock_session = AsyncMock()
            mock_session.get = AsyncMock()
            mock_session.get.side_effect = [
                AsyncMock(
                    __aenter__=AsyncMock(side_effect=aiohttp.ClientError("First failure")),
                    __aexit__=AsyncMock()
                ),
                AsyncMock(
                    __aenter__=AsyncMock(side_effect=asyncio.TimeoutError()),
                    __aexit__=AsyncMock()
                ),
                success_resp
            ]
            crawler.session = mock_session

            # 测试搜索
            result = await crawler.search("test")
            assert result["success"] is True
            assert len(result["data"]["notes"]) == 1

            # 验证重试次数
            assert mock_session.get.call_count == 3
            assert mock_cookie_manager.report_failure.call_count == 2
            assert mock_cookie_manager.report_success.call_count == 1
            assert mock_proxy_manager.report_failure.call_count == 2
            assert mock_proxy_manager.report_success.call_count == 1
        finally:
            await langsmith.end_trace(trace)

@pytest.fixture
def mock_rate_limiter():
    """模拟速率限制器"""
    rate_limiter = MagicMock()
    rate_limiter.get_delay = AsyncMock(return_value=0.1)
    rate_limiter.acquire = AsyncMock()
    rate_limiter.release = AsyncMock()
    rate_limiter.report_success = AsyncMock()
    rate_limiter.report_failure = AsyncMock()
    return rate_limiter

@pytest.mark.asyncio
async def test_adaptive_rate_limiting(self, crawler, mock_rate_limiter, mock_cookie_manager, langsmith):
    """测试自适应速率限制"""
    trace = langsmith.start_trace("test_adaptive_rate_limiting")

    try:
        # Mock cookie manager
        crawler.cookie_manager = mock_cookie_manager
        mock_cookie_manager.get_cookie = AsyncMock(return_value="test_cookie")
        mock_cookie_manager.report_success = AsyncMock()
        mock_cookie_manager.report_failure = AsyncMock()

        # Mock rate limiter
        crawler.rate_limiter = mock_rate_limiter
        mock_rate_limiter.acquire = AsyncMock()
        mock_rate_limiter.release = AsyncMock()
        mock_rate_limiter.update_delay = AsyncMock()

        # Mock response for success
        success_response = {
            "success": True,
            "data": {
                "notes": [
                    {
                        "id": "test_note_1",
                        "title": "Test Note 1",
                        "desc": "Test Description 1"
                    }
                ],
                "has_more": False,
                "cursor": ""
            }
        }

        # Mock response for rate limit
        rate_limit_response = {
            "success": False,
            "msg": "Rate limit exceeded"
        }

        # 创建成功的响应
        success_resp = AsyncMock()
        success_resp.status = 200
        success_resp.json = AsyncMock(return_value=success_response)
        success_resp.__aenter__ = AsyncMock(return_value=success_resp)
        success_resp.__aexit__ = AsyncMock()

        # 创建速率限制的响应
        rate_limit_resp = AsyncMock()
        rate_limit_resp.status = 429
        rate_limit_resp.json = AsyncMock(return_value=rate_limit_response)
        rate_limit_resp.__aenter__ = AsyncMock(return_value=rate_limit_resp)
        rate_limit_resp.__aexit__ = AsyncMock()

        # Mock session
        mock_session = AsyncMock()
        mock_session.get = AsyncMock()
        mock_session.get.side_effect = [rate_limit_resp, success_resp]
        crawler.session = mock_session

        # 第一次请求（触发速率限制）
        result1 = await crawler.search("test")
        assert result1["success"] is False
        assert mock_rate_limiter.update_delay.call_count == 1

        # 第二次请求（成功）
        result2 = await crawler.search("test")
        assert result2["success"] is True
        assert len(result2["data"]["notes"]) == 1

        # 验证调用次数
        assert mock_session.get.call_count == 2
        assert mock_rate_limiter.acquire.call_count == 2
        assert mock_rate_limiter.release.call_count == 2
        assert mock_cookie_manager.get_cookie.call_count == 2
        assert mock_cookie_manager.report_failure.call_count == 1
        assert mock_cookie_manager.report_success.call_count == 1
    finally:
        await langsmith.end_trace(trace)

@pytest.mark.asyncio
async def test_concurrent_requests(self, crawler, mock_rate_limiter, mock_cookie_manager, langsmith):
    """测试并发请求控制"""
    trace = langsmith.start_trace("test_concurrent_requests")

    try:
        # Mock cookie manager
        crawler.cookie_manager = mock_cookie_manager
        mock_cookie_manager.get_cookie = AsyncMock(return_value="test_cookie")
        mock_cookie_manager.report_success = AsyncMock()

        # Mock rate limiter
        crawler.rate_limiter = mock_rate_limiter
        mock_rate_limiter.acquire = AsyncMock()
        mock_rate_limiter.release = AsyncMock()

        # Mock response
        mock_response = {
            "success": True,
            "data": {
                "notes": [
                    {
                        "id": "test_note_1",
                        "title": "Test Note 1",
                        "desc": "Test Description 1"
                    }
                ],
                "has_more": False,
                "cursor": ""
            }
        }

        # 创建mock响应对象
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value=mock_response)
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock()

        # 创建mock session
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_resp)
        crawler.session = mock_session

        # 并发执行多个请求
        tasks = [crawler.search("test") for _ in range(5)]
        results = await asyncio.gather(*tasks)

        # 验证所有请求都成功
        for result in results:
            assert result["success"] is True
            assert len(result["data"]["notes"]) == 1

        # 验证调用次数
        assert mock_session.get.call_count == 5
        assert mock_rate_limiter.acquire.call_count == 5
        assert mock_rate_limiter.release.call_count == 5
        assert mock_cookie_manager.get_cookie.call_count == 5
        assert mock_cookie_manager.report_success.call_count == 5

        # 验证并发控制（通过rate_limiter的acquire和release调用时间间隔）
        acquire_times = [call[1]["time"] for call in mock_rate_limiter.acquire.mock_calls]
        release_times = [call[1]["time"] for call in mock_rate_limiter.release.mock_calls]
        
        # 验证acquire和release的配对
        for i in range(5):
            assert acquire_times[i] <= release_times[i]
            
        # 验证并发数不超过限制
        concurrent_requests = 0
        max_concurrent = 0
        for time in sorted(acquire_times + release_times):
            if time in acquire_times:
                concurrent_requests += 1
            else:
                concurrent_requests -= 1
            max_concurrent = max(max_concurrent, concurrent_requests)
        
        assert max_concurrent <= crawler.max_concurrent_requests
    finally:
        await langsmith.end_trace(trace)

@pytest.fixture
def mock_retry_policy():
    """模拟重试策略"""
    retry_policy = MagicMock()
    retry_policy.max_retries = 3
    retry_policy.get_delay = AsyncMock(return_value=0.1)
    retry_policy.should_retry = AsyncMock(return_value=True)
    return retry_policy

@pytest.mark.asyncio
async def test_retry_on_failure(crawler, mock_retry_policy, mock_search_response, langsmith):
    """测试失败重试"""
    trace = langsmith.start_trace("test_retry_on_failure")

    try:
        crawler.retry_policy = mock_retry_policy
        mock_retry_policy.should_retry = Mock(return_value=True)
        mock_retry_policy.get_delay = Mock(return_value=0.1)
        mock_retry_policy.max_retries = 3

        with patch.object(crawler.session, 'request') as mock_request:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_search_response)

            mock_request.side_effect = [
                aiohttp.ClientError("First attempt failed"),
                aiohttp.ClientError("Second attempt failed"),
                mock_response
            ]

            result = await crawler.search("test")
            assert result == mock_search_response
            assert mock_retry_policy.should_retry.call_count == 2
            assert mock_retry_policy.get_delay.call_count == 2

    finally:
        await langsmith.end_trace(trace)

@pytest.mark.asyncio
async def test_retry_with_backoff(self, crawler, mock_rate_limiter, mock_cookie_manager, langsmith):
    """测试带退避的重试机制"""
    trace = langsmith.start_trace("test_retry_with_backoff")

    try:
        # Mock cookie manager
        crawler.cookie_manager = mock_cookie_manager
        mock_cookie_manager.get_cookie = AsyncMock(return_value="test_cookie")
        mock_cookie_manager.report_success = AsyncMock()
        mock_cookie_manager.report_failure = AsyncMock()

        # Mock rate limiter
        crawler.rate_limiter = mock_rate_limiter
        mock_rate_limiter.acquire = AsyncMock()
        mock_rate_limiter.release = AsyncMock()

        # Mock response
        mock_response = {
            "success": True,
            "data": {
                "notes": [
                    {
                        "id": "test_note_1",
                        "title": "Test Note 1",
                        "desc": "Test Description 1"
                    }
                ],
                "has_more": False,
                "cursor": ""
            }
        }

        # Mock session with failures and success
        mock_session = AsyncMock()
        mock_session.get = AsyncMock()
        
        # 创建失败的响应
        fail_resp1 = AsyncMock()
        fail_resp1.__aenter__ = AsyncMock(side_effect=aiohttp.ClientError("First failure"))
        fail_resp1.__aexit__ = AsyncMock()
        
        fail_resp2 = AsyncMock()
        fail_resp2.__aenter__ = AsyncMock(side_effect=aiohttp.ClientError("Second failure"))
        fail_resp2.__aexit__ = AsyncMock()
        
        # 创建成功的响应
        success_resp = AsyncMock()
        success_resp.status = 200
        success_resp.json = AsyncMock(return_value=mock_response)
        success_resp.__aenter__ = AsyncMock(return_value=success_resp)
        success_resp.__aexit__ = AsyncMock()
        
        # 设置side_effect
        mock_session.get.side_effect = [fail_resp1, fail_resp2, success_resp]
        crawler.session = mock_session

        result = await crawler.search("test")
        langsmith.log_request(trace, "search", result)

        # 验证重试次数
        assert mock_session.get.call_count == 3
        # 验证最终结果
        assert result["success"] is True
        assert len(result["data"]["notes"]) == 1
        # 验证Cookie管理器调用
        assert mock_cookie_manager.get_cookie.call_count == 3
        assert mock_cookie_manager.report_failure.call_count == 2
        assert mock_cookie_manager.report_success.call_count == 1
        # 验证速率限制器调用
        assert mock_rate_limiter.acquire.call_count == 3
        assert mock_rate_limiter.release.call_count == 3
    finally:
        await langsmith.end_trace(trace)

@pytest.mark.asyncio
async def test_retry_specific_errors(crawler, mock_retry_policy, mock_search_response, langsmith):
    """测试特定错误重试"""
    trace = langsmith.start_trace("test_retry_specific_errors")

    try:
        # 设置mock
        crawler.retry_policy = mock_retry_policy
        mock_retry_policy.should_retry = Mock(return_value=True)
        mock_retry_policy.get_delay = Mock(return_value=0.1)
        mock_retry_policy.max_retries = 3

        # 模拟请求
        crawler.session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_search_response)
        crawler.session.request = AsyncMock(side_effect=[
            aiohttp.ClientError("连接错误"),
            aiohttp.ClientError("超时错误"),
            mock_response
        ])

        result = await crawler.search("test")
        assert result == mock_search_response

        # 验证重试次数
        assert mock_retry_policy.should_retry.call_count == 2
        assert mock_retry_policy.get_delay.call_count == 2

    except Exception as e:
        langsmith.log_error(trace, e)
        raise
    finally:
        langsmith.end_trace(trace)

@pytest.fixture
def mock_data_cleaner():
    """模拟数据清洗器"""
    data_cleaner = MagicMock()
    data_cleaner.clean_text = MagicMock(side_effect=lambda x: x)
    data_cleaner.clean_html = MagicMock(side_effect=lambda x: x)
    data_cleaner.clean_url = MagicMock(side_effect=lambda x: x)
    data_cleaner.validate_data = MagicMock(return_value=True)
    return data_cleaner

@pytest.mark.asyncio
async def test_text_cleaning(crawler, mock_data_cleaner, langsmith):
    """测试文本清洗"""
    trace = langsmith.start_trace("test_text_cleaning")
    
    try:
        # 创建新的mock对象
        mock_cleaner = MagicMock()
        mock_cleaner.clean_text = MagicMock()
        crawler.data_cleaner = mock_cleaner
        
        # 测试特殊字符清洗
        text = "测试文本\n\t\r带有特殊字符"
        mock_cleaner.clean_text.return_value = "测试文本 带有特殊字符"
        result = crawler.data_cleaner.clean_text(text)
        assert result == "测试文本 带有特殊字符"
        mock_cleaner.clean_text.assert_called_with(text)
        
        # 测试空白字符处理
        text = "  多余的  空白  字符  "
        mock_cleaner.clean_text.return_value = "多余的 空白 字符"
        result = crawler.data_cleaner.clean_text(text)
        assert result == "多余的 空白 字符"
        mock_cleaner.clean_text.assert_called_with(text)
        
        await langsmith.end_trace(trace)
    except Exception as e:
        langsmith.log_error(trace, e)
        await langsmith.end_trace(trace)
        raise

@pytest.mark.asyncio
async def test_html_cleaning(crawler, mock_data_cleaner, langsmith):
    """测试HTML清洗"""
    trace = langsmith.start_trace("test_html_cleaning")
    
    try:
        # 创建新的mock对象
        mock_cleaner = MagicMock()
        mock_cleaner.clean_html = MagicMock()
        crawler.data_cleaner = mock_cleaner
        
        # 测试HTML标签清洗
        html = "<div>测试<script>alert('xss')</script>内容</div>"
        mock_cleaner.clean_html.return_value = "<div>测试内容</div>"
        result = crawler.data_cleaner.clean_html(html)
        assert result == "<div>测试内容</div>"
        mock_cleaner.clean_html.assert_called_with(html)
        
        # 测试样式清洗
        html = '<div style="color: red">带样式的内容</div>'
        mock_cleaner.clean_html.return_value = "<div>带样式的内容</div>"
        result = crawler.data_cleaner.clean_html(html)
        assert result == "<div>带样式的内容</div>"
        mock_cleaner.clean_html.assert_called_with(html)
        
        await langsmith.end_trace(trace)
    except Exception as e:
        langsmith.log_error(trace, e)
        await langsmith.end_trace(trace)
        raise

@pytest.mark.asyncio
async def test_url_cleaning(crawler, mock_data_cleaner, langsmith):
    """测试URL清洗"""
    trace = langsmith.start_trace("test_url_cleaning")
    
    try:
        # 创建新的mock对象
        mock_cleaner = MagicMock()
        mock_cleaner.clean_url = MagicMock()
        crawler.data_cleaner = mock_cleaner
        
        # 测试图片URL清洗
        url = "http://example.com/image.jpg!thumb"
        mock_cleaner.clean_url.return_value = "http://example.com/image.jpg"
        result = crawler.data_cleaner.clean_url(url)
        assert result == "http://example.com/image.jpg"
        mock_cleaner.clean_url.assert_called_with(url)
        
        # 测试视频URL清洗
        url = "http://example.com/video.mp4?watermark=1"
        mock_cleaner.clean_url.return_value = "http://example.com/video.mp4"
        result = crawler.data_cleaner.clean_url(url)
        assert result == "http://example.com/video.mp4"
        mock_cleaner.clean_url.assert_called_with(url)
        
        await langsmith.end_trace(trace)
    except Exception as e:
        langsmith.log_error(trace, e)
        await langsmith.end_trace(trace)
        raise

@pytest.mark.asyncio
async def test_data_validation(crawler, mock_data_cleaner, langsmith):
    """测试数据验证"""
    trace = langsmith.start_trace("test_data_validation")
    
    try:
        crawler.data_cleaner = mock_data_cleaner
        
        # 测试有效数据
        valid_data = {
            "id": "123",
            "title": "测试标题",
            "content": "测试内容",
            "images": ["http://example.com/image.jpg"]
        }
        mock_data_cleaner.validate_data.return_value = True
        assert crawler.data_cleaner.validate_data(valid_data) is True
        mock_data_cleaner.validate_data.assert_called_with(valid_data)
        
        # 测试无效数据
        invalid_data = {
            "id": "123",
            "title": "",  # 空标题
            "content": None,  # 空内容
            "images": []  # 空图片列表
        }
        mock_data_cleaner.validate_data.return_value = False
        assert crawler.data_cleaner.validate_data(invalid_data) is False
        mock_data_cleaner.validate_data.assert_called_with(invalid_data)
        
        await langsmith.end_trace(trace)
    except Exception as e:
        langsmith.log_error(trace, e)
        await langsmith.end_trace(trace)
        raise 