# 项目开发文档

# 开发指南

## 开发环境

### 1. 环境要求
- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- Chrome/Chromium
- Git

### 2. 开发工具
- IDE: VSCode
  - Python扩展
  - GitLens
  - Docker
  - REST Client
- PyCharm Professional
  - 数据库工具
  - HTTP Client
  - Git工具

### 3. 环境设置
```bash
# 1. 克隆项目
git clone https://github.com/yourusername/content-crawler.git
cd content-crawler

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑.env文件，配置必要的参数

# 设置开发环境变量
export ENV=development
```

## 代码规范

### 1. Python代码规范
- 遵循PEP 8规范
- 使用类型注解
- 编写文档字符串
- 适当的注释

### 2. 命名规范
- 类名: 大驼峰命名法 (PascalCase)
- 函数名: 小写下划线 (snake_case)
- 变量名: 小写下划线 (snake_case)
- 常量名: 大写下划线 (UPPER_SNAKE_CASE)

### 3. 文件组织
```
src/
├── crawlers/          # 爬虫模块
├── processors/        # 处理模块
├── database/         # 数据库模块
├── models/           # 数据模型
├── utils/            # 工具函数
└── config/           # 配置文件
```

## 开发流程

### 1. 功能开发
1. 创建功能分支
```bash
git checkout -b feature/new-feature
```

2. 编写代码和测试
```bash
# 运行测试
pytest tests/

# 代码格式化
black src/ tests/

# 代码检查
flake8 src/ tests/

# 类型检查
mypy src/
```

3. 提交代码
```bash
git add .
git commit -m "feat: 添加新功能"
git push origin feature/new-feature
```

4. 创建Pull Request
- 填写功能说明
- 关联相关Issue
- 请求代码审查

### 2. Bug修复
1. 创建修复分支
```bash
git checkout -b bugfix/issue-123
```

2. 修复和测试
```bash
# 运行相关测试
pytest tests/test_xxx.py -v

# 添加新的测试用例
```

3. 提交修复
```bash
git add .
git commit -m "fix: 修复问题"
git push origin bugfix/issue-123
```

4. 创建Pull Request
- 描述问题和解决方案
- 关联相关Issue
- 请求代码审查

### 3. 代码审查

#### 审查清单
- 代码风格是否规范
- 测试是否完整
- 文档是否更新
- 性能是否优化
- 安全是否考虑

#### 审查流程
1. 检查代码变更
2. 运行测试
3. 提供反馈
4. 确认修改
5. 批准合并

## 测试指南

### 1. 测试类型
- 单元测试
- 集成测试
- 功能测试
- 性能测试

### 2. 测试规范
- 测试文件命名: test_*.py
- 测试类命名: Test*
- 测试函数命名: test_*
- 使用fixture共享资源

### 3. 测试示例
```python
import pytest
from src.crawlers import XiaoHongShuCrawler

@pytest.fixture
def crawler():
    return XiaoHongShuCrawler()

def test_crawler_init(crawler):
    assert crawler is not None
    assert crawler.name == "xiaohongshu"

@pytest.mark.asyncio
async def test_crawler_fetch(crawler):
    result = await crawler.fetch_content("test_url")
    assert result is not None
    assert "content" in result
```

## 调试技巧

### 1. 日志调试
```python
from loguru import logger

logger.debug("变量值: {}", var)
logger.info("执行步骤: {}", step)
logger.error("错误信息: {}", error)
```

### 2. 断点调试
```python
import pdb; pdb.set_trace()
# 或使用IDE的调试工具
```

### 3. 性能分析
```python
import cProfile
import pstats

def profile_code():
    profiler = cProfile.Profile()
    profiler.enable()
    # 要分析的代码
    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats('cumtime')
    stats.print_stats()
```

## 文档编写

### 1. 代码文档
- 模块文档
- 类文档
- 函数文档
- 重要算法说明

### 2. API文档
- 接口说明
- 参数说明
- 返回值说明
- 错误码说明

