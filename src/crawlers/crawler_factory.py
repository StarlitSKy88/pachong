"""爬虫工厂模块"""

from typing import Dict, Type, Optional
from .base_crawler import BaseCrawler
from .xhs_crawler import XHSCrawler
from .bilibili_crawler import BiliBiliCrawler
from ..utils.config_manager import ConfigManager
from ..utils.exceptions import ConfigError

class CrawlerFactory:
    """爬虫工厂类"""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """初始化爬虫工厂
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager or ConfigManager()
        self.crawler_classes: Dict[str, Type[BaseCrawler]] = {
            "xhs": XHSCrawler,
            "bilibili": BiliBiliCrawler
        }
        self.crawler_instances: Dict[str, BaseCrawler] = {}
        
    def register_crawler(self, platform: str, crawler_class: Type[BaseCrawler]) -> None:
        """注册爬虫类
        
        Args:
            platform: 平台名称
            crawler_class: 爬虫类
        """
        self.crawler_classes[platform] = crawler_class
        
    def get_crawler(self, platform: str) -> BaseCrawler:
        """获取爬虫实例
        
        Args:
            platform: 平台名称
            
        Returns:
            BaseCrawler: 爬虫实例
            
        Raises:
            ConfigError: 当平台不存在时
        """
        # 如果实例已存在，直接返回
        if platform in self.crawler_instances:
            return self.crawler_instances[platform]
            
        # 检查平台是否支持
        if platform not in self.crawler_classes:
            raise ConfigError(
                message=f"不支持的平台: {platform}",
                config_key="platform"
            )
            
        # 获取爬虫配置
        crawler_config = self.config_manager.get_nested(f"crawler.{platform}", {})
        
        # 创建爬虫实例
        crawler_class = self.crawler_classes[platform]
        crawler = crawler_class(**crawler_config)
        
        # 缓存实例
        self.crawler_instances[platform] = crawler
        
        return crawler
        
    def get_all_crawlers(self) -> Dict[str, BaseCrawler]:
        """获取所有爬虫实例
        
        Returns:
            Dict[str, BaseCrawler]: 爬虫实例字典
        """
        # 确保所有平台的爬虫都已创建
        for platform in self.crawler_classes:
            if platform not in self.crawler_instances:
                self.get_crawler(platform)
                
        return self.crawler_instances
        
    def clear_instances(self) -> None:
        """清除所有爬虫实例"""
        self.crawler_instances.clear()
        
    async def close_all(self) -> None:
        """关闭所有爬虫实例"""
        for crawler in self.crawler_instances.values():
            await crawler.close()
        self.clear_instances() 