# 项目结构地图

## 总体完成度：40%

## 核心模块

### 1. 爬虫引擎 (45%)
```
src/crawlers/
├── base/ (60%)
│   ├── base.py - 基础爬虫类
│   ├── base_crawler.py - 爬虫基类
│   └── crawler_factory.py - 爬虫工厂
├── network/ (50%)
│   ├── cookie_manager.py - Cookie管理
│   ├── proxy_manager.py - 代理管理
│   └── proxy_pool.py - 代理池
├── platforms/ (40%)
│   ├── xiaohongshu/ - 小红书爬虫
│   ├── bilibili/ - B站爬虫
│   └── ai_crawler.py - AI内容爬虫
└── utils/ (30%)
    ├── xhs_sign.py - 签名工具
    ├── bilibili_sign.py - B站签名
    └── cookie_generator.py - Cookie生成
```

### 2. 数据库模块 (50%)
```
src/database/
├── models/ (60%)
│   ├── models.py - 数据模型
│   └── base_dao.py - 基础DAO
├── storage/ (50%)
│   ├── base_storage.py - 存储基类
│   ├── sqlite_storage.py - SQLite存储
│   ├── mongo_storage.py - MongoDB存储
│   └── cache_storage.py - 缓存存储
├── dao/ (50%)
│   ├── content_dao.py - 内容DAO
│   ├── comment_dao.py - 评论DAO
│   ├── platform_dao.py - 平台DAO
│   └── tag_dao.py - 标签DAO
└── connection/ (40%)
    ├── connection_pool.py - 连接池
    └── session.py - 会话管理
```

### 3. API服务 (45%)
```
src/api/
├── routes/ (50%)
│   ├── crawler_api.py - 爬虫接口
│   └── alert_api.py - 告警接口
├── main.py (50%)
│   └── FastAPI应用主文件
└── schemas/ (35%)
    ├── request.py - 请求模型
    └── response.py - 响应模型
```

### 4. 前端界面 (30%)
```
frontend/
├── src/ (35%)
│   ├── views/ - 页面视图
│   ├── components/ - 组件
│   ├── router.js - 路由配置
│   └── App.vue - 主应用
├── public/ (30%)
└── assets/ (25%)
```

### 5. 监控模块 (40%)
```
src/monitor/
├── 告警系统 (45%)
│   ├── alert.py - 告警核心
│   ├── alert_engine.py - 告警引擎
│   ├── alert_rule.py - 告警规则
│   ├── alert_notifier.py - 通知器
│   ├── alert_history.py - 历史记录
│   ├── alert_stats.py - 统计分析
│   └── alert_aggregator.py - 聚合器
├── 监控核心 (40%)
│   ├── base_monitor.py - 监控基类
│   ├── crawler_monitor.py - 爬虫监控
│   ├── business_monitor.py - 业务监控
│   └── performance_monitor.py - 性能监控
├── 指标系统 (35%)
│   ├── metrics.py - 指标定义
│   ├── metrics_collector.py - 指标收集
│   └── dashboard.py - 监控面板
└── 视图层 (40%)
    ├── views.py - 视图定义
    ├── monitor.py - 监控视图
    └── notifier.py - 通知视图
```

### 6. 处理器模块 (35%)
```
src/processors/
├── 基础组件 (40%)
│   ├── base_processor.py - 处理器基类
│   └── analyzer.py - 分析器
├── 平台处理 (35%)
│   └── xiaohongshu_processor.py - 小红书处理器
└── 内容处理 (30%)
    ├── generator.py - 内容生成
    └── summarizer.py - 内容摘要
```

### 7. 调度器模块 (30%)
```
src/scheduler/
├── 基础框架 (35%)
│   ├── base_scheduler.py - 调度器基类
│   └── crawler_scheduler.py - 爬虫调度器
└── 测试组件 (25%)
    └── test_scheduler.py - 调度器测试
```

### 8. 模型模块 (45%)
```
src/models/
├── 基础模型 (50%)
│   ├── base.py - 模型基类
│   ├── tables.py - 数据表定义
│   └── enums.py - 枚举定义
├── 业务模型 (45%)
│   ├── content_tag.py - 内容标签
│   ├── category.py - 分类模型
│   └── task.py - 任务模型
├── 网络模型 (40%)
│   ├── cookie.py - Cookie模型
│   ├── proxy.py - 代理模型
│   └── request.py - 请求模型
└── 监控模型 (45%)
    ├── metrics.py - 指标模型
    └── error.py - 错误模型
```

