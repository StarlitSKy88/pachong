# 部署文档

## 系统要求

- Python 3.10+
- MongoDB 4.4+
- Redis 6.0+（可选，用于缓存）

## 安装步骤

1. 克隆代码
```bash
git clone https://github.com/yourusername/content-crawler.git
cd content-crawler
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
```

4. 配置环境变量
```bash
cp examples/config.env .env
# 编辑.env文件，填入必要的配置信息
```

## 配置说明

### 数据库配置

```env
# MongoDB配置
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB=crawler_db

# Redis配置（可选）
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

### 代理配置

```env
# 代理配置
PROXY_API_URL=http://localhost:5555/get_all
PROXY_MIN_SCORE=60
PROXY_MAX_SCORE=100
PROXY_CHECK_INTERVAL=300
```

### Cookie配置

```env
# Cookie配置
COOKIE_FILE_PATH=./data/cookies.json
COOKIE_MIN_SCORE=60
COOKIE_MAX_SCORE=100
COOKIE_CHECK_INTERVAL=300
COOKIE_MIN_COUNT=5
```

### 监控配置

```env
# 监控配置
MONITOR_CHECK_INTERVAL=60
ALERT_WEBHOOK=https://your-webhook-url/alert
```

### 爬虫配置

```env
# 爬虫配置
CRAWLER_CONCURRENCY=3
CRAWLER_RETRY_TIMES=3
CRAWLER_TIMEOUT=30
REQUEST_DELAY=1
```

### 日志配置

```env
# 日志配置
LOG_LEVEL=INFO
LOG_FILE=./logs/crawler.log
```

## 目录结构

```
content-crawler/
├── src/                # 源代码目录
│   ├── crawlers/      # 爬虫实现
│   ├── database/      # 数据存储
│   ├── models/        # 数据模型
│   ├── monitor/       # 监控系统
│   └── utils/         # 工具函数
├── examples/          # 使用示例
├── tests/             # 测试用例
├── docs/              # 文档
├── data/              # 数据目录
│   ├── cookies.json   # Cookie文件
│   └── exports/       # 导出目录
├── logs/              # 日志目录
├── requirements.txt   # 项目依赖
└── README.md         # 项目说明
```

## 部署方式

### 1. 直接部署

适用于开发环境或小规模部署。

1. 安装依赖
```bash
pip install -r requirements.txt
```

2. 启动MongoDB
```bash
mongod --dbpath /path/to/data/db
```

3. 运行爬虫
```bash
python examples/crawler_example.py
```

### 2. Docker部署

适用于生产环境部署。

1. 构建镜像
```bash
docker build -t content-crawler .
```

2. 运行容器
```bash
docker run -d \
    --name content-crawler \
    -v $(pwd)/data:/app/data \
    -v $(pwd)/logs:/app/logs \
    --env-file .env \
    content-crawler
```

### 3. Docker Compose部署

适用于完整的服务部署。

1. 创建docker-compose.yml
```yaml
version: '3'

services:
  crawler:
    build: .
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    env_file:
      - .env
    depends_on:
      - mongodb
      - redis
      
  mongodb:
    image: mongo:4.4
    volumes:
      - ./data/db:/data/db
    ports:
      - "27017:27017"
      
  redis:
    image: redis:6.0
    volumes:
      - ./data/redis:/data
    ports:
      - "6379:6379"
```

2. 启动服务
```bash
docker-compose up -d
```

## 监控和维护

### 1. 日志查看

```bash
# 查看应用日志
tail -f logs/crawler.log

# 查看错误日志
grep ERROR logs/crawler.log
```

### 2. 数据备份

```bash
# 备份MongoDB
mongodump --out backup/$(date +%Y%m%d)

# 备份Cookie文件
cp data/cookies.json backup/cookies_$(date +%Y%m%d).json
```

### 3. 监控指标

可以通过以下方式查看监控指标：

1. 日志文件
2. 监控接口
3. 告警通知

### 4. 常见问题

1. 代理不可用
   - 检查代理API是否可访问
   - 检查代理质量分数
   - 更新代理池

2. Cookie失效
   - 检查Cookie有效性
   - 更新Cookie池
   - 增加Cookie数量

3. 请求失败
   - 检查网络连接
   - 检查请求参数
   - 调整并发数量

4. 内存占用过高
   - 检查内存泄漏
   - 调整批量大小
   - 增加清理任务

## 升级和回滚

### 1. 升级步骤

1. 备份数据
```bash
./scripts/backup.sh
```

2. 更新代码
```bash
git pull origin main
```

3. 更新依赖
```bash
pip install -r requirements.txt
```

4. 重启服务
```bash
docker-compose restart
```

### 2. 回滚步骤

1. 切换版本
```bash
git checkout <version>
```

2. 恢复数据
```bash
./scripts/restore.sh <backup_date>
```

3. 重启服务
```bash
docker-compose restart
```

## 安全建议

1. 使用环境变量管理敏感信息
2. 定期更新依赖版本
3. 限制API访问频率
4. 加密敏感数据
5. 定期备份数据
6. 监控异常访问
7. 使用HTTPS传输
