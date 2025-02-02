"""爬虫工厂测试模块"""

import pytest
from unittest.mock import Mock, AsyncMock
from src.crawlers.crawler_factory import CrawlerFactory
from src.crawlers.base_crawler import BaseCrawler
from src.utils.config_manager import ConfigManager
from src.utils.exceptions import ConfigError

class TestCrawler(BaseCrawler):
    """测试用爬虫类"""
    
    async def crawl(self, keywords, time_range="24h", limit=10):
        """测试采集方法"""
        return []
        
    async def parse(self, data):
        """测试解析方法"""
        return data

@pytest.fixture
def config_manager():
    """配置管理器实例"""
    return ConfigManager()

@pytest.fixture
def crawler_factory(config_manager):
    """爬虫工厂实例"""
    return CrawlerFactory(config_manager)

def test_init_crawler_factory(crawler_factory):
    """测试初始化爬虫工厂"""
    assert isinstance(crawler_factory.config_manager, ConfigManager)
    assert "xhs" in crawler_factory.crawler_classes
    assert "bilibili" in crawler_factory.crawler_classes
    assert not crawler_factory.crawler_instances

def test_register_crawler(crawler_factory):
    """测试注册爬虫类"""
    crawler_factory.register_crawler("test", TestCrawler)
    assert "test" in crawler_factory.crawler_classes
    assert crawler_factory.crawler_classes["test"] == TestCrawler

def test_get_crawler(crawler_factory):
    """测试获取爬虫实例"""
    # 注册测试爬虫
    crawler_factory.register_crawler("test", TestCrawler)
    
    # 获取爬虫实例
    crawler = crawler_factory.get_crawler("test")
    assert isinstance(crawler, TestCrawler)
    assert "test" in crawler_factory.crawler_instances
    
    # 再次获取同一个爬虫
    crawler2 = crawler_factory.get_crawler("test")
    assert crawler2 is crawler  # 应该返回相同的实例

def test_get_crawler_not_found(crawler_factory):
    """测试获取不存在的爬虫"""
    with pytest.raises(ConfigError) as exc_info:
        crawler_factory.get_crawler("not_exists")
    assert "不支持的平台" in str(exc_info.value)

def test_get_all_crawlers(crawler_factory):
    """测试获取所有爬虫实例"""
    # 注册测试爬虫
    crawler_factory.register_crawler("test1", TestCrawler)
    crawler_factory.register_crawler("test2", TestCrawler)
    
    # 获取所有爬虫
    crawlers = crawler_factory.get_all_crawlers()
    
    assert len(crawlers) == 4  # xhs, bilibili, test1, test2
    assert all(isinstance(c, BaseCrawler) for c in crawlers.values())
    assert set(crawlers.keys()) == {"xhs", "bilibili", "test1", "test2"}

def test_clear_instances(crawler_factory):
    """测试清除爬虫实例"""
    # 创建一些爬虫实例
    crawler_factory.register_crawler("test", TestCrawler)
    crawler_factory.get_crawler("test")
    assert len(crawler_factory.crawler_instances) == 1
    
    # 清除实例
    crawler_factory.clear_instances()
    assert not crawler_factory.crawler_instances

@pytest.mark.asyncio
async def test_close_all(crawler_factory):
    """测试关闭所有爬虫实例"""
    # 创建Mock爬虫类
    mock_crawler = Mock(spec=BaseCrawler)
    mock_crawler.close = AsyncMock()
    
    # 注册并获取Mock爬虫
    crawler_factory.crawler_instances["test"] = mock_crawler
    
    # 关闭所有爬虫
    await crawler_factory.close_all()
    
    # 验证close方法被调用
    mock_crawler.close.assert_called_once()
    assert not crawler_factory.crawler_instances

def test_crawler_config(crawler_factory, config_manager):
    """测试爬虫配置"""
    # 设置测试配置
    config_manager.config = {
        "crawler": {
            "test": {
                "timeout": 30,
                "retry_times": 3
            }
        }
    }
    
    # 注册测试爬虫
    crawler_factory.register_crawler("test", TestCrawler)
    
    # 获取爬虫实例
    crawler = crawler_factory.get_crawler("test")
    
    # 验证配置是否正确传递
    assert isinstance(crawler, TestCrawler)
    assert crawler.timeout == 30
    assert crawler.retry_times == 3 