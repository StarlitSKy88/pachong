# 内容采集和分析系统

## 项目概述

这是一个基于Python的内容采集和分析系统，支持从多个平台（如小红书、B站）采集内容，并进行智能分析和处理。

## 核心功能

1. 内容采集
   - 多平台支持（小红书、B站）
   - 智能代理池
   - Cookie管理
   - 反爬处理

2. 内容分析
   - 质量评估
   - 主题分析
   - 相关性评估
   - 标签推荐

3. 数据处理
   - 数据清洗
   - 数据存储
   - 数据分析
   - 数据导出

4. 系统功能
   - 监控告警
   - 任务调度
   - 性能优化
   - 日志管理

## 技术栈

- 语言：Python 3.8+
- 数据库：SQLite/MySQL
- 缓存：Redis
- Web框架：FastAPI
- 任务队列：Celery
- 监控：Prometheus + Grafana

## 快速开始

1. 环境准备
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

2. 配置
```bash
cp .env.example .env
# 编辑.env文件，配置必要的参数
```

3. 运行
```bash
python -m src.cli run
```

## 文档导航

- [系统架构](ARCHITECTURE.md)
- [开发指南](DEVELOPMENT.md)
- [部署文档](DEPLOYMENT.md)
- [API文档](API.md)
- [监控运维](MONITORING.md)

## 项目状态

当前版本：v0.1.0

- [x] 基础架构搭建
- [x] 爬虫系统实现
- [x] 内容分析器
- [ ] 数据存储优化
- [ ] 监控系统
- [ ] Web接口

## 贡献指南

请参阅 [CONTRIBUTING.md](../CONTRIBUTING.md)

## 许可证

MIT License - 详见 [LICENSE](../LICENSE) 