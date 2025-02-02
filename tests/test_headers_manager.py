import pytest
from datetime import datetime, timedelta
from src.utils.headers_manager import HeadersManager

def test_user_agent_rotation():
    """测试User-Agent轮换策略"""
    manager = HeadersManager()
    
    # 获取初始User-Agent
    initial_ua = manager.get_random_user_agent()
    
    # 连续获取99次，应该保持不变
    for _ in range(99):
        assert manager.get_random_user_agent() == initial_ua
    
    # 第100次应该更换
    assert manager.get_random_user_agent() != initial_ua

def test_browser_detection():
    """测试浏览器类型检测"""
    manager = HeadersManager()
    
    # 测试Chrome检测
    chrome_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    assert manager._detect_browser(chrome_ua) == 'chrome'
    
    # 测试Firefox检测
    firefox_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"
    assert manager._detect_browser(firefox_ua) == 'firefox'
    
    # 测试Safari检测
    safari_ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15"
    assert manager._detect_browser(safari_ua) == 'safari'

def test_browser_features():
    """测试浏览器特征生成"""
    manager = HeadersManager()
    
    # 测试Chrome特征
    manager._current_browser = 'chrome'
    features = manager._get_browser_features()
    assert 'sec-ch-ua' in features
    assert 'sec-ch-ua-platform' in features
    assert 'sec-ch-ua-mobile' in features
    
    # 测试Firefox特征
    manager._current_browser = 'firefox'
    features = manager._get_browser_features()
    assert 'sec-ch-ua' not in features
    assert 'sec-fetch-dest' in features
    
    # 测试Safari特征
    manager._current_browser = 'safari'
    features = manager._get_browser_features()
    assert len(features) == 0

def test_headers_consistency():
    """测试请求头的一致性"""
    manager = HeadersManager()
    
    # 获取基础请求头
    headers = manager.get_headers()
    assert "User-Agent" in headers
    assert "Accept" in headers
    assert "Accept-Language" in headers
    
    # 测试小红书请求头
    xhs_headers = manager.get_xiaohongshu_headers()
    assert xhs_headers["Origin"] == "https://www.xiaohongshu.com"
    assert xhs_headers["Referer"] == "https://www.xiaohongshu.com"
    assert "X-Requested-With" in xhs_headers
    
    # 测试B站请求头
    bili_headers = manager.get_bilibili_headers()
    assert bili_headers["Origin"] == "https://www.bilibili.com"
    assert bili_headers["Referer"] == "https://www.bilibili.com"
    assert "X-Requested-With" in bili_headers
    
    # 测试API请求头
    api_headers = manager.get_api_headers()
    assert api_headers["Accept"] == "application/json, text/plain, */*"
    assert api_headers["Content-Type"] == "application/json;charset=UTF-8"
    assert "X-Requested-With" in api_headers

def test_language_rotation():
    """测试Accept-Language轮换"""
    manager = HeadersManager()
    languages = set()
    
    # 获取100次Accept-Language，应该有多个不同的值
    for _ in range(100):
        languages.add(manager.get_random_accept_language())
    
    assert len(languages) > 1

def test_time_based_rotation():
    """测试基于时间的User-Agent轮换"""
    manager = HeadersManager()
    
    # 获取初始User-Agent
    initial_ua = manager.get_random_user_agent()
    
    # 修改上次重置时间为1小时前
    manager._last_reset = datetime.now() - timedelta(hours=1, minutes=1)
    
    # 应该获取新的User-Agent
    assert manager.get_random_user_agent() != initial_ua 