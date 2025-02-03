# 内容采集和生成系统

## 项目简介

这是一个多平台内容采集和生成系统，支持从多个平台（如小红书、B站）采集特定主题的内容，并进行分析和生成。

### 主要功能

1. 内容采集
   - 多平台支持（小红书、B站）
   - 关键词搜索
   - 时间范围筛选
   - 质量评估
   - 自动化采集

2. 内容分析
   - 主题分类
   - 质量评估
   - 热度分析
   - 趋势分析
   - 数据统计

3. 内容生成
   - 小红书格式
   - HTML格式
   - 播客格式
   - 多媒体支持
   - 质量优化

4. 系统管理
   - 平台管理
   - 任务管理
   - 数据管理
   - 监控告警
   - 日志记录

## 技术栈

- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- SQLAlchemy 2.0+
- aiohttp
- BeautifulSoup4
- Click
- Loguru
- Alembic

## 快速开始

1. 克隆项目：
```bash
git clone https://github.com/your-username/content-crawler.git
cd content-crawler
```

2. 创建虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 配置环境：
```bash
cp .env.example .env
# 编辑 .env 文件，填写必要的配置信息
```

5. 初始化数据库：
```bash
alembic upgrade head
```

6. 添加平台：
```bash
python src/cli.py platform add xiaohongshu https://www.xiaohongshu.com -d "小红书" -c config/xiaohongshu.json
python src/cli.py platform add bilibili https://www.bilibili.com -d "B站" -c config/bilibili.json
```

7. 开始采集：
```bash
python src/cli.py content crawl xiaohongshu "Cursor" "AI" -t 24h -l 100
```

## 项目结构

```
content-crawler/
├── alembic/              # 数据库迁移
├── config/               # 配置文件
├── docs/                 # 文档
├── logs/                 # 日志
├── src/                  # 源代码
│   ├── crawlers/        # 爬虫实现
│   ├── database/        # 数据访问
│   ├── models/          # 数据模型
│   ├── monitor/         # 监控系统
│   ├── utils/           # 工具函数
│   └── cli.py           # 命令行工具
├── tests/               # 测试用例
├── .env.example         # 环境变量示例
├── .gitignore          # Git忽略文件
├── README.md           # 项目说明
└── requirements.txt    # 项目依赖
```

## 使用文档

详细的使用说明请参考 [使用文档](docs/usage.md)。

## 开发指南

1. 代码规范
   - 使用 Black 进行代码格式化
   - 使用 Flake8 进行代码检查
   - 使用 Mypy 进行类型检查
   - 遵循 PEP 8 编码规范

2. Git 规范
   - 主分支：main
   - 开发分支：develop
   - 功能分支：feature/*
   - 修复分支：bugfix/*
   - 发布分支：release/*

3. 提交规范
   - feat: 新功能
   - fix: 修复问题
   - docs: 文档变更
   - style: 代码格式
   - refactor: 代码重构
   - test: 测试相关
   - chore: 其他修改

4. 测试要求
   - 单元测试覆盖率 > 80%
   - 必须包含集成测试
   - 提交前必须通过所有测试

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交代码
4. 创建 Pull Request

## 版本历史

### v0.1.0 (2024-03-27)
- 项目初始化
- 基础架构搭建
- 核心功能实现
- 文档体系建立

## 许可证

本项目采用 MIT 许可证，详情请参阅 [LICENSE](LICENSE) 文件。

## 联系方式

- 作者：Your Name
- 邮箱：your.email@example.com
- 项目地址：https://github.com/your-username/content-crawler