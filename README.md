# 爬虫项目

## 项目结构

```
.
├── src/                    # 源代码目录
│   ├── api/               # API服务
│   ├── cli/               # 命令行工具
│   ├── crawlers/          # 爬虫实现
│   ├── database/          # 数据库模块
│   ├── models/            # 数据模型
│   ├── processors/        # 数据处理器
│   ├── monitor/           # 监控模块
│   ├── utils/             # 工具类
│   ├── web/              # Web服务
│   ├── export/           # 导出模块
│   ├── themes/           # 主题模块
│   ├── generators/       # 生成器模块
│   └── scheduler/        # 调度模块
│
├── data/                  # 数据目录
│   ├── db/               # 数据库文件
│   ├── logs/             # 日志文件
│   ├── output/           # 输出文件
│   ├── cache/            # 缓存文件
│   ├── downloads/        # 下载文件
│   └── reports/          # 报告文件
│
├── config/               # 配置目录
│   ├── env/             # 环境配置
│   ├── test/            # 测试配置
│   └── deploy/          # 部署配置
│
├── tests/                # 测试目录
│   ├── unit/            # 单元测试
│   ├── integration/     # 集成测试
│   ├── performance/     # 性能测试
│   └── stress/          # 压力测试
│
├── deploy/               # 部署配置
│   ├── docker/          # Docker配置
│   ├── grafana/         # Grafana配置
│   ├── prometheus/      # Prometheus配置
│   └── nginx/           # Nginx配置
│
├── docs/                 # 文档目录
│   ├── api/             # API文档
│   └── development/     # 开发文档
│
└── frontend/            # 前端目录
    ├── src/             # 前端源码
    └── public/          # 静态资源
```

## 配置说明

- 环境配置文件位于 `config/env/` 目录
- 测试配置文件位于 `config/test/` 目录
- 部署配置文件位于 `config/deploy/` 目录

## 数据目录说明

- 数据库文件存储在 `data/db/` 目录
- 日志文件存储在 `data/logs/` 目录
- 输出文件存储在 `data/output/` 目录
- 缓存文件存储在 `data/cache/` 目录
- 下载文件存储在 `data/downloads/` 目录
- 报告文件存储在 `data/reports/` 目录

## 开发说明

1. 安装依赖
```bash
pip install -r requirements.txt
```

2. 配置环境
- 复制 `config/env/.env.example` 到 `config/env/.env`
- 根据需要修改配置

3. 运行测试
```bash
python -m pytest
```

4. 启动服务
```bash
python src/main.py
```

## 部署说明

使用Docker Compose部署：
```bash
docker-compose up -d
```

## 监控说明

- Grafana仪表盘访问：http://localhost:3000
- Prometheus指标访问：http://localhost:9090

## 文档

- API文档：docs/api/
- 开发文档：docs/development/
- 部署文档：docs/deployment/