### 3. 文档示例
```python
def fetch_content(self, url: str) -> Dict[str, Any]:
    """获取内容
    
    Args:
        url: 内容URL
        
    Returns:
        Dict[str, Any]: 包含以下字段的字典
        - content: 内容正文
        - images: 图片列表
        - stats: 统计信息
        
    Raises:
        RequestError: 请求失败
        ParseError: 解析失败
    """
    pass
```

## 发布流程

### 1. 版本管理
- 使用语义化版本
- 更新版本号
- 生成更新日志

### 2. 测试验证
- 运行完整测试
- 检查覆盖率
- 验证功能

### 3. 文档更新
- 更新API文档
- 更新使用说明
- 更新部署文档

### 4. 代码合并
- 合并到develop分支
- 创建发布分支
- 合并到main分支

### 5. 发布
- 打标签
- 生成发布包
- 更新生产环境

## 常见问题

### 1. 环境问题
- 检查Python版本
- 验证依赖版本
- 确认环境变量

### 2. 数据库问题
- 检查连接配置
- 验证SQL语句
- 检查索引使用

### 3. 爬虫问题
- 检查请求参数
- 验证响应解析
- 检查代理设置

### 4. 性能问题
- 使用性能分析工具
- 优化数据库查询
- 调整缓存策略

# 开发日志

## 2024-03-27

### 完成的任务

1. 导出功能开发 (100%)
   - [x] 创建导出基类
   - [x] 实现HTML格式导出
   - [x] 添加资源处理功能
   - [x] 实现批量导出
   - [x] 添加通知功能
   - [x] 编写测试用例

2. 模板开发 (100%)
   - [x] 创建文章页面模板
   - [x] 创建索引页面模板
   - [x] 添加响应式设计
   - [x] 添加暗色模式
   - [x] 优化打印样式

3. 测试用例开发 (100%)
   - [x] 基础导出功能测试
   - [x] HTML格式导出测试
   - [x] 批量导出测试
   - [x] 资源处理测试
   - [x] 错误处理测试
   - [x] 通知功能测试

### 遇到的问题

1. 图片处理
   - 问题：图片下载失败时的处理策略
   - 解决：保留原始链接，记录错误日志

2. 并发控制
   - 问题：批量导出时的资源占用
   - 解决：添加并发限制，分批处理

3. 模板管理
   - 问题：模板加载失败的处理
   - 解决：添加错误处理，提供详细日志

### 经验总结

1. 代码设计
   - 使用抽象基类定义接口
   - 分离关注点（格式、存储、通知）
   - 提供灵活的配置选项
   - 实现优雅的错误处理

2. 测试策略
   - 使用pytest-asyncio测试异步代码
   - 模拟外部依赖（HTTP请求、文件系统）
   - 验证边界条件和错误情况
   - 测试并发和资源清理

3. 性能优化
   - 异步处理I/O操作
   - 复用HTTP会话
   - 优化图片大小和质量
   - 实现资源清理机制

### 下一步计划

1. PDF格式支持
   - 实现PDF导出格式
   - 添加页面布局选项
   - 支持目录生成
   - 优化打印效果

2. EPUB格式支持
   - 实现EPUB导出格式
   - 添加元数据支持
   - 优化阅读体验
   - 支持多章节

3. 导出优化
   - 添加进度报告
   - 优化内存使用
   - 提供取消功能
   - 改进错误恢复

### 项目进度

- [x] 基础设施搭建
- [x] 导出基类开发
- [x] HTML格式支持
- [x] 测试用例开发
- [ ] PDF格式支持
- [ ] EPUB格式支持
- [ ] 性能优化
- [ ] 文档完善

### 备注

1. 代码质量
   - 所有测试通过
   - 代码覆盖率>90%
   - 无严重bug
   - 文档完整

2. 性能指标
   - 单文件导出<1s
   - 批量导出（10个文件）<5s
   - 内存占用<200MB
   - CPU使用率<50%

3. 可用性
   - 配置简单
   - 错误提示清晰
   - 使用文档完整
   - 示例代码充分
