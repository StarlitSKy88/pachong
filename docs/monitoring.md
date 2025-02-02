# 监控文档

## 一、监控架构

### 1.1 整体架构

```
                    [Grafana]
                        |
                  [Prometheus]
                        |
    +------------------+------------------+
    |                  |                  |
[应用指标]        [系统指标]        [业务指标]
    |                  |                  |
    v                  v                  v
FastAPI           Node Exporter     自定义Exporter
Celery           cAdvisor
```

### 1.2 监控组件

1. 指标采集
   - Prometheus: 时序数据库
   - Node Exporter: 系统指标
   - cAdvisor: 容器指标

2. 可视化
   - Grafana: 监控面板
   - Alertmanager: 告警管理

3. 日志管理
   - ELK Stack: 日志收集和分析
   - Filebeat: 日志采集

## 二、监控指标

### 2.1 系统指标

1. 主机监控
```yaml
# node_exporter指标
- CPU使用率
  - node_cpu_seconds_total
  - node_cpu_guest_seconds_total

- 内存使用
  - node_memory_MemTotal_bytes
  - node_memory_MemFree_bytes
  - node_memory_Cached_bytes

- 磁盘使用
  - node_disk_io_time_seconds_total
  - node_disk_read_bytes_total
  - node_disk_written_bytes_total

- 网络流量
  - node_network_receive_bytes_total
  - node_network_transmit_bytes_total
```

2. 容器监控
```yaml
# cAdvisor指标
- 容器CPU
  - container_cpu_usage_seconds_total
  - container_cpu_system_seconds_total

- 容器内存
  - container_memory_usage_bytes
  - container_memory_working_set_bytes

- 容器网络
  - container_network_receive_bytes_total
  - container_network_transmit_bytes_total
```

### 2.2 应用指标

1. API性能
```python
# FastAPI指标
from prometheus_client import Counter, Histogram

# 请求计数器
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

# 响应时间
request_latency = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

@app.middleware("http")
async def metrics_middleware(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    request_count.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    request_latency.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response
```

2. 任务监控
```python
# Celery指标
from prometheus_client import Gauge

# 任务队列长度
queue_length = Gauge(
    'celery_queue_length',
    'Number of tasks in queue',
    ['queue']
)

# 工作进程数
worker_count = Gauge(
    'celery_worker_count',
    'Number of celery workers',
    ['queue']
)

# 任务执行时间
task_duration = Histogram(
    'celery_task_duration_seconds',
    'Task execution duration',
    ['task_name']
)
```

### 2.3 业务指标

1. 爬虫指标
```python
# 爬虫性能指标
- 爬取速率
  crawler_requests_per_minute{crawler="xhs"}
  
- 成功率
  crawler_success_rate{crawler="xhs"}
  
- 数据量
  crawler_data_size_bytes{crawler="xhs"}
```

2. 内容指标
```python
# 内容处理指标
- 处理速率
  content_process_rate{type="text"}
  
- 生成质量
  content_quality_score{format="xhs"}
  
- 错误率
  content_error_rate{stage="generation"}
```

## 三、告警规则

### 3.1 系统告警

1. 资源告警
```yaml
# prometheus/rules/system.yml
groups:
- name: system
  rules:
  - alert: HighCPUUsage
    expr: avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) > 0.8
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: High CPU usage

  - alert: HighMemoryUsage
    expr: node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes * 100 < 10
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: Low memory available
```

2. 服务告警
```yaml
# prometheus/rules/service.yml
groups:
- name: service
  rules:
  - alert: ServiceDown
    expr: up == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Service {{ $labels.job }} is down"

  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: High error rate detected
```

### 3.2 业务告警

1. 爬虫告警
```yaml
# prometheus/rules/crawler.yml
groups:
- name: crawler
  rules:
  - alert: CrawlerSlowDown
    expr: rate(crawler_requests_per_minute[5m]) < 10
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: Crawler is slow

  - alert: HighFailureRate
    expr: crawler_success_rate < 0.9
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: High crawler failure rate
```

