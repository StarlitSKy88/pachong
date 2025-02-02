"""性能测试配置"""

# 爬虫性能配置
CRAWLER_CONFIG = {
    "max_duration": 60,  # 最大执行时间（秒）
    "max_cpu_average": 80,  # 最大平均CPU使用率（%）
    "max_memory": 80,  # 最大内存使用率（%）
    "max_concurrent": 10,  # 最大并发数
    "test_keywords": ["AI开发", "独立开发", "Cursor"],  # 测试关键词
    "time_ranges": ["24h", "1w", "1m"],  # 测试时间范围
    "item_limits": [10, 50, 100]  # 测试数据量
}

# 任务队列性能配置
TASK_QUEUE_CONFIG = {
    "max_duration": 10,  # 最大执行时间（秒）
    "max_cpu_average": 50,  # 最大平均CPU使用率（%）
    "max_memory": 50,  # 最大内存使用率（%）
    "max_workers": [1, 3, 5, 10],  # 测试工作线程数
    "task_counts": [10, 100, 1000],  # 测试任务数量
    "task_priorities": [0, 1, 2]  # 测试任务优先级
}

# 导出工具性能配置
EXPORTER_CONFIG = {
    "max_duration": 5,  # 最大执行时间（秒）
    "max_cpu_average": 70,  # 最大平均CPU使用率（%）
    "max_memory": 70,  # 最大内存使用率（%）
    "max_io_write": 10 * 1024 * 1024,  # 最大写入字节数（10MB）
    "data_sizes": [100, 1000, 10000],  # 测试数据量
    "export_formats": ["json", "csv", "excel", "markdown", "html"]  # 导出格式
}

# 监控配置
MONITOR_CONFIG = {
    "metrics_interval": 1.0,  # 指标收集间隔（秒）
    "report_interval": 5.0,  # 报告生成间隔（秒）
    "save_metrics": True,  # 是否保存指标数据
    "metrics_file": "performance_metrics.json"  # 指标数据文件
} 