import pytest
import asyncio
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from src.utils.proxy import ProxyManager
from src.utils.cookie import CookieManager
from src.utils.llm_api import query_llm
from src.utils.screenshot_utils import take_screenshot_sync

class TestProxyManager:
    """代理管理器测试"""
    
    @pytest.mark.asyncio
    async def test_get_proxy(self, mock_proxy_list):
        """测试获取代理"""
        with patch('src.utils.proxy.ProxyManager._fetch_proxies') as mock_fetch:
            mock_fetch.return_value = mock_proxy_list
            
            manager = ProxyManager()
            proxy = await manager.get_proxy()
            
            assert proxy is not None
            assert proxy in [p['url'] for p in mock_proxy_list]
    
    @pytest.mark.asyncio
    async def test_report_proxy_status(self, mock_proxy_list):
        """测试报告代理状态"""
        with patch('src.utils.proxy.ProxyManager._fetch_proxies') as mock_fetch:
            mock_fetch.return_value = mock_proxy_list
            
            manager = ProxyManager()
            await manager.get_proxy()  # 初始化代理列表
            
            # 报告成功
            proxy_url = mock_proxy_list[0]['url']
            await manager.report_proxy_status(proxy_url, True)
            proxy = next(p for p in manager.proxies if p['url'] == proxy_url)
            assert proxy['score'] == min(100, mock_proxy_list[0]['score'] + 10)
            
            # 报告失败
            await manager.report_proxy_status(proxy_url, False)
            proxy = next(p for p in manager.proxies if p['url'] == proxy_url)
            assert proxy['score'] == max(0, mock_proxy_list[0]['score'] - 10)
    
    @pytest.mark.asyncio
    async def test_proxy_update_interval(self):
        """测试代理更新间隔"""
        with patch('src.utils.proxy.ProxyManager._fetch_proxies') as mock_fetch:
            mock_fetch.return_value = []
            
            manager = ProxyManager()
            manager.update_interval = timedelta(seconds=1)
            
            # 第一次调用
            await manager._update_proxies()
            assert mock_fetch.call_count == 1
            
            # 间隔内调用
            await manager._update_proxies()
            assert mock_fetch.call_count == 1
            
            # 等待间隔
            await asyncio.sleep(1)
            
            # 间隔后调用
            await manager._update_proxies()
            assert mock_fetch.call_count == 2

class TestCookieManager:
    """Cookie管理器测试"""
    
    @pytest.mark.asyncio
    async def test_get_cookies(self, mock_cookies):
        """测试获取Cookie"""
        with patch('src.utils.cookie.CookieManager._fetch_cookies_from_api') as mock_fetch:
            mock_fetch.return_value = {'test.com': mock_cookies}
            
            manager = CookieManager('test_platform')
            cookies = await manager.get_cookies('test.com')
            
            assert cookies == mock_cookies
    
    @pytest.mark.asyncio
    async def test_refresh_cookies(self, mock_cookies):
        """测试刷新Cookie"""
        with patch('src.utils.cookie.CookieManager._fetch_cookies_from_api') as mock_fetch:
            mock_fetch.return_value = {'test.com': mock_cookies}
            
            manager = CookieManager('test_platform')
            await manager.get_cookies('test.com')  # 初始化Cookie
            
            # 修改返回值
            new_cookies = {'session_id': 'new_session'}
            mock_fetch.return_value = {'test.com': new_cookies}
            
            # 刷新Cookie
            await manager.refresh_cookies()
            cookies = await manager.get_cookies('test.com')
            
            assert cookies == new_cookies
    
    @pytest.mark.asyncio
    async def test_cookie_update_interval(self):
        """测试Cookie更新间隔"""
        with patch('src.utils.cookie.CookieManager._fetch_cookies_from_api') as mock_fetch:
            mock_fetch.return_value = {}
            
            manager = CookieManager('test_platform')
            manager.update_interval = timedelta(seconds=1)
            
            # 第一次调用
            await manager._update_cookies()
            assert mock_fetch.call_count == 1
            
            # 间隔内调用
            await manager._update_cookies()
            assert mock_fetch.call_count == 1
            
            # 等待间隔
            await asyncio.sleep(1)
            
            # 间隔后调用
            await manager._update_cookies()
            assert mock_fetch.call_count == 2

class TestLLMAPI:
    """LLM API测试"""
    
    @pytest.mark.asyncio
    async def test_query_llm(self, mock_llm_response):
        """测试查询LLM"""
        with patch('src.utils.llm_api.openai.ChatCompletion.acreate') as mock_create:
            mock_create.return_value = MagicMock(
                choices=[MagicMock(message=MagicMock(content=str(mock_llm_response)))]
            )
            
            response = await query_llm(
                prompt="Test prompt",
                provider="openai"
            )
            
            assert response == str(mock_llm_response)
            mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_query_llm_with_image(self, mock_llm_response):
        """测试带图片查询LLM"""
        with patch('src.utils.llm_api.openai.ChatCompletion.acreate') as mock_create:
            mock_create.return_value = MagicMock(
                choices=[MagicMock(message=MagicMock(content=str(mock_llm_response)))]
            )
            
            response = await query_llm(
                prompt="Test prompt",
                provider="openai",
                image_path="test.jpg"
            )
            
            assert response == str(mock_llm_response)
            mock_create.assert_called_once()
            
            # 验证调用参数包含图片
            args = mock_create.call_args[1]
            assert any('image' in str(msg) for msg in args['messages'])
    
    @pytest.mark.asyncio
    async def test_query_llm_retry(self, mock_llm_response):
        """测试LLM重试"""
        with patch('src.utils.llm_api.openai.ChatCompletion.acreate') as mock_create:
            # 前两次调用失败，第三次成功
            mock_create.side_effect = [
                Exception("API error"),
                Exception("API error"),
                MagicMock(choices=[MagicMock(message=MagicMock(content=str(mock_llm_response)))])
            ]
            
            response = await query_llm(
                prompt="Test prompt",
                provider="openai",
                max_retries=3
            )
            
            assert response == str(mock_llm_response)
            assert mock_create.call_count == 3

class TestScreenshotUtils:
    """截图工具测试"""
    
    def test_take_screenshot(self):
        """测试生成截图"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Page</title>
            <style>
                body { background: white; }
            </style>
        </head>
        <body>
            <h1>Test Content</h1>
        </body>
        </html>
        """
        
        screenshot = take_screenshot_sync(
            html_content=html_content,
            width=800,
            height=600
        )
        
        assert screenshot is not None
        assert isinstance(screenshot, str)
        assert screenshot.endswith('.png')
    
    def test_take_screenshot_with_css(self):
        """测试带CSS生成截图"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Page</title>
        </head>
        <body>
            <h1>Test Content</h1>
        </body>
        </html>
        """
        
        css_content = """
        body {
            background: #f0f0f0;
            padding: 20px;
        }
        h1 {
            color: #333;
            font-family: Arial;
        }
        """
        
        screenshot = take_screenshot_sync(
            html_content=html_content,
            css_content=css_content,
            width=800,
            height=600
        )
        
        assert screenshot is not None
        assert isinstance(screenshot, str)
        assert screenshot.endswith('.png')
    
    def test_take_screenshot_error(self):
        """测试截图错误处理"""
        with pytest.raises(ValueError):
            take_screenshot_sync(
                html_content="",  # 空内容
                width=800,
                height=600
            ) 