### 9. 缓存模块 (40%)
```
src/cache/
├── 核心组件 (45%)
│   ├── cache_manager.py - 缓存管理器
│   └── cache_sync.py - 缓存同步
└── 存储实现 (35%)
    ├── redis_cache.py - Redis缓存
    └── local_cache.py - 本地缓存
```

### 10. 导出模块 (35%)
```
src/export/
├── base.py - 导出基类
└── html.py - HTML导出器
```

### 11. Web服务 (40%)
```
src/web/
├── 核心组件 (45%)
│   ├── app.py - 应用主文件
│   └── __init__.py - 初始化文件
├── 路由组件 (40%)
│   ├── routes/ - 路由定义
│   └── middleware/ - 中间件
├── 认证组件 (35%)
│   └── auth/ - 认证模块
└── 视图组件 (40%)
    ├── templates/ - 模板文件
    ├── crawler.html - 爬虫页面
    └── index.html - 主页
```

### 12. 主题模块 (35%)
```
src/themes/
├── 基础组件 (40%)
│   ├── base.py - 主题基类
│   └── __init__.py - 初始化文件
├── 主题实现 (35%)
│   ├── default.py - 默认主题
│   ├── elegant.py - 优雅主题
│   └── modern.py - 现代主题
└── 格式化 (30%)
    └── formatters/ - 格式化工具
```

### 13. CLI工具 (35%)
```
src/
├── cli.py - 命令行接口
└── config.py - 配置文件
```

### 14. Web组件 (40%)
```
src/web/
├── 中间件 (35%)
│   └── rate_limit.py - 限速中间件
├── 认证 (40%)
│   └── jwt.py - JWT认证
├── 路由 (35%)
│   └── monitor.py - 监控路由
└── 模板 (45%)
    ├── base.html - 基础模板
    ├── topic.html - 主题模板
    ├── daily.html - 日报模板
    ├── monitor/ - 监控模板
    └── reports/ - 报告模板
```

### 4. 模板系统 (40%)
```
templates/
└── html/ (40%)
    ├── index.html - 主页模板
    └── article.html - 文章模板
```

### 5. 数据迁移 (35%)
```
migrations/
├── env.py - 迁移环境
└── script.py.mako - 迁移脚本模板
```

### 6. 示例代码 (45%)
```
examples/
├── 基础示例 (50%)
│   ├── crawler_example.py - 爬虫示例
│   ├── export_example.py - 导出示例
│   └── generate_example.py - 生成示例
├── 功能示例 (45%)
│   ├── cache_crawler.py - 缓存示例
│   └── example_article.html - 文章示例
├── 配置示例 (40%)
│   └── config.env - 配置示例
└── 高级示例 (45%)
    ├── monitoring/ - 监控示例
    ├── resilience/ - 容错示例
    ├── concurrency/ - 并发示例
    └── security/ - 安全示例
```

## 支持模块

### 1. 配置管理 (55%)
```
src/config/
├── config.py - 配置类
└── settings.py - 设置管理
```

### 2. 工具类 (45%)
```
src/utils/
├── 网络工具 (50%)
│   ├── proxy_manager.py - 代理管理
│   ├── proxy_providers.py - 代理供应商
│   ├── headers_manager.py - 请求头管理
│   └── cookie_manager.py - Cookie管理
├── 性能工具 (45%)
│   ├── rate_limiter.py - 限速器
│   ├── circuit_breaker.py - 断路器
│   ├── retry.py - 重试机制
│   └── cache_manager.py - 缓存管理
├── 错误处理 (40%)
│   ├── error_handler.py - 错误处理
│   ├── exceptions.py - 异常定义
│   └── retry_decorator.py - 重试装饰器
├── 任务管理 (45%)
│   ├── task_queue.py - 任务队列
│   ├── dependency_injector.py - 依赖注入
│   └── config_manager.py - 配置管理
└── 辅助工具 (45%)
    ├── logger.py - 日志工具
    ├── notifier.py - 通知工具
    ├── data_cleaner.py - 数据清理
    ├── exporter.py - 数据导出
    └── llm_api.py - AI接口
```

