import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime
import asyncio
import os
import pytest_asyncio
from contextlib import asynccontextmanager
import time

from src.crawlers.base import BaseCrawler
from src.models.platform import Platform
from src.models.content import Content
from src.utils.proxy import ProxyManager
from src.utils.cookie import CookieManager

class TestCrawler(BaseCrawler):
    """测试用爬虫类"""
    
    def __init__(self, config=None):
        """初始化"""
        super().__init__(config or {'platform_name': 'test'})
        self.platform_name = 'test'
        self.cookie_manager = MagicMock()
        self.cookie_manager.refresh_cookies = AsyncMock()
        self.cookie_manager.get_cookies = MagicMock(return_value={})
        self.retry_limit = int(os.getenv('RETRY_LIMIT', '3'))
        
    async def search(self, keyword: str):
        """测试搜索方法"""
        return []
        
    async def get_detail(self, item):
        """测试获取详情方法"""
        return item
        
    async def crawl(self, keywords, time_range='24h', limit=100):
        """测试爬取方法"""
        return []
        
    async def parse(self, data):
        """测试解析方法"""
        return data

    async def request(self, url: str, method: str = "GET", **kwargs):
        """发送请求"""
        if 'cookies' not in kwargs:
            kwargs['cookies'] = self.cookie_manager.get_cookies()
        response = await self._request(url, method, **kwargs)
        if isinstance(response, dict):
            return response
        if response and response.status == 403:
            await self.cookie_manager.refresh_cookies()
            response = None
        return response

    async def _wait_for_rate_limit(self):
        """等待频率限制"""
        await asyncio.sleep(1)

    async def initialize(self):
        """初始化"""
        from src.database.session import get_db
        async with get_db() as db:
            platform = await db.query(Platform).filter_by(name=self.platform_name).first()
            if not platform:
                platform = Platform(
                    name=self.platform_name,
                    is_active=True
                )
                db.add(platform)
            elif not platform.is_active:
                raise ValueError(f"Platform {self.platform_name} is not active")
            self.platform = platform
            
    async def save_content(self, content: Content):
        """保存内容"""
        from src.database.session import get_db
        async with get_db() as db:
            db.add(content)

    async def _get_or_create_platform(self, db):
        """获取或创建平台记录"""
        platform = db.query(Platform).filter(Platform.name == self.platform_name).first()
        if not platform:
            platform = Platform(name=self.platform_name, is_active=True)
            db.add(platform)
            await db.commit()
        return platform

    async def _request(self, url: str, method: str = "GET", **kwargs):
        """发送请求"""
        for _ in range(self.retry_limit):
            try:
                async with self.session.request(method, url, **kwargs) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 403:
                        print(f"请求失败: {response.status} {url}")
                        return response
                    else:
                        print(f"请求失败: {response.status} {url}")
                        return None
            except Exception as e:
                print(f"请求异常: {e}")
                if _ == self.retry_limit - 1:
                    raise e
                await asyncio.sleep(1)

@pytest_asyncio.fixture(scope='function')
async def crawler():
    """返回一个测试爬虫实例"""
    _crawler = TestCrawler()
    await _crawler.__aenter__()
    try:
        yield _crawler
    finally:
        await _crawler.__aexit__(None, None, None)

@pytest.fixture
def mock_db():
    """Mock数据库会话"""
    mock = AsyncMock()
    mock.commit = AsyncMock()
    mock.rollback = AsyncMock()
    mock.close = AsyncMock()
    mock.add = MagicMock()
    
    # 设置查询链
    query_mock = MagicMock()
    filter_by_mock = MagicMock()
    first_mock = AsyncMock()
    
    mock.query = MagicMock(return_value=query_mock)
    query_mock.filter_by = MagicMock(return_value=filter_by_mock)
    filter_by_mock.first = first_mock
    
    # 设置返回值
    async def _first():
        return first_mock.return_value
    filter_by_mock.first = _first
    
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

