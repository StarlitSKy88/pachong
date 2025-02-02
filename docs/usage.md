# 使用说明

## 目录

1. [系统概述](#系统概述)
2. [环境准备](#环境准备)
3. [快速开始](#快速开始)
4. [功能使用](#功能使用)
5. [常见问题](#常见问题)

## 系统概述

本系统是一个多平台内容采集和生成系统，支持以下主要功能：

- 多平台内容采集（小红书、B站）
- 内容分析和质量评估
- 自动化内容生成（小红书、网页、播客）
- 系统监控和告警

## 环境准备

### 系统要求

- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- Chrome/Chromium（用于网页截图）

### 安装步骤

1. 克隆代码仓库：
```bash
git clone <repository_url>
cd <project_directory>
```

2. 创建并激活虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\\Scripts\\activate  # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 配置环境变量：
```bash
cp .env.example .env
# 编辑 .env 文件，填写必要的配置信息
```

5. 初始化数据库：
```bash
alembic upgrade head
```

## 快速开始

### 启动系统

1. 启动主服务：
```bash
python main.py
```

2. 启动监控服务：
```bash
python monitor.py
```

### 基本使用流程

1. 创建爬虫任务：
```bash
curl -X POST http://localhost:8000/api/v1/crawlers/tasks \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "xhs",
    "task_type": "search",
    "params": {
      "keyword": "搜索关键词",
      "max_pages": 10
    }
  }'
```

2. 查看采集结果：
```bash
curl http://localhost:8000/api/v1/contents?platform=xhs \
  -H "Authorization: Bearer <your_token>"
```

3. 生成内容：
```bash
curl -X POST http://localhost:8000/api/v1/contents/generate \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "source_content_ids": ["id1", "id2"],
    "output_format": "xhs",
    "params": {
      "title": "标题",
      "tags": ["标签1", "标签2"]
    }
  }'
```

## 功能使用

### 内容采集

#### 小红书采集

支持以下采集方式：
- 关键词搜索
- 用户主页
- 标签页面
- 相关推荐

配置参数：
```json
{
  "max_pages": 10,  // 最大页数
  "min_likes": 100,  // 最小点赞数
  "min_collects": 50,  // 最小收藏数
  "date_range": "7d"  // 时间范围：1d, 7d, 30d, all
}
```

#### B站采集

支持以下采集方式：
- 视频搜索
- UP主主页
- 专栏文章
- 动态内容

配置参数：
```json
{
  "max_pages": 10,  // 最大页数
  "order": "pubdate",  // 排序方式：pubdate（发布时间）, click（点击量）
  "duration": 0,  // 视频时长：0（全部）, 1（<10分钟）, 2（10-30分钟）, 3（30-60分钟）, 4（>60分钟）
  "date_range": "7d"  // 时间范围：1d, 7d, 30d, all
}
```

### 内容生成

#### 小红书内容

生成参数：
```json
{
  "title": "标题",
  "tags": ["标签1", "标签2"],
  "style": "清新/文艺/商务",
  "image_count": 4,  // 图片数量
  "text_length": "medium"  // 文本长度：short/medium/long
}
```

#### 网页内容

生成参数：
```json
{
  "title": "标题",
  "template": "blog/news/product",
  "sections": ["intro", "main", "summary"],
  "include_images": true
}
```

#### 播客内容

生成参数：
```json
{
  "title": "标题",
  "duration": "180",  // 时长（秒）
  "background_music": true,
  "voice_type": "female"  // 声音类型：male/female
}
```

### 系统监控

#### 监控指标

- CPU使用率
- 内存使用率
- 磁盘使用率
- 任务队列长度
- API响应时间
- 错误率

#### 告警规则

示例配置：
```json
{
  "cpu_usage": {
    "threshold": 80,
    "duration": "5m",
    "severity": "warning"
  },
  "error_rate": {
    "threshold": 5,
    "duration": "1m",
    "severity": "critical"
  }
}
```

## 常见问题

### 1. 采集失败

可能原因：
- 网络连接问题
- IP被封禁
- 目标网站改版
- 配置参数错误

解决方案：
1. 检查网络连接
2. 更换代理IP
3. 更新爬虫规则
4. 验证配置参数

### 2. 内容生成失败

可能原因：
- 源内容质量不足
- API限额用尽
- 模型服务异常
- 参数配置错误

解决方案：
1. 调整源内容筛选条件
2. 检查API配额
3. 重试生成请求
4. 验证生成参数

### 3. 系统性能问题

可能原因：
- 资源不足
- 并发任务过多
- 数据库性能瓶颈
- 缓存失效

解决方案：
1. 增加系统资源
2. 调整并发限制
3. 优化数据库查询
4. 检查缓存配置 