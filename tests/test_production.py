"""生产环境测试"""
import asyncio
import os
from datetime import datetime
from loguru import logger

from src.database.sqlite_storage import SQLiteStorage
from src.database.mongo_storage import MongoStorage
from src.database.cache_storage import CacheStorage, CachedStorage
from src.monitor.performance_monitor import PerformanceMonitor
from src.monitor.business_monitor import BusinessMonitor
from src.crawlers.base_crawler import BaseCrawler

async def setup_storage():
    """初始化存储"""
    logger.info("初始化存储系统...")
    
    # SQLite存储
    sqlite = SQLiteStorage('data/crawler.db')
    await sqlite.init()
    
    # MongoDB存储
    mongo = MongoStorage(
        mongo_url='mongodb://localhost:27017',
        database='crawler',
        collection='contents'
    )
    await mongo.init()
    
    # Redis缓存
    cache = CacheStorage('redis://localhost')
    await cache.init()
    
    # 带缓存的存储
    storage = CachedStorage(mongo, cache)
    
    return storage

async def setup_monitor(storage):
    """初始化监控"""
    logger.info("初始化监控系统...")
    
    # 性能监控
    perf_monitor = PerformanceMonitor()
    
    # 业务监控
    biz_monitor = BusinessMonitor(storage)
    
    # 添加告警处理
    async def alert_handler(alert):
        logger.warning(f"收到告警: [{alert.level}] {alert.name} - {alert.message}")
        
    perf_monitor.add_alert_handler(alert_handler)
    biz_monitor.add_alert_handler(alert_handler)
    
    # 启动监控
    await perf_monitor.start()
    await biz_monitor.start()
    
    return perf_monitor, biz_monitor

async def test_crawler(storage):
    """测试爬虫"""
    logger.info("开始爬虫测试...")
    
    # 测试数据
    test_data = {
        'content': {
            'title': '测试内容',
            'text': '这是一条测试数据'
        },
        'source': 'test',
        'created_at': datetime.now()
    }
    
    # 保存数据
    success = await storage.save(test_data)
    logger.info(f"保存测试数据: {'成功' if success else '失败'}")
    
    # 查询数据
    saved_data = await storage.get(test_data['id'])
    logger.info(f"查询数据: {saved_data is not None}")
    
    # 更新数据
    test_data['content']['title'] = '更新的标题'
    success = await storage.update(test_data['id'], test_data)
    logger.info(f"更新数据: {'成功' if success else '失败'}")
    
    # 列出数据
    items = await storage.list(
        filter={'source': 'test'},
        sort=[('created_at', 'DESC')],
        limit=10
    )
    logger.info(f"查询到 {len(items)} 条数据")
    
    return True

async def test_monitor(perf_monitor, biz_monitor):
    """测试监控"""
    logger.info("开始监控测试...")
    
    # 等待采集数据
    await asyncio.sleep(10)
    
    # 检查性能指标
    cpu_metrics = perf_monitor.get_metrics('cpu_percent')
    memory_metrics = perf_monitor.get_metrics('memory_percent')
    logger.info(f"CPU使用率: {cpu_metrics[-1].value if cpu_metrics else 'N/A'}%")
    logger.info(f"内存使用率: {memory_metrics[-1].value if memory_metrics else 'N/A'}%")
    
    # 检查业务指标
    stats = await biz_monitor.get_statistics()
    logger.info(f"总数据量: {stats.get('total_count', 0)}")
    logger.info(f"今日数据量: {stats.get('today_count', 0)}")
    
    # 检查告警
    alerts = perf_monitor.get_alerts()
    if alerts:
        logger.warning(f"存在 {len(alerts)} 个告警")
        for alert in alerts:
            logger.warning(f"- [{alert.level}] {alert.name}: {alert.message}")
            
    return True

async def main():
    """主测试流程"""
    try:
        # 初始化存储
        storage = await setup_storage()
        
        # 初始化监控
        perf_monitor, biz_monitor = await setup_monitor(storage)
        
        # 测试爬虫
        crawler_ok = await test_crawler(storage)
        
        # 测试监控
        monitor_ok = await test_monitor(perf_monitor, biz_monitor)
        
        # 输出结果
        if crawler_ok and monitor_ok:
            logger.success("生产测试通过!")
        else:
            logger.error("生产测试失败!")
            
    except Exception as e:
        logger.error(f"测试过程出错: {str(e)}")
        raise
        
if __name__ == '__main__':
    # 配置日志
    logger.add(
        "logs/test_{time}.log",
        rotation="1 day",
        retention="7 days",
        level="INFO"
    )
    
    # 运行测试
    asyncio.run(main()) 