# 入门指南

## 系统概述

本系统提供了强大的内容采集、分析和生成功能，帮助用户高效地处理和利用互联网内容。

## 快速开始

### 1. 基础配置

#### 环境准备
- 安装Python 3.8+
- 安装MongoDB
- 安装Redis
- 安装RabbitMQ

#### 项目配置
1. 克隆项目并安装依赖：
```bash
git clone [项目地址]
cd [项目目录]
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

2. 配置环境变量：
```bash
cp .env.example .env
```

编辑 `.env` 文件，配置以下必要参数：
```ini
# 数据库配置
MONGODB_URI=mongodb://localhost:27017/crawler
REDIS_URI=redis://localhost:6379/0

# 消息队列配置
RABBITMQ_URI=amqp://guest:guest@localhost:5672/

# API密钥配置
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# 监控配置
ALERT_WEBHOOK=your_alert_webhook_url
```

### 2. 基本使用

#### 启动服务
```bash
# 启动主服务
python src/main.py

# 启动监控服务
python src/monitor/main.py

# 启动内容生成服务
python src/generators/main.py
```

#### 使用爬虫
```python
from src.crawlers.xhs_crawler import XHSCrawler

# 初始化爬虫
crawler = XHSCrawler()

# 采集内容
results = await crawler.crawl(
    keywords=["AI开发", "独立开发"],
    time_range="24h",
    limit=100
)
```

#### 内容分析
```python
from src.analyzers.content_analyzer import ContentAnalyzer

# 初始化分析器
analyzer = ContentAnalyzer()

# 分析内容
analysis = await analyzer.analyze(content)
```

#### 生成内容
```python
from src.generators.content_generator import ContentGenerator

# 初始化生成器
generator = ContentGenerator()

# 生成内容
content = await generator.generate(
    template="xiaohongshu",
    topic="AI开发经验分享",
    keywords=["Python", "AI", "开发"]
)
```

## 常见问题

### 1. 配置问题
- Q: 如何修改数据库连接？
- A: 在 `.env` 文件中修改 `MONGODB_URI` 配置

### 2. 运行问题
- Q: 服务无法启动？
- A: 检查环境变量配置和依赖安装

### 3. 性能问题
- Q: 采集速度慢？
- A: 调整并发配置和代理设置

## 下一步

- 阅读[开发文档](../development/README.md)了解更多技术细节
- 查看[API文档](../development/api.md)了解接口使用
- 参考[最佳实践](../user-guide/best-practices.md)优化使用方式

## 获取帮助

- 提交Issue报告问题
- 加入技术社群讨论
- 查看更新日志了解最新变化 