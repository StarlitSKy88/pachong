import asyncio
from datetime import datetime
from .crawler_scheduler import CrawlerScheduler

async def test_crawler_scheduler():
    """测试爬虫调度器"""
    print("Testing Crawler Scheduler...")
    
    # 创建调度器
    scheduler = CrawlerScheduler()
    
    # 添加小红书任务
    xhs_task_id = 'xhs_python_task'
    scheduler.add_crawl_task(
        task_id=xhs_task_id,
        platform='xhs',
        keyword='Python编程',
        schedule='*/5 * * * *'  # 每5分钟执行一次
    )
    
    # 添加B站任务
    bilibili_task_id = 'bilibili_python_task'
    scheduler.add_crawl_task(
        task_id=bilibili_task_id,
        platform='bilibili',
        keyword='Python教程',
        schedule='*/10 * * * *'  # 每10分钟执行一次
    )
    
    # 启动调度器
    scheduler.start()
    print("Scheduler started")
    
    try:
        # 立即执行任务
        print("Executing tasks immediately...")
        await scheduler.execute_job(xhs_task_id)
        await scheduler.execute_job(bilibili_task_id)
        
        # 等待一段时间，让定时任务有机会执行
        print("Waiting for scheduled tasks...")
        await asyncio.sleep(300)  # 等待5分钟
        
        # 获取任务日志
        print("\nTask Logs:")
        xhs_logs = scheduler.get_task_logs(xhs_task_id)
        bilibili_logs = scheduler.get_task_logs(bilibili_task_id)
        
        print("\nXHS Task Logs:")
        for log in xhs_logs:
            print(f"Status: {log['status']}, Start: {log['start_time']}, End: {log['end_time']}")
        
        print("\nBilibili Task Logs:")
        for log in bilibili_logs:
            print(f"Status: {log['status']}, Start: {log['start_time']}, End: {log['end_time']}")
        
        # 获取任务统计
        print("\nTask Statistics:")
        stats = scheduler.get_task_stats(days=1)
        print(f"Type Stats: {stats['type_stats']}")
        print(f"Status Stats: {stats['status_stats']}")
        print(f"Platform Stats: {stats['platform_stats']}")
        
    finally:
        # 关闭调度器
        scheduler.shutdown()
        print("Scheduler shutdown")

if __name__ == "__main__":
    asyncio.run(test_crawler_scheduler()) 