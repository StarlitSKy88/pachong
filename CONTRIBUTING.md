# 贡献指南

感谢您考虑为本项目做出贡献！

## 行为准则

本项目采用[贡献者公约](https://www.contributor-covenant.org/zh-cn/version/2/0/code_of_conduct/)。参与本项目即表示您同意遵守其条款。

## 如何贡献

### 提交Issue

1. 在提交issue之前，请先搜索现有的issue，避免重复。
2. 使用提供的issue模板，填写所有必要信息。
3. 清晰描述问题或建议，提供必要的上下文。
4. 如果是bug报告，请提供复现步骤和相关日志。

### 提交Pull Request

1. Fork本仓库
2. 创建您的特性分支：`git checkout -b feature/my-feature`
3. 提交您的修改：`git commit -m 'feat: add some feature'`
4. 推送到分支：`git push origin feature/my-feature`
5. 提交Pull Request

### 开发流程

1. 克隆项目
```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
```

2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

4. 安装pre-commit钩子
```bash
pre-commit install
```

### 代码规范

1. Python代码规范
   - 使用Black格式化代码
   - 使用Flake8检查代码质量
   - 使用Mypy进行类型检查
   - 遵循PEP 8编码规范

2. 文档规范
   - 所有函数和类必须有文档字符串
   - 复杂逻辑必须有注释说明
   - 更新相关文档

3. 测试规范
   - 添加单元测试
   - 保持测试覆盖率
   - 运行所有测试套件

### 提交规范

1. 提交信息格式
```
<type>(<scope>): <subject>

<body>

<footer>
```

2. Type类型
   - feat: 新功能
   - fix: 修复bug
   - docs: 文档更新
   - style: 代码格式
   - refactor: 代码重构
   - test: 测试相关
   - chore: 构建过程或辅助工具的变动

3. Scope范围
   - api: API相关
   - crawler: 爬虫相关
   - processor: 处理器相关
   - generator: 生成器相关
   - db: 数据库相关
   - monitor: 监控相关
   - deploy: 部署相关
   - docs: 文档相关

4. Subject主题
   - 使用祈使句
   - 不超过50个字符
   - 不以句号结尾

### 分支管理

1. 分支命名
   - 主分支：main
   - 开发分支：develop
   - 功能分支：feature/*
   - 修复分支：bugfix/*
   - 发布分支：release/*

2. 工作流程
   - 从develop分支创建功能分支
   - 完成开发后提交PR到develop分支
   - develop分支定期合并到main分支发布

### 版本发布

1. 版本号规则
   - 主版本号：不兼容的API修改
   - 次版本号：向下兼容的功能性新增
   - 修订号：向下兼容的问题修正

2. 发布流程
   - 更新CHANGELOG.md
   - 更新版本号
   - 创建发布分支
   - 执行测试
   - 合并到main分支
   - 创建标签
   - 发布版本

### 文档维护

1. 文档类型
   - README.md：项目概述
   - CONTRIBUTING.md：贡献指南
   - CHANGELOG.md：变更日志
   - docs/：详细文档

2. 文档更新
   - 代码变更时更新相关文档
   - 保持文档的时效性
   - 使用清晰的语言

## 问题反馈

如果您在贡献过程中遇到任何问题，请：

1. 查看现有的issue
2. 在issue中提出问题
3. 等待维护者回应

## 联系方式

- 维护者：Your Name
- 邮箱：your.email@example.com
- 项目主页：https://github.com/your-org/your-repo

## 致谢

感谢所有为本项目做出贡献的开发者！ 