2. 内容告警
```yaml
# prometheus/rules/content.yml
groups:
- name: content
  rules:
  - alert: LowQualityContent
    expr: avg_over_time(content_quality_score[1h]) < 0.7
    for: 15m
    labels:
      severity: warning
    annotations:
      summary: Low content quality detected

  - alert: HighGenerationError
    expr: rate(content_error_rate[5m]) > 0.1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: High content generation error rate
```

## 四、监控面板

### 4.1 系统面板

1. 主机概览
```json
{
  "title": "Host Overview",
  "panels": [
    {
      "title": "CPU Usage",
      "type": "graph",
      "targets": [
        {
          "expr": "rate(node_cpu_seconds_total{mode!='idle'}[5m])"
        }
      ]
    },
    {
      "title": "Memory Usage",
      "type": "graph",
      "targets": [
        {
          "expr": "node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes"
        }
      ]
    }
  ]
}
```

2. 容器监控
```json
{
  "title": "Container Metrics",
  "panels": [
    {
      "title": "Container CPU",
      "type": "graph",
      "targets": [
        {
          "expr": "rate(container_cpu_usage_seconds_total[5m])"
        }
      ]
    },
    {
      "title": "Container Memory",
      "type": "graph",
      "targets": [
        {
          "expr": "container_memory_usage_bytes"
        }
      ]
    }
  ]
}
```

### 4.2 应用面板

1. API监控
```json
{
  "title": "API Metrics",
  "panels": [
    {
      "title": "Request Rate",
      "type": "graph",
      "targets": [
        {
          "expr": "rate(http_requests_total[5m])"
        }
      ]
    },
    {
      "title": "Response Time",
      "type": "heatmap",
      "targets": [
        {
          "expr": "rate(http_request_duration_seconds_bucket[5m])"
        }
      ]
    }
  ]
}
```

2. 任务监控
```json
{
  "title": "Task Metrics",
  "panels": [
    {
      "title": "Queue Length",
      "type": "graph",
      "targets": [
        {
          "expr": "celery_queue_length"
        }
      ]
    },
    {
      "title": "Task Duration",
      "type": "graph",
      "targets": [
        {
          "expr": "rate(celery_task_duration_seconds_sum[5m])"
        }
      ]
    }
  ]
}
```

## 五、日志管理

### 5.1 日志配置

1. 应用日志
```python
# logging配置
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        }
    },
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/app.log',
            'formatter': 'json',
            'maxBytes': 10485760,
            'backupCount': 5
        }
    },
    'loggers': {
        '': {
            'handlers': ['file'],
            'level': 'INFO'
        }
    }
}
```

2. Filebeat配置
```yaml
# filebeat.yml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /app/logs/*.log
  json.keys_under_root: true
  json.add_error_key: true

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  index: "logs-%{[agent.version]}-%{+yyyy.MM.dd}"
```

### 5.2 日志分析

1. Elasticsearch查询
```json
// 错误日志查询
GET logs-*/_search
{
  "query": {
    "bool": {
      "must": [
        { "match": { "level": "ERROR" } },
        { "range": {
            "@timestamp": {
              "gte": "now-1h"
            }
          }
        }
      ]
    }
  }
}
```

2. Kibana可视化
```json
{
  "title": "Error Analysis",
  "type": "visualization",
  "visualization": {
    "type": "line",
    "aggs": [
      {
        "id": "1",
        "type": "count",
        "schema": "metric"
      },
      {
        "id": "2",
        "type": "date_histogram",
        "schema": "segment",
        "params": {
          "field": "@timestamp",
          "interval": "auto"
        }
      }
    ]
  }
}
```

## 六、监控维护

### 6.1 数据保留

1. Prometheus配置
```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  # 数据保留时间
  retention_time: 15d
```

2. 日志轮转
```conf
# logrotate配置
/app/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 www-data www-data
}
```

### 6.2 性能优化

1. Prometheus优化
```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  scrape_timeout: 10s
  evaluation_interval: 15s

storage:
  tsdb:
    retention.time: 15d
    retention.size: 50GB
    wal-compression: true
```

2. Grafana优化
```ini
# grafana.ini
[dashboards]
versions_to_keep = 20

[database]
cache_mode = server
cache_ttl = 3600

[security]
cookie_secure = true
cookie_samesite = strict
``` 