class TestBaseCrawler:
    """基础爬虫测试类"""
    
    @pytest.mark.asyncio
    async def test_initialization(self, crawler):
        """测试爬虫初始化"""
        assert crawler.platform_name == "test"
        assert isinstance(crawler.proxy_manager, ProxyManager)
        assert hasattr(crawler.cookie_manager, 'get_cookies')
        assert hasattr(crawler.cookie_manager, 'refresh_cookies')
        assert crawler.rate_limit > 0
        assert crawler.retry_limit > 0
        
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """测试上下文管理器"""
        crawler = TestCrawler()
        await crawler.__aenter__()
        assert crawler.session is not None
        await crawler.__aexit__(None, None, None)
        await crawler.session.close()
        crawler.session = None
        assert crawler.session is None
        
    @pytest.mark.asyncio
    async def test_rate_limit(self, crawler):
        """测试请求频率限制"""
        start_time = time.time()
        
        # 连续发送3个请求
        for _ in range(3):
            await crawler._wait_for_rate_limit()
            
        duration = time.time() - start_time
        assert duration >= 2.0  # 应该至少等待2秒
        
    @pytest.mark.asyncio
    async def test_make_request_success(self, crawler):
        """测试请求成功"""
        test_url = "https://test.com"
        test_data = {'key': 'value'}
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = test_data
        
        with patch('aiohttp.ClientSession.request') as mock_request:
            mock_request.return_value.__aenter__.return_value = mock_response
            
            response = await crawler.request(test_url)
            assert response is not None
            assert response == test_data
            
    @pytest.mark.asyncio
    async def test_make_request_retry(self, crawler):
        """测试请求重试"""
        test_url = "https://test.com"
        
        with patch('aiohttp.ClientSession.request') as mock_request:
            mock_request.side_effect = Exception("Test error")
            
            with pytest.raises(Exception):
                await crawler.request(test_url)
                
            assert mock_request.call_count == crawler.retry_limit
            
    @pytest.mark.asyncio
    async def test_make_request_403(self, crawler):
        """测试403状态码处理"""
        test_url = "https://test.com"
        
        mock_response = AsyncMock()
        mock_response.status = 403
        
        with patch('aiohttp.ClientSession.request') as mock_request:
            mock_request.return_value.__aenter__.return_value = mock_response
            with patch.object(crawler.cookie_manager, 'refresh_cookies') as mock_refresh:
                response = await crawler.request(test_url)
                assert response is None
                assert mock_refresh.called
                
    @pytest.mark.asyncio
    async def test_initialize(self, crawler, mock_db, mock_get_db):
        """测试初始化平台配置"""
        mock_platform = Platform(
            name="test",
            is_active=True,
            rate_limit=2.0,
            retry_limit=5,
            cookie_config={}
        )

        with patch('src.database.session.get_db', return_value=mock_get_db):
            mock_db.query.return_value.filter.return_value.first.return_value = mock_platform
            await crawler.initialize()
            assert crawler.platform == mock_platform

    @pytest.mark.asyncio
    async def test_initialize_inactive_platform(self, crawler, mock_db, mock_get_db):
        """测试初始化非活动平台"""
        mock_platform = Platform(
            name="test",
            is_active=False
        )

        with patch('src.database.session.get_db', return_value=mock_get_db):
            mock_db.query.return_value.filter.return_value.first.return_value = mock_platform
            with pytest.raises(ValueError):
                await crawler.initialize()

    @pytest.mark.asyncio
    async def test_save_content(self, crawler, mock_db, mock_get_db):
        """测试保存内容"""
        test_content = Content(
            platform_id=1,
            url="https://test.com",
            title="Test",
            content="Test content"
        )

        with patch('src.database.session.get_db', return_value=mock_get_db):
            await crawler.save_content(test_content)
            mock_db.add.assert_called_once_with(test_content)
            mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_save_content_error(self, crawler, mock_db, mock_get_db):
        """测试保存内容失败"""
        test_content = Content(
            platform_id=1,
            url="https://test.com",
            title="Test",
            content="Test content"
        )

        with patch('src.database.session.get_db', return_value=mock_get_db):
            mock_db.commit.side_effect = Exception("Test error")
            with pytest.raises(Exception):
                await crawler.save_content(test_content)
            mock_db.rollback.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_request_with_custom_headers(self, crawler):
        """测试自定义请求头"""
        test_url = "https://test.com"
        custom_headers = {'Custom-Header': 'test-value'}
        
        mock_response = AsyncMock()
        mock_response.status = 200
        
        with patch('aiohttp.ClientSession.request') as mock_request:
            mock_request.return_value.__aenter__.return_value = mock_response
            
            await crawler.request(test_url, headers=custom_headers)
            mock_request.assert_called_once()
            _, kwargs = mock_request.call_args
            assert kwargs['headers']['Custom-Header'] == 'test-value'
            
    @pytest.mark.asyncio
    async def test_request_with_params(self, crawler):
        """测试URL参数"""
        test_url = "https://test.com"
        test_params = {'key': 'value'}
        
        mock_response = AsyncMock()
        mock_response.status = 200
        
        with patch('aiohttp.ClientSession.request') as mock_request:
            mock_request.return_value.__aenter__.return_value = mock_response
            
            await crawler.request(test_url, params=test_params)
            mock_request.assert_called_once()
            _, kwargs = mock_request.call_args
            assert kwargs['params'] == test_params
            
    @pytest.mark.asyncio
    async def test_request_with_data(self, crawler):
        """测试POST数据"""
        test_url = "https://test.com"
        test_data = {'key': 'value'}
        
        mock_response = AsyncMock()
        mock_response.status = 200
        
        with patch('aiohttp.ClientSession.request') as mock_request:
            mock_request.return_value.__aenter__.return_value = mock_response
            
            await crawler.request(test_url, method='POST', data=test_data)
            mock_request.assert_called_once()
            _, kwargs = mock_request.call_args
            assert kwargs['data'] == test_data
            
    @pytest.mark.asyncio
    async def test_request_with_proxy(self, crawler):
        """测试代理使用"""
        test_url = "https://test.com"
        test_proxy = "http://test.proxy:8080"
        
        mock_response = AsyncMock()
        mock_response.status = 200
        
        with patch('aiohttp.ClientSession.request') as mock_request:
            mock_request.return_value.__aenter__.return_value = mock_response
            
            await crawler.request(test_url, proxy=test_proxy)
            mock_request.assert_called_once()
            _, kwargs = mock_request.call_args
            assert kwargs['proxy'] == test_proxy
            
    @pytest.mark.asyncio
    async def test_request_with_timeout(self, crawler):
        """测试超时设置"""
        test_url = "https://test.com"
        test_timeout = 60
        
        mock_response = AsyncMock()
        mock_response.status = 200
        
        with patch('aiohttp.ClientSession.request') as mock_request:
            mock_request.return_value.__aenter__.return_value = mock_response
            
            await crawler.request(test_url, timeout=test_timeout)
            mock_request.assert_called_once()
            _, kwargs = mock_request.call_args
            assert kwargs['timeout'] == test_timeout
            
    @pytest.mark.asyncio
    async def test_request_with_cookies(self, crawler):
        """测试Cookie使用"""
        test_url = "https://test.com"
        test_cookies = {'session': 'test123'}
        
        with patch.object(crawler.cookie_manager, 'get_cookies', return_value=test_cookies):
            with patch('aiohttp.ClientSession.request') as mock_request:
                mock_request.return_value.__aenter__.return_value = mock_response
                
                await crawler.request(test_url)
                mock_request.assert_called_once()
                _, kwargs = mock_request.call_args
                assert kwargs['cookies'] == test_cookies
                
    @pytest.mark.asyncio
    async def test_get_or_create_platform(self, crawler, mock_db, mock_get_db):
        """测试获取或创建平台记录"""
        # 测试获取已存在的平台
        mock_platform = Platform(
            name="test",
            is_active=True
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_platform
        platform = await crawler._get_or_create_platform(mock_db)
        assert platform == mock_platform
        
    @pytest.mark.asyncio
    async def test_environment_variables(self):
        """测试环境变量配置"""
        # 设置环境变量
        os.environ['USER_AGENT'] = 'test-user-agent'
        os.environ['RATE_LIMIT'] = '2.5'
        os.environ['RETRY_LIMIT'] = '5'
        
        crawler = TestCrawler()
        assert crawler.headers['User-Agent'] == 'test-user-agent'
        assert crawler.rate_limit == 2.5
        assert crawler.retry_limit == 5
        
        # 清理环境变量
        del os.environ['USER_AGENT']
        del os.environ['RATE_LIMIT']
        del os.environ['RETRY_LIMIT'] 