import pytest
import asyncio
import time
import psutil
import os
from typing import List, Dict, Any
from datetime import datetime
from src.crawlers.xhs_crawler import XHSCrawler
from src.crawlers.bilibili_crawler import BiliBiliCrawler
from src.utils.task_queue import TaskQueue, Task
from src.utils.exporter import Exporter

class PerformanceMetrics:
    """性能指标收集器"""
    
    def __init__(self):
        """初始化性能指标收集器"""
        self.process = psutil.Process(os.getpid())
        self.start_time = time.time()
        self.end_time = None
        self.cpu_percent = []
        self.memory_percent = []
        self.io_counters = []
        
    def collect(self):
        """收集性能指标"""
        self.cpu_percent.append(self.process.cpu_percent())
        self.memory_percent.append(self.process.memory_percent())
        self.io_counters.append(self.process.io_counters())
        
    def stop(self):
        """停止收集"""
        self.end_time = time.time()
        
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        duration = self.end_time - self.start_time
        
        # CPU使用率
        avg_cpu = sum(self.cpu_percent) / len(self.cpu_percent)
        max_cpu = max(self.cpu_percent)
        
        # 内存使用率
        avg_memory = sum(self.memory_percent) / len(self.memory_percent)
        max_memory = max(self.memory_percent)
        
        # IO统计
        io_read = self.io_counters[-1].read_bytes - self.io_counters[0].read_bytes
        io_write = self.io_counters[-1].write_bytes - self.io_counters[0].write_bytes
        
        return {
            "duration": duration,
            "cpu": {
                "average": avg_cpu,
                "max": max_cpu
            },
            "memory": {
                "average": avg_memory,
                "max": max_memory
            },
            "io": {
                "read": io_read,
                "write": io_write
            }
        }

async def collect_metrics(metrics: PerformanceMetrics, interval: float = 1.0):
    """收集性能指标
    
    Args:
        metrics: 性能指标收集器
        interval: 收集间隔（秒）
    """
    while True:
        metrics.collect()
        await asyncio.sleep(interval)

@pytest.mark.performance
@pytest.mark.asyncio
async def test_crawler_performance():
    """测试爬虫性能"""
    # 初始化性能指标收集器
    metrics = PerformanceMetrics()
    
    # 启动指标收集
    collector = asyncio.create_task(collect_metrics(metrics))
    
    try:
        # 初始化爬虫
        xhs_crawler = XHSCrawler()
        bilibili_crawler = BiliBiliCrawler()
        
        # 设置测试参数
        keywords = ["AI开发", "独立开发", "Cursor"]
        time_range = "24h"
        limit = 10
        
        # 并发采集
        tasks = []
        for keyword in keywords:
            tasks.extend([
                xhs_crawler.crawl([keyword], time_range, limit),
                bilibili_crawler.crawl([keyword], time_range, limit)
            ])
        
        # 执行采集
        results = await asyncio.gather(*tasks)
        
        # 验证结果
        assert len(results) == len(keywords) * 2
        assert all(isinstance(r, list) for r in results)
        assert all(len(r) <= limit for r in results)
        
        # 计算性能指标
        total_items = sum(len(r) for r in results)
        
    finally:
        # 停止指标收集
        collector.cancel()
        metrics.stop()
        
    # 获取性能统计
    stats = metrics.get_stats()
    
    # 验证性能要求
    assert stats["duration"] < 60  # 总耗时不超过60秒
    assert stats["cpu"]["average"] < 80  # 平均CPU使用率不超过80%
    assert stats["memory"]["max"] < 80  # 最大内存使用率不超过80%

@pytest.mark.performance
@pytest.mark.asyncio
async def test_task_queue_performance():
    """测试任务队列性能"""
    # 初始化性能指标收集器
    metrics = PerformanceMetrics()
    
    # 启动指标收集
    collector = asyncio.create_task(collect_metrics(metrics))
    
    try:
        # 初始化任务队列
        queue = TaskQueue(max_workers=3)
        await queue.start()
        
        # 创建测试任务
        async def dummy_task(sleep_time: float = 0.1) -> str:
            await asyncio.sleep(sleep_time)
            return "success"
        
        # 添加任务
        task_count = 100
        for i in range(task_count):
            task = Task(
                task_id=f"task_{i}",
                func=dummy_task,
                args=(0.1,),
                priority=i % 3
            )
            await queue.add_task(task)
        
        # 等待任务完成
        while len(queue.completed_tasks) < task_count:
            await asyncio.sleep(0.1)
            
        # 验证结果
        assert len(queue.completed_tasks) == task_count
        assert all(t.status == "completed" for t in queue.completed_tasks)
        assert all(t.result == "success" for t in queue.completed_tasks)
        
    finally:
        # 停止任务队列
        await queue.stop()
        
        # 停止指标收集
        collector.cancel()
        metrics.stop()
        
    # 获取性能统计
    stats = metrics.get_stats()
    
    # 验证性能要求
    assert stats["duration"] < 10  # 总耗时不超过10秒
    assert stats["cpu"]["average"] < 50  # 平均CPU使用率不超过50%
    assert stats["memory"]["max"] < 50  # 最大内存使用率不超过50%

@pytest.mark.performance
@pytest.mark.asyncio
async def test_exporter_performance():
    """测试导出工具性能"""
    # 初始化性能指标收集器
    metrics = PerformanceMetrics()
    
    # 启动指标收集
    collector = asyncio.create_task(collect_metrics(metrics))
    
    try:
        # 创建测试数据
        data = []
        for i in range(1000):
            data.append({
                "id": i,
                "title": f"测试标题{i}",
                "content": f"测试内容{i}",
                "tags": [f"标签{j}" for j in range(5)],
                "stats": {
                    "views": i * 100,
                    "likes": i * 10,
                    "comments": i * 5
                },
                "create_time": datetime.now().isoformat()
            })
            
        # 初始化导出工具
        exporter = Exporter()
        
        # 导出所有格式
        results = exporter.export_all(data, "performance_test")
        
        # 验证结果
        assert len(results) == 5  # json, csv, excel, markdown, html
        assert all(os.path.exists(f) for f in results.values())
        
    finally:
        # 停止指标收集
        collector.cancel()
        metrics.stop()
        
        # 清理测试文件
        for filepath in results.values():
            if os.path.exists(filepath):
                os.remove(filepath)
                
    # 获取性能统计
    stats = metrics.get_stats()
    
    # 验证性能要求
    assert stats["duration"] < 5  # 总耗时不超过5秒
    assert stats["cpu"]["average"] < 70  # 平均CPU使用率不超过70%
    assert stats["memory"]["max"] < 70  # 最大内存使用率不超过70%
    assert stats["io"]["write"] < 10 * 1024 * 1024  # 写入不超过10MB 