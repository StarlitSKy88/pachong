import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime
from pytest_asyncio import fixture as async_fixture

from src.crawlers.base_crawler import BaseCrawler
from src.utils.headers_manager import HeadersManager
from src.utils.cookie_manager import CookieManager
from src.utils.proxy_manager import ProxyManager
from src.utils.rate_limiter import RateLimiter
from src.utils.exceptions import CrawlerException
from src.utils.circuit_breaker import CircuitBreaker

@async_fixture(scope="function")
async def crawler():
    """返回一个测试爬虫实例"""
    async with TestCrawler() as _crawler:
        yield _crawler

@pytest.fixture(autouse=True)
def reset_circuit_breaker():
    """重置断路器状态"""
    CircuitBreaker.reset_all()

class TestCrawler(BaseCrawler):
    """测试用爬虫类"""
    
    def __init__(self):
        """初始化"""
        config = {'platform_name': 'test'}
        super().__init__(config)
        self.platform = config['platform_name']
    
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

class TestBaseCrawler:
    """基础爬虫测试类"""

    @pytest.mark.asyncio
    async def test_initialization(self, crawler):
        """测试爬虫初始化"""
        assert crawler.platform == "test"
        # 不再比较headers，因为它们是随机生成的
        assert isinstance(crawler.headers, dict)
        assert isinstance(crawler.cookie_manager, CookieManager)
        assert isinstance(crawler.proxy_manager, ProxyManager)
        assert isinstance(crawler.rate_limiter, RateLimiter)

    @pytest.mark.asyncio
    async def test_request_retry(self, crawler):
        """测试请求重试机制"""
        # 模拟请求失败
        with patch('aiohttp.ClientSession.request') as mock_request:
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_request.return_value.__aenter__.return_value = mock_response
            
            result = await crawler.request('https://test.com')
            
            # 验证重试次数
            assert mock_request.call_count == 3
            assert result is None

    @pytest.mark.asyncio
    async def test_request_success(self, crawler):
        """测试请求成功"""
        test_data = {'key': 'value'}
        
        # 模拟请求成功
        with patch('aiohttp.ClientSession.request') as mock_request:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = test_data
            mock_request.return_value.__aenter__.return_value = mock_response
            
            result = await crawler.request('https://test.com')
            
            assert result == test_data
            assert mock_request.call_count == 1

    @pytest.mark.asyncio
    async def test_rate_limit(self, crawler):
        """测试请求频率限制"""
        test_data = {'key': 'value'}
        
        # 模拟请求成功
        with patch('aiohttp.ClientSession.request') as mock_request:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = test_data
            mock_request.return_value.__aenter__.return_value = mock_response
            
            start_time = datetime.now()
            
            # 连续发送3个请求
            for _ in range(3):
                await crawler.request('https://test.com')
                
            duration = (datetime.now() - start_time).total_seconds()
            
            # 验证是否遵守了频率限制（默认1秒1个请求）
            # 由于系统调度和其他因素的影响，我们使用一个较小的值
            assert duration >= 1.8  # 允许0.2秒的误差

    @pytest.mark.asyncio
    async def test_proxy_usage(self, crawler):
        """测试代理使用"""
        test_proxy = "http://test.proxy:8080"
        
        # 模拟代理获取
        with patch.object(ProxyManager, 'get_proxy', return_value=test_proxy):
            with patch('aiohttp.ClientSession.request') as mock_request:
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = {}
                mock_request.return_value.__aenter__.return_value = mock_response
                
                await crawler.request('https://test.com')
                
                # 验证是否使用了代理
                call_kwargs = mock_request.call_args[1]
                assert call_kwargs['proxy'] == test_proxy

    @pytest.mark.asyncio
    async def test_cookie_usage(self, crawler):
        """测试Cookie使用"""
        test_cookies = {'session': 'test123'}
        
        # 模拟Cookie获取
        with patch.object(CookieManager, 'get_cookies', return_value=test_cookies):
            with patch('aiohttp.ClientSession.request') as mock_request:
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = {}
                mock_request.return_value.__aenter__.return_value = mock_response
                
                await crawler.request('https://test.com')
                
                # 验证是否使用了Cookie
                call_kwargs = mock_request.call_args[1]
                assert call_kwargs['cookies'] == test_cookies

    @pytest.mark.asyncio
    async def test_headers_usage(self, crawler):
        """测试请求头使用"""
        test_headers = {
            'User-Agent': 'test-ua',
            'Accept': 'test-accept',
            'Accept-Language': 'test-lang'
        }
        
        with patch.object(HeadersManager, 'get_headers', return_value=test_headers):
            with patch('aiohttp.ClientSession.request') as mock_request:
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = {}
                mock_request.return_value.__aenter__.return_value = mock_response
                
                await crawler.request('https://test.com')
                
                # 验证是否使用了正确的请求头
                call_kwargs = mock_request.call_args[1]
                assert call_kwargs['headers'] == test_headers

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """测试上下文管理器"""
        crawler = None
        try:
            async with TestCrawler() as crawler:
                assert crawler.session is not None
                # 发送测试请求
                with patch('aiohttp.ClientSession.request') as mock_request:
                    mock_response = AsyncMock()
                    mock_response.status = 200
                    mock_response.json.return_value = {}
                    mock_request.return_value.__aenter__.return_value = mock_response
                    
                    await crawler.request('https://test.com')
        finally:
            if crawler and crawler.session:
                await crawler.session.close()
                crawler.session = None
                
        # 验证session是否已关闭
        assert crawler.session is None

    @pytest.mark.asyncio
    async def test_request_timeout(self, crawler):
        """测试请求超时"""
        with patch('aiohttp.ClientSession.request') as mock_request:
            mock_request.side_effect = asyncio.TimeoutError()
            
            result = await crawler.request('https://test.com')
            assert result is None
            assert mock_request.call_count == 3  # 验证重试次数

    @pytest.mark.asyncio
    async def test_request_network_error(self, crawler):
        """测试网络错误"""
        with patch('aiohttp.ClientSession.request') as mock_request:
            mock_request.side_effect = ConnectionError()
            
            result = await crawler.request('https://test.com')
            assert result is None
            assert mock_request.call_count == 3  # 验证重试次数

    @pytest.mark.asyncio
    async def test_request_invalid_json(self, crawler):
        """测试无效JSON响应"""
        with patch('aiohttp.ClientSession.request') as mock_request:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.side_effect = ValueError()
            mock_request.return_value.__aenter__.return_value = mock_response
            
            result = await crawler.request('https://test.com')
            assert result is None

    @pytest.mark.asyncio
    async def test_request_with_custom_headers(self, crawler):
        """测试自定义请求头"""
        custom_headers = {'Custom-Header': 'test-value'}
        
        with patch('aiohttp.ClientSession.request') as mock_request:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {}
            mock_request.return_value.__aenter__.return_value = mock_response
            
            await crawler.request('https://test.com', headers=custom_headers)
            
            call_kwargs = mock_request.call_args[1]
            assert call_kwargs['headers']['Custom-Header'] == 'test-value'

    @pytest.mark.asyncio
    async def test_request_with_params(self, crawler):
        """测试URL参数"""
        test_params = {'key': 'value'}
        
        with patch('aiohttp.ClientSession.request') as mock_request:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {}
            mock_request.return_value.__aenter__.return_value = mock_response
            
            await crawler.request('https://test.com', params=test_params)
            
            call_kwargs = mock_request.call_args[1]
            assert call_kwargs['params'] == test_params

    @pytest.mark.asyncio
    async def test_request_with_data(self, crawler):
        """测试POST数据"""
        test_data = {'key': 'value'}
        
        with patch('aiohttp.ClientSession.request') as mock_request:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {}
            mock_request.return_value.__aenter__.return_value = mock_response
            
            await crawler.request('https://test.com', method='POST', data=test_data)
            
            call_kwargs = mock_request.call_args[1]
            assert call_kwargs['json'] == test_data

    @pytest.mark.asyncio
    async def test_request_with_invalid_url(self, crawler):
        """测试无效URL"""
        with pytest.raises(ValueError):
            await crawler.request('invalid-url')

    @pytest.mark.asyncio
    async def test_request_with_invalid_method(self, crawler):
        """测试无效请求方法"""
        with pytest.raises(ValueError):
            await crawler.request('https://test.com', method='INVALID')

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, crawler):
        """测试并发请求"""
        test_data = {'key': 'value'}
        
        with patch('aiohttp.ClientSession.request') as mock_request:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = test_data
            mock_request.return_value.__aenter__.return_value = mock_response
            
            # 并发发送多个请求
            tasks = [
                crawler.request('https://test.com')
                for _ in range(5)
            ]
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 5
            assert all(result == test_data for result in results) 