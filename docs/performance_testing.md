# 性能测试指南

## 概述

本文档描述了项目的性能测试框架和使用方法。性能测试主要包括以下几个方面：

1. 爬虫性能测试
2. 任务队列性能测试
3. 数据导出性能测试

## 测试环境要求

- Python 3.10+
- pytest
- psutil
- asyncio

## 测试配置

性能测试的配置文件位于 `tests/performance/performance_config.py`，包含以下配置：

### 爬虫性能配置
```python
CRAWLER_CONFIG = {
    "max_duration": 60,  # 最大执行时间（秒）
    "max_cpu_average": 80,  # 最大平均CPU使用率（%）
    "max_memory": 80,  # 最大内存使用率（%）
    "max_concurrent": 10,  # 最大并发数
    "test_keywords": ["AI开发", "独立开发", "Cursor"],  # 测试关键词
    "time_ranges": ["24h", "1w", "1m"],  # 测试时间范围
    "item_limits": [10, 50, 100]  # 测试数据量
}
```

### 任务队列性能配置
```python
TASK_QUEUE_CONFIG = {
    "max_duration": 10,  # 最大执行时间（秒）
    "max_cpu_average": 50,  # 最大平均CPU使用率（%）
    "max_memory": 50,  # 最大内存使用率（%）
    "max_workers": [1, 3, 5, 10],  # 测试工作线程数
    "task_counts": [10, 100, 1000],  # 测试任务数量
    "task_priorities": [0, 1, 2]  # 测试任务优先级
}
```

### 导出工具性能配置
```python
EXPORTER_CONFIG = {
    "max_duration": 5,  # 最大执行时间（秒）
    "max_cpu_average": 70,  # 最大平均CPU使用率（%）
    "max_memory": 70,  # 最大内存使用率（%）
    "max_io_write": 10 * 1024 * 1024,  # 最大写入字节数（10MB）
    "data_sizes": [100, 1000, 10000],  # 测试数据量
    "export_formats": ["json", "csv", "excel", "markdown", "html"]  # 导出格式
}
```

## 运行测试

### 命令行选项

```bash
python tests/performance/run_performance_tests.py [options]

选项：
  --tests TEST [TEST ...]  要运行的测试名称列表
  --no-save               不保存测试结果
  --report               生成测试报告
```

### 示例

1. 运行所有性能测试：
```bash
python tests/performance/run_performance_tests.py --report
```

2. 运行特定测试：
```bash
python tests/performance/run_performance_tests.py --tests test_crawler_performance test_task_queue_performance --report
```

3. 只运行测试，不保存结果：
```bash
python tests/performance/run_performance_tests.py --no-save
```

## 测试结果

测试结果保存在 `test_results/performance` 目录下，包括：

1. 性能测试结果（JSON格式）：
```json
{
    "timestamp": "2024-03-27T10:00:00",
    "test_names": ["test_crawler_performance"],
    "exit_code": 0,
    "metrics": {
        "test_crawler_performance": {
            "duration": 45.2,
            "cpu": {
                "average": 65.3,
                "max": 78.9
            },
            "memory": {
                "average": 45.6,
                "max": 68.7
            },
            "io": {
                "read": 1024576,
                "write": 512000
            }
        }
    }
}
```

2. 性能测试报告（Markdown格式）：
```markdown
# 性能测试报告

## 测试时间: 2024-03-27T10:00:00
## 测试范围: ["test_crawler_performance"]
## 测试结果: 成功

## 性能指标

### test_crawler_performance
执行时间: 45.20秒
CPU使用率: 平均65.3%, 最大78.9%
内存使用率: 平均45.6%, 最大68.7%
IO读取: 1000.0KB
IO写入: 500.0KB
```

## 性能指标说明

1. 执行时间：测试完成所需的总时间
2. CPU使用率：测试过程中的CPU使用情况
   - 平均值：整个测试过程的平均CPU使用率
   - 最大值：测试过程中的峰值CPU使用率
3. 内存使用率：测试过程中的内存使用情况
   - 平均值：整个测试过程的平均内存使用率
   - 最大值：测试过程中的峰值内存使用率
4. IO统计：测试过程中的磁盘IO情况
   - 读取：总读取字节数
   - 写入：总写入字节数

## 性能优化建议

1. 爬虫性能优化：
   - 使用异步IO和并发处理
   - 优化请求频率和间隔
   - 实现请求重试和错误处理
   - 使用代理池和Cookie池

2. 任务队列优化：
   - 调整工作线程数
   - 优化任务优先级策略
   - 实现任务批处理
   - 添加任务超时处理

3. 数据导出优化：
   - 使用流式处理大数据
   - 实现数据压缩
   - 优化文件写入方式
   - 添加缓存机制

## 常见问题

1. 测试超时
   - 检查网络连接
   - 调整超时时间
   - 减少测试数据量
   - 优化并发设置

2. 内存使用过高
   - 使用生成器处理大数据
   - 及时释放资源
   - 减少数据缓存
   - 优化数据结构

3. CPU使用率过高
   - 减少并发数量
   - 优化计算密集操作
   - 添加任务节流
   - 使用性能分析工具

4. IO操作频繁
   - 使用批量处理
   - 实现数据缓冲
   - 优化文件操作
   - 使用异步IO 