# 爬虫项目

## 项目结构

```
src/
├── crawlers/                    # 爬虫模块 [85%]
│   ├── base_crawler.py         # 基础爬虫类 [100%]
│   ├── base.py                 # 通用基类 [100%]
│   ├── bilibili/              # B站爬虫 [90%]
│   │   ├── base.py            # B站基础类 [100%]
│   │   ├── video.py           # 视频爬虫 [95%]
│   │   ├── article.py         # 文章爬虫 [90%]
│   │   ├── dynamic.py         # 动态爬虫 [85%]
│   │   └── search.py          # 搜索爬虫 [90%]
│   ├── xiaohongshu/           # 小红书爬虫 [85%]
│   │   ├── base.py            # 小红书基础类 [100%]
│   │   ├── detail.py          # 笔记详情爬虫 [90%]
│   │   ├── user.py            # 用户爬虫 [85%]
│   │   ├── search.py          # 搜索爬虫 [90%]
│   │   └── tag.py             # 标签爬虫 [80%]
│   ├── utils/                 # 工具类 [90%]
│   │   ├── cookie_manager.py   # Cookie管理 [95%]
│   │   ├── proxy_manager.py    # 代理管理 [90%]
│   │   └── headers_manager.py  # 请求头管理 [95%]
│   └── tests/                 # 测试用例 [70%]
└── database/                  # 数据存储 [80%]

## 功能特性

### 已实现功能
- [x] 基础爬虫框架
- [x] 代理IP池
- [x] Cookie管理
- [x] 请求头管理
- [x] 反爬虫策略
- [x] B站视频爬取
- [x] B站文章爬取
- [x] B站动态爬取
- [x] B站搜索功能
- [x] 小红书笔记爬取
- [x] 小红书用户爬取
- [x] 小红书搜索功能
- [x] 小红书标签爬取
- [x] 数据存储功能

### 进行中功能
- [ ] 分布式爬虫支持
- [ ] 任务调度系统
- [ ] 监控告警系统
- [ ] 数据分析功能
- [ ] 内容生成功能

### 计划功能
- [ ] 自动化测试完善
- [ ] 性能优化
- [ ] 数据导出功能
- [ ] 可视化界面
- [ ] API接口服务

## 开发进度

总体完成度：85%

主要模块完成度：
- 基础框架：100%
- B站爬虫：90%
- 小红书爬虫：85%
- 工具类：90%
- 数据存储：80%
- 测试用例：70%

## 下一步计划

1. 完善测试用例覆盖率
2. 实现分布式爬虫支持
3. 开发监控告警系统
4. 优化性能和稳定性
5. 添加更多平台支持

## 主要功能

1. 内容采集
   - 多平台内容抓取
   - 自动化数据清洗
   - 智能内容分类

2. 内容处理
   - 文本分析和摘要
   - 图片处理和优化
   - 视频剪辑和合成

3. 内容生成
   - 自动化文章生成
   - 图文排版优化
   - 视频内容制作

4. 系统监控
   - 性能指标收集
   - 异常监控告警
   - 运行状态报告

5. Web API接口
   - RESTful API设计
   - JWT认证授权
   - 请求限流控制
   - OpenAPI/Swagger文档

## 快速开始

1. 克隆项目
```bash
git clone https://github.com/your-username/crawler.git
cd crawler
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
```

4. 配置环境变量
```bash
cp config/env/.env.example config/env/.env
# 编辑 .env 文件，设置必要的配置项
```

5. 初始化数据库
```bash
alembic upgrade head
```

6. 运行测试
```bash
pytest
```

7. 启动服务
```bash
python -m src.web.app
```

## API文档

启动服务后，可以通过以下地址访问API文档：

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
- OpenAPI JSON: http://localhost:8000/api/openapi.json

## 开发指南

1. 添加新的爬虫
```python
from src.crawlers.base_crawler import BaseCrawler

class NewCrawler(BaseCrawler):
    async def crawl(self, keywords, time_range="24h", limit=10):
        # 实现采集逻辑
        pass
        
    async def parse(self, data):
        # 实现解析逻辑
        pass

# 注册爬虫
crawler_factory.register_crawler("new_platform", NewCrawler)
```

2. 添加新的API路由
```python
from fastapi import APIRouter, Depends
from src.web.auth.jwt import jwt_handler

