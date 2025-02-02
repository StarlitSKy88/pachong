"""爬虫示例"""

import os
import asyncio
from datetime import datetime
from src.utils.config_manager import ConfigManager
from src.utils.dependency_injector import DependencyContainer
from src.crawlers.crawler_factory import CrawlerFactory
from src.monitor.crawler_monitor import CrawlerMonitor
from src.utils.logger import LogManager

async def main():
    """主函数"""
    try:
        # 初始化配置管理器
        config_manager = ConfigManager()
        config_manager.load_env()
        
        # 初始化日志管理器
        log_manager = LogManager(
            name="crawler",
            level=config_manager.get_env("LOG_LEVEL", "INFO"),
            log_dir=config_manager.get_env("LOG_DIR", "logs")
        )
        logger = log_manager.get_logger()
        
        # 初始化依赖容器
        container = DependencyContainer()
        container.register_instance("config_manager", config_manager)
        container.register_instance("log_manager", log_manager)
        
        # 初始化爬虫工厂
        crawler_factory = CrawlerFactory(config_manager)
        container.register_instance("crawler_factory", crawler_factory)
        
        # 初始化监控器
        monitor = CrawlerMonitor()
        monitor.alert_webhook = config_manager.get_env("ALERT_WEBHOOK")
        await monitor.start()
        container.register_instance("monitor", monitor)
        
        try:
            # 设置关键词
            keywords = ["AI开发", "独立开发", "Cursor"]
            time_range = "24h"
            limit = 10
            
            # 获取爬虫实例
            xhs_crawler = crawler_factory.get_crawler("xhs")
            bilibili_crawler = crawler_factory.get_crawler("bilibili")
            
            # 采集内容
            logger.info("开始采集内容...")
            
            # 小红书采集
            logger.info("采集小红书内容:")
            xhs_results = await xhs_crawler.crawl(
                keywords=keywords,
                time_range=time_range,
                limit=limit
            )
            logger.info(f"采集到 {len(xhs_results)} 条小红书内容")
            
            # B站采集
            logger.info("采集B站内容:")
            bilibili_results = await bilibili_crawler.crawl(
                keywords=keywords,
                time_range=time_range,
                limit=limit
            )
            logger.info(f"采集到 {len(bilibili_results)} 条B站内容")
            
            # 输出监控指标
            logger.info("监控指标:")
            metrics = monitor.get_metrics()
            logger.info(f"代理状态: {metrics.get('proxy', {})}")
            logger.info(f"Cookie状态: {metrics.get('cookie', {})}")
            logger.info(f"内容统计: {metrics.get('content', {})}")
            
            # 输出告警信息
            logger.info("告警信息:")
            alerts = monitor.get_alerts()
            for alert in alerts:
                logger.warning(
                    f"[{alert['level']}] {alert['type']}: {alert['message']}"
                )
                
        finally:
            # 关闭爬虫实例
            await crawler_factory.close_all()
            
            # 停止监控
            await monitor.stop()
            
    except Exception as e:
        logger.error(f"发生错误: {str(e)}", exc_info=True)
        raise
        
if __name__ == "__main__":
    # 运行示例
    asyncio.run(main()) 