### 3. 测试套件 (35%)
```
tests/
├── unit/ (40%)
│   ├── test_crawlers.py - 爬虫测试
│   ├── test_models.py - 模型测试
│   └── test_utils.py - 工具测试
├── integration/ (35%)
│   ├── test_storage.py - 存储集成测试
│   ├── test_export.py - 导出集成测试
│   └── test_production.py - 生产环境测试
├── performance/ (30%)
│   ├── test_client.py - 客户端性能
│   └── test_server.py - 服务器性能
├── monitoring/ (35%)
│   ├── test_monitor.py - 监控测试
│   └── test_metrics_collector.py - 指标收集测试
└── stress/ (35%)
    ├── test_crawler_monitor.py - 爬虫压力测试
    └── test_rate_limiter.py - 限速器压力测试
```

### 4. 部署相关 (30%)
```
deploy/
├── docker/ (35%)
│   ├── api/ - API服务容器
│   ├── crawler/ - 爬虫服务容器
│   ├── processor/ - 处理器服务容器
│   └── generator/ - 生成器服务容器
├── monitoring/ (30%)
│   ├── grafana/ - 监控面板
│   └── prometheus/ - 指标收集
├── nginx/ (25%)
│   └── conf/ - 反向代理配置
└── scripts/ (30%)
    ├── deploy.sh - 部署脚本
    └── backup.sh - 备份脚本
```

## 文档 (45%)

### 1. 开发文档 (50%)
```
./
├── README.md - 项目说明
├── CHANGELOG.md - 变更日志
├── PROJECT_STATUS.md - 项目状态
└── docs/ - 详细文档
```

### 2. 规范文档 (45%)
```
./
├── SECURITY.md - 安全策略
├── CODE_OF_CONDUCT.md - 行为准则
└── CONTRIBUTING.md - 贡献指南
```

### 3. 配置文档 (40%)
```
./
├── .env.example - 环境变量示例
├── requirements.txt - 依赖要求
├── setup.py - 安装配置
└── pyproject.toml - 项目配置
```

## 配置模块

### 1. 项目配置 (50%)
```
config/
├── 基础配置 (55%)
│   ├── config.json - 基础配置
│   ├── config.py - 配置类
│   └── alembic.ini - 数据库迁移配置
├── 平台配置 (45%)
│   ├── bilibili.json - B站配置
│   └── xiaohongshu.json - 小红书配置
├── 功能配置 (50%)
│   ├── export.json - 导出配置
│   └── alert_rules.json - 告警规则
└── 环境配置 (50%)
    ├── dev/ - 开发环境
    └── env/ - 环境变量
```

### 2. 工具集 (40%)
```
tools/
├── llm_api.py - AI接口工具
├── web_scraper.py - 网页抓取
├── screenshot_utils.py - 截图工具
└── search_engine.py - 搜索引擎
```

### 3. 数据管理 (45%)
```
data/
├── 数据存储 (50%)
│   ├── crawler.db - SQLite数据库
│   ├── cookies.json - Cookie存储
│   └── proxies.json - 代理存储
├── 任务管理 (45%)
│   ├── tasks/ - 任务数据
│   └── results/ - 结果数据
├── 日志记录 (40%)
│   ├── logs/ - 日志文件
│   └── reports/ - 报告文件
└── 缓存管理 (45%)
    ├── cache/ - 缓存数据
    ├── downloads/ - 下载文件
    └── output/ - 输出数据
```

## 开发配置

### 1. GitHub配置 (45%)
```
.github/
├── 工作流配置 (50%)
│   └── workflows/ - GitHub Actions
├── 问题模板 (45%)
│   └── ISSUE_TEMPLATE/ - Issue模板
├── 安全配置 (40%)
│   ├── dependabot.yml - 依赖更新
│   └── dependency-review-config.yml - 依赖审查
└── 社区文档 (45%)
    ├── SUPPORT.md - 支持文档
    ├── FUNDING.yml - 赞助配置
    ├── CODEOWNERS - 代码所有者
    └── pull_request_template.md - PR模板
```

### 2. 开发环境 (40%)
```
.devcontainer/
├── devcontainer.json - 容器配置
└── settings.json - VSCode设置
```

### 3. 部署配置 (45%)
```
deploy/
├── Grafana配置 (50%)
│   ├── dashboards/ - 仪表盘配置
│   └── provisioning/ - 资源配置
├── Prometheus配置 (45%)
│   ├── rules/ - 告警规则
│   └── prometheus.yml - 主配置
└── Nginx配置 (40%)
    ├── conf.d/ - 站点配置
    └── nginx.conf - 主配置
```

### 4. AI配置 (35%)
```
prompts/
└── analyzer.json - 分析器提示词
```