router = APIRouter()

@router.get("/items/")
async def get_items(token_data = Depends(jwt_handler.verify_token)):
    # 实现API逻辑
    pass
```

3. 自定义监控
```python
from src.monitor.base_monitor import BaseMonitor

class CustomMonitor(BaseMonitor):
    async def collect_metrics(self):
        # 实现指标收集
        pass
        
    async def check_alerts(self):
        # 实现告警检查
        pass
```

4. 运行测试
```bash
# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/

# 运行性能测试
python tests/performance/run_performance_tests.py --report
```

## 配置说明

系统通过环境变量和配置文件进行配置，主要配置项包括：

1. 数据库配置
   - `DATABASE_URL`: 数据库连接URI
   - `DATABASE_POOL_SIZE`: 连接池大小
   
2. 认证配置
   - `JWT_SECRET_KEY`: JWT密钥
   - `JWT_ALGORITHM`: JWT算法
   - `ACCESS_TOKEN_EXPIRE`: 访问令牌过期时间
   
3. 限流配置
   - `RATE_LIMIT_DEFAULT`: 默认限流规则
   - `RATE_LIMIT_API`: API限流规则
   - `RATE_LIMIT_CRAWLER`: 爬虫限流规则
   
4. 监控配置
   - `MONITOR_INTERVAL`: 监控检查间隔
   - `ALERT_WEBHOOK`: 告警Webhook地址
   
5. 日志配置
   - `LOG_LEVEL`: 日志级别
   - `LOG_FORMAT`: 日志格式（text/json）

完整配置项请参考 `config/env/.env.example` 文件。

## 注意事项

- 请遵守目标平台的使用规则
- 合理设置采集频率和并发数
- 定期更新Cookie和代理
- 及时处理监控告警
- 使用依赖注入管理组件
- 保持日志记录的完整性
- 遵循API限流规则
- 保护好认证密钥

## 贡献指南

详见 [贡献指南](CONTRIBUTING.md)

## 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。

# 数据脱敏示例
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

def anonymize_text(text):
    analyzer = AnalyzerEngine()
    anonymizer = AnonymizerEngine()
    results = analyzer.analyze(text=text, language='zh')
    return anonymizer.anonymize(text, results) 

# 自适应并发控制示例
class AdaptiveConcurrency:
    def __init__(self):
        self.max_workers = 10
        self.error_window = deque(maxlen=100)
    
    def adjust_concurrency(self):
        error_rate = sum(self.error_window)/len(self.error_window)
        if error_rate < 0.05:
            self.max_workers = min(self.max_workers+2, 50)
        else:
            self.max_workers = max(self.max_workers-5, 1)


# 示例：在API网关中添加熔断逻辑
from pybreaker import CircuitBreaker

breaker = CircuitBreaker(fail_max=5, reset_timeout=60)

@breaker
async def api_handler(request):
    # 业务逻辑



# 使用import-linter进行架构守护
[importlinter:contract:layers]
name = Layered architecture 
layer_modules =
    src.domain
    src.application
    src.infrastructure

# 自定义指标示例
- name: content_metrics
  labels:
    - platform
    - content_type
  metrics:
    - name: content_processing_time
      type: histogram
      help: 内容处理耗时分布
      buckets: [0.1, 0.5, 1, 5]

# 配置热更新示例
@app.post("/config/reload")
async def reload_config():
    try:
        load_config()
        logger.info("配置热更新成功")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"配置更新失败: {str(e)}")
        return {"status": "error"}


| 紧急度 | 高                  | 中                | 低               |
|--------|---------------------|-------------------|------------------|
| 高影响 | 安全增强            | 监控增强          | 文档优化         |
| 中影响 | 性能优化            | 架构优化          | 部署优化         |
| 低影响 | 可维护性提升        | 基础设施升级      | 实验性功能开发   |

Phase 1 (1-2周):
- 安全补丁升级
- 关键性能指标监控
- 核心文档完善

Phase 2 (2-4周):
- 自适应并发控制
- 结构化日志改造
- 配置中心建设

Phase 3 (1-2月):
- 服务网格集成
- 混沌工程框架
- 自动扩缩容策略