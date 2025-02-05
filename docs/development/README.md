# 开发指南

## 开发环境设置

### 1. 系统要求

- Python 3.8+
- Node.js 16+
- Docker & Docker Compose
- Git

### 2. 开发工具

推荐使用以下工具：
- VSCode
- PyCharm
- Git Bash
- DBeaver (数据库管理)

### 3. 环境准备

1. 克隆项目
```bash
git clone <repository_url>
cd crawler-project
```

2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

4. 配置环境变量
```bash
cp config/env/.env.example config/env/.env
# 编辑 .env 文件设置必要的环境变量
```

## 开发规范

### 1. 代码风格

- 遵循 PEP 8 规范
- 使用 Black 进行代码格式化
- 使用 isort 进行导入排序
- 使用 flake8 进行代码检查
- 使用 mypy 进行类型检查

### 2. 提交规范

提交信息格式：
```
<type>(<scope>): <subject>

<body>

<footer>
```

类型（type）：
- feat: 新功能
- fix: 修复
- docs: 文档
- style: 格式
- refactor: 重构
- test: 测试
- chore: 构建过程或辅助工具的变动

### 3. 分支管理

- main: 主分支，用于生产环境
- develop: 开发分支
- feature/*: 功能分支
- bugfix/*: 修复分支
- release/*: 发布分支

### 4. 测试规范

- 单元测试覆盖率要求：80%+
- 集成测试覆盖主要功能
- 编写测试文档
- 使用 pytest 进行测试

## 开发流程

### 1. 功能开发

1. 从 develop 分支创建功能分支
```bash
git checkout develop
git pull
git checkout -b feature/new-feature
```

2. 开发新功能
3. 编写测试
4. 提交代码
5. 创建合并请求

### 2. Bug修复

1. 从 develop 分支创建修复分支
```bash
git checkout develop
git pull
git checkout -b bugfix/fix-issue
```

2. 修复问题
3. 编写测试
4. 提交代码
5. 创建合并请求

### 3. 代码审查

- 代码审查清单
- 性能考虑
- 安全考虑
- 测试覆盖
- 文档更新

## 调试指南

### 1. 日志

- 使用项目的日志工具
```python
from utils.logger import get_logger

logger = get_logger(__name__)
logger.info("Message")
```

### 2. 调试工具

- 使用 pdb/ipdb 进行调试
- 使用 logging 模块记录日志
- 使用 pytest.set_trace() 进行测试调试

### 3. 性能分析

- 使用 cProfile 进行性能分析
- 使用 memory_profiler 进行内存分析
- 使用 line_profiler 进行逐行分析

## 部署流程

### 1. 测试环境

```bash
docker-compose -f docker-compose.test.yml up -d
```

### 2. 生产环境

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## 监控和日志

### 1. 监控指标

- 系统资源使用
- API响应时间
- 错误率
- 任务队列长度

### 2. 日志收集

- 应用日志
- 访问日志
- 错误日志
- 性能日志

## 常见问题

### 1. 环境问题

- 检查 Python 版本
- 检查依赖版本
- 检查环境变量

### 2. 数据库问题

- 连接问题
- 性能问题
- 数据一致性

### 3. 部署问题

- Docker 配置
- 网络设置
- 权限问题

## 参考资源

- [Python 官方文档](https://docs.python.org/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Docker 文档](https://docs.docker.com/)
- [Git 文档](https://git-scm.com/doc) 