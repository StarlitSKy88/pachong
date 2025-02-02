# 测试文档

## 测试环境

### 1. 环境要求

- Python 3.10+
- pytest 8.0+
- pytest-asyncio
- pytest-cov
- pytest-mock
- MongoDB 4.4+
- Redis 6.0+（可选）

### 2. 环境配置

1. 安装测试依赖
```bash
pip install -r requirements-dev.txt
```

2. 配置测试环境变量
```bash
cp examples/config.env .env.test
# 编辑.env.test文件，设置测试环境配置
```

## 测试类型

### 1. 单元测试

测试单个组件的功能。

#### 测试范围

- 爬虫类
- 数据模型
- 工具函数
- 监控系统

#### 示例

```python
def test_crawler_init():
    """测试爬虫初始化"""
    crawler = BaseCrawler("test")
    assert crawler.platform == "test"
    assert crawler.proxy_manager is None
    assert crawler.cookie_manager is None

@pytest.mark.asyncio
async def test_crawler_crawl():
    """测试爬虫采集"""
    crawler = TestCrawler()
    results = await crawler.crawl(["test"], "24h", 10)
    assert len(results) == 10
    assert all(isinstance(r, dict) for r in results)
```

### 2. 集成测试

测试多个组件的交互。

#### 测试范围

- 爬虫与代理
- 爬虫与Cookie
- 爬虫与数据库
- 监控与告警

#### 示例

```python
@pytest.mark.asyncio
async def test_crawler_with_proxy():
    """测试带代理的爬虫"""
    proxy_manager = ProxyManager()
    crawler = TestCrawler(proxy_manager=proxy_manager)
    results = await crawler.crawl(["test"], "24h", 10)
    assert len(results) == 10

@pytest.mark.asyncio
async def test_crawler_with_cookie():
    """测试带Cookie的爬虫"""
    cookie_manager = CookieManager()
    crawler = TestCrawler(cookie_manager=cookie_manager)
    results = await crawler.crawl(["test"], "24h", 10)
    assert len(results) == 10
```

### 3. 功能测试

测试完整的功能流程。

#### 测试范围

- 内容采集
- 数据处理
- 数据导出
- 监控告警

#### 示例

```python
@pytest.mark.asyncio
async def test_content_collection():
    """测试内容采集流程"""
    # 初始化组件
    proxy_manager = ProxyManager()
    cookie_manager = CookieManager()
    crawler = TestCrawler(
        proxy_manager=proxy_manager,
        cookie_manager=cookie_manager
    )
    
    # 采集内容
    results = await crawler.crawl(["test"], "24h", 10)
    assert len(results) == 10
    
    # 处理数据
    for result in results:
        content = await Content.create(**result)
        assert content.id is not None
        
    # 导出数据
    exporter = Exporter()
    filepath = exporter.export_json(results, "test.json")
    assert os.path.exists(filepath)
```

### 4. 性能测试

测试系统性能和资源使用。

#### 测试范围

- 并发性能
- 内存使用
- CPU使用
- 网络性能

#### 示例

```python
@pytest.mark.asyncio
async def test_crawler_performance():
    """测试爬虫性能"""
    crawler = TestCrawler()
    
    # 记录开始时间
    start_time = time.time()
    
    # 并发采集
    tasks = []
    for _ in range(10):
        task = crawler.crawl(["test"], "24h", 10)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    
    # 计算性能指标
    end_time = time.time()
    duration = end_time - start_time
    total_items = sum(len(r) for r in results)
    items_per_second = total_items / duration
    
    assert items_per_second >= 10  # 每秒至少处理10条数据
```

## 测试编写指南

### 1. 测试结构

1. 测试文件组织
```
tests/
├── unit/              # 单元测试
├── integration/       # 集成测试
├── functional/        # 功能测试
└── performance/       # 性能测试
```

2. 测试命名规范
```python
# 文件名：test_module.py
# 类名：TestClassName
# 方法名：test_function_name
```

3. 测试夹具
```python
@pytest.fixture
def crawler():
    """创建测试爬虫"""
    return TestCrawler()

@pytest.fixture
async def database():
    """创建测试数据库"""
    # 设置
    yield database
    # 清理
```

### 2. 测试原则

1. 单一职责
   - 每个测试只测试一个功能
   - 避免测试之间的依赖
   - 保持测试简单明了

2. 完整覆盖
   - 测试正常流程
   - 测试异常情况
   - 测试边界条件

3. 可维护性
   - 使用测试夹具
   - 避免重复代码
   - 保持测试整洁

### 3. 测试数据

1. 模拟数据
```python
@pytest.fixture
def mock_data():
    """创建模拟数据"""
    return [
        {
            "id": 1,
            "title": "测试标题1",
            "content": "测试内容1"
        },
        {
            "id": 2,
            "title": "测试标题2",
            "content": "测试内容2"
        }
    ]
```

2. 测试数据库
```python
@pytest.fixture
async def test_db():
    """创建测试数据库"""
    # 创建测试数据库
    db = await create_test_database()
    
    # 添加测试数据
    await db.content.insert_many(mock_data)
    
    yield db
    
    # 清理测试数据
    await db.content.delete_many({})
```

## 测试运行

### 1. 运行测试

1. 运行所有测试
```bash
pytest
```

2. 运行特定测试
```bash
# 运行单元测试
pytest tests/unit/

# 运行特定文件
pytest tests/test_crawler.py

# 运行特定测试
pytest tests/test_crawler.py::test_function
```

3. 运行选项
```bash
# 显示详细信息
pytest -v

# 显示打印输出
pytest -s

# 并行运行
pytest -n auto

# 失败时停止
pytest -x
```

### 2. 测试覆盖率

1. 生成覆盖率报告
```bash
pytest --cov=src tests/
```

2. 生成HTML报告
```bash
pytest --cov=src --cov-report=html tests/
```

3. 检查覆盖率要求
```bash
pytest --cov=src --cov-fail-under=80 tests/
```

### 3. 测试报告

1. 生成JUnit报告
```bash
pytest --junitxml=reports/junit.xml
```

2. 生成HTML报告
```bash
pytest --html=reports/report.html
```

## 持续集成

### 1. GitHub Actions

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      mongodb:
        image: mongo:4.4
        ports:
          - 27017:27017
          
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: "3.10"
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
          
      - name: Run tests
        run: |
          pytest --cov=src tests/
          
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

### 2. 本地CI

1. pre-commit配置
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: tests
        name: run tests
        entry: pytest
        language: system
        types: [python]
        pass_filenames: false
```

2. 安装pre-commit
```bash
pip install pre-commit
pre-commit install
```

## 测试维护

### 1. 测试更新

1. 更新测试用例
   - 添加新功能的测试
   - 修复失败的测试
   - 删除过时的测试

2. 更新测试数据
   - 更新模拟数据
   - 更新测试数据库
   - 更新测试配置

### 2. 测试清理

1. 清理测试文件
   - 删除临时文件
   - 清理测试数据库
   - 重置测试状态

2. 清理测试环境
   - 停止测试服务
   - 清理测试缓存
   - 重置环境变量 