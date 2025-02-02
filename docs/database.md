# 数据库设计文档

## 一、概述

本文档描述了系统的数据库设计，包括表结构、索引、关系和优化策略。

### 1.1 设计原则

1. 数据完整性
   - 使用外键保证引用完整性
   - 合理设置字段约束
   - 使用事务保证数据一致性

2. 性能优化
   - 合理的索引设计
   - 适当的分区策略
   - 查询优化

3. 可扩展性
   - 预留扩展字段
   - 版本控制支持
   - 分表策略

### 1.2 技术选型

- 主数据库：PostgreSQL 13
- 缓存数据库：Redis 6
- 搜索引擎：Elasticsearch 7
- 时序数据库：InfluxDB

## 二、表结构设计

### 2.1 核心业务表

#### keywords（关键词表）
```sql
CREATE TABLE keywords (
    id SERIAL PRIMARY KEY,
    keyword TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    search_count INTEGER DEFAULT 0,
    last_search_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_keyword UNIQUE (keyword)
);

CREATE INDEX idx_keywords_status ON keywords(status);
CREATE INDEX idx_keywords_search_count ON keywords(search_count DESC);
```

#### questions（问题表）
```sql
CREATE TABLE questions (
    id SERIAL PRIMARY KEY,
    keyword_id INTEGER REFERENCES keywords(id),
    question TEXT NOT NULL,
    question_vector VECTOR(384),  -- 问题的向量表示
    frequency INTEGER DEFAULT 1,
    status VARCHAR(20) DEFAULT 'active',
    source_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_keyword_question UNIQUE (keyword_id, question)
);

CREATE INDEX idx_questions_keyword_id ON questions(keyword_id);
CREATE INDEX idx_questions_frequency ON questions(frequency DESC);
CREATE INDEX idx_questions_vector ON questions USING ivfflat (question_vector vector_cosine_ops);
```

#### sources（来源表）
```sql
CREATE TABLE sources (
    id SERIAL PRIMARY KEY,
    question_id INTEGER REFERENCES questions(id),
    platform VARCHAR(50) NOT NULL,
    url TEXT NOT NULL,
    title TEXT,
    content TEXT,
    author VARCHAR(100),
    publish_time TIMESTAMP WITH TIME ZONE,
    crawled_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    CONSTRAINT uk_platform_url UNIQUE (platform, url)
);

CREATE INDEX idx_sources_question_id ON sources(question_id);
CREATE INDEX idx_sources_platform ON sources(platform);
CREATE INDEX idx_sources_publish_time ON sources(publish_time DESC);
```

#### contents（生成内容表）
```sql
CREATE TABLE contents (
    id SERIAL PRIMARY KEY,
    question_id INTEGER REFERENCES questions(id),
    format VARCHAR(50) NOT NULL,
    title TEXT,
    content TEXT NOT NULL,
    summary TEXT,
    tags TEXT[],
    status VARCHAR(20) DEFAULT 'draft',
    quality_score DECIMAL(3,2),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_contents_question_id ON contents(question_id);
CREATE INDEX idx_contents_format ON contents(format);
CREATE INDEX idx_contents_status ON contents(status);
CREATE INDEX idx_contents_quality_score ON contents(quality_score DESC);
```

### 2.2 系统管理表

#### tasks（任务表）
```sql
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    params JSONB NOT NULL,
    result JSONB,
    error TEXT,
    progress DECIMAL(5,2) DEFAULT 0,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tasks_type ON tasks(type);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_created_at ON tasks(created_at DESC);
```

#### errors（错误日志表）
```sql
CREATE TABLE errors (
    id SERIAL PRIMARY KEY,
    service VARCHAR(50) NOT NULL,
    error_type VARCHAR(100) NOT NULL,
    error_message TEXT NOT NULL,
    stack_trace TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_errors_service ON errors(service);
CREATE INDEX idx_errors_error_type ON errors(error_type);
CREATE INDEX idx_errors_created_at ON errors(created_at DESC);
```

## 三、数据关系

### 3.1 实体关系图

```
keywords 1:N questions 1:N sources
questions 1:N contents
```

### 3.2 关键关系说明

1. 关键词与问题
   - 一个关键词可以对应多个问题
   - 问题必须关联到一个关键词

2. 问题与来源
   - 一个问题可以有多个来源
   - 来源必须关联到一个问题

3. 问题与内容
   - 一个问题可以生成多个不同格式的内容
   - 内容必须关联到一个问题

## 四、索引策略

### 4.1 主要索引

1. 查询优化索引
   - 关键词状态索引
   - 问题频率索引
   - 内容质量分数索引

2. 关联查询索引
   - 问题-关键词索引
   - 来源-问题索引
   - 内容-问题索引

3. 全文搜索索引
   - 问题向量索引
   - 内容标题索引
   - 来源内容索引

### 4.2 索引维护

1. 定期重建
   - 向量索引每周重建
   - 统计信息每日更新
   - 清理无效索引

2. 监控指标
   - 索引使用率
   - 索引大小
   - 查询性能

## 五、数据优化

### 5.1 分区策略

1. 时间分区
   ```sql
   CREATE TABLE sources_partition OF sources
   PARTITION BY RANGE (publish_time);
   
   CREATE TABLE sources_y2024m01 
   PARTITION OF sources_partition
   FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
   ```

2. 平台分区
   ```sql
   CREATE TABLE contents_partition OF contents
   PARTITION BY LIST (format);
   
   CREATE TABLE contents_xhs 
   PARTITION OF contents_partition
   FOR VALUES IN ('xhs');
   ```

### 5.2 缓存策略

1. Redis缓存
   ```
   # 热门关键词缓存
   KEY: hot_keywords
   TYPE: ZSET
   TTL: 1 hour
   
   # 问题详情缓存
   KEY: question:{id}
   TYPE: HASH
   TTL: 30 minutes
   ```

2. 本地缓存
   ```python
   # LRU缓存装饰器
   @cache(maxsize=1000, ttl=300)
   def get_question_detail(question_id: int) -> Dict:
       pass
   ```

### 5.3 清理策略

1. 数据归档
   ```sql
   -- 归档旧数据
   INSERT INTO sources_archive
   SELECT * FROM sources
   WHERE publish_time < NOW() - INTERVAL '1 year';
   ```

2. 垃圾清理
   ```sql
   -- 清理无效数据
   DELETE FROM contents
   WHERE status = 'draft'
   AND created_at < NOW() - INTERVAL '7 days';
   ```

## 六、监控和维护

### 6.1 性能监控

1. 慢查询日志
   ```sql
   ALTER SYSTEM SET log_min_duration_statement = '1000';
   ```

2. 统计信息
   ```sql
   SELECT schemaname, relname, seq_scan, idx_scan
   FROM pg_stat_user_tables;
   ```

### 6.2 维护计划

1. 定期维护
   ```sql
   -- 更新统计信息
   ANALYZE keywords;
   
   -- 回收空间
   VACUUM FULL contents;
   ```

2. 备份策略
   ```bash
   # 每日全量备份
   pg_dump -Fc dbname > backup.dump
   
   # 定时增量备份
   pg_basebackup -D backup -P --wal-method=stream
   ```

## 七、安全策略

### 7.1 访问控制

```sql
-- 创建只读用户
CREATE ROLE readonly_user WITH LOGIN PASSWORD 'xxx';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;

-- 创建应用用户
CREATE ROLE app_user WITH LOGIN PASSWORD 'xxx';
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO app_user;
```

### 7.2 数据加密

```sql
-- 创建加密扩展
CREATE EXTENSION pgcrypto;

-- 加密敏感数据
UPDATE users SET password = crypt(password, gen_salt('bf'));
```

## 八、扩展性设计

### 8.1 版本控制

```sql
-- 添加版本信息
ALTER TABLE contents ADD COLUMN version INTEGER DEFAULT 1;
ALTER TABLE contents ADD COLUMN parent_version INTEGER;
```

### 8.2 元数据管理

```sql
-- 创建元数据表
CREATE TABLE metadata_definitions (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    field_name VARCHAR(50) NOT NULL,
    field_type VARCHAR(20) NOT NULL,
    description TEXT,
    is_required BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

# 数据库连接池文档

## 概述

数据库连接池是一个用于管理数据库连接的组件，它可以重用数据库连接，减少连接创建和销毁的开销，提高系统性能。本项目实现了一个通用的连接池管理器，支持多种数据库类型。

## 功能特点

- 支持多种数据库
  - SQLAlchemy（PostgreSQL, MySQL等）
  - Redis
  - MongoDB
- 连接池监控
  - 连接数量统计
  - 活跃连接监控
  - 空闲连接监控
- 配置管理
  - 灵活的配置项
  - 运行时配置修改
  - 配置验证
- 资源管理
  - 自动创建连接
  - 自动回收连接
  - 优雅关闭
- 异常处理
  - 连接错误处理
  - 重试机制
  - 错误报告

## 安装依赖

```bash
pip install sqlalchemy[asyncio] redis[hiredis] motor
```

## 基本用法

### 1. 创建连接池管理器

```python
from src.database.connection_pool import ConnectionPoolManager
from src.utils.config_manager import ConfigManager

# 创建配置管理器
config_manager = ConfigManager()
config_manager.load_env()

# 创建连接池管理器
pool_manager = ConnectionPoolManager(config_manager)
```

### 2. 配置连接池

```python
# SQLAlchemy连接池配置
sql_config = {
    "url": "postgresql+asyncpg://user:pass@localhost/db",
    "pool_size": 5,
    "max_overflow": 10,
    "pool_timeout": 30,
    "pool_recycle": 1800,
    "pool_pre_ping": True
}

# Redis连接池配置
redis_config = {
    "host": "localhost",
    "port": 6379,
    "db": 0,
    "max_connections": 10,
    "timeout": 30
}

# MongoDB连接池配置
mongo_config = {
    "uri": "mongodb://localhost:27017",
    "max_pool_size": 100,
    "min_pool_size": 0,
    "max_idle_time_ms": 10000,
    "wait_queue_timeout_ms": 1000
}
```

### 3. 创建连接池

```python
from src.database.connection_pool import (
    SQLAlchemyPool,
    RedisConnectionPool,
    MongoConnectionPool
)

# 创建SQLAlchemy连接池
sql_pool = await pool_manager.create_pool(
    "sql",
    SQLAlchemyPool,
    sql_config
)

# 创建Redis连接池
redis_pool = await pool_manager.create_pool(
    "redis",
    RedisConnectionPool,
    redis_config
)

# 创建MongoDB连接池
mongo_pool = await pool_manager.create_pool(
    "mongo",
    MongoConnectionPool,
    mongo_config
)
```

### 4. 使用连接池

```python
# 获取连接池
sql_pool = pool_manager.get_pool("sql")
redis_pool = pool_manager.get_pool("redis")
mongo_pool = pool_manager.get_pool("mongo")

# 使用连接池
async with sql_pool.pool.connect() as conn:
    result = await conn.execute(query)
    
redis = redis_pool.pool
await redis.set("key", "value")

mongo = mongo_pool.pool
await mongo.db.collection.insert_one(document)
```

### 5. 监控连接池

```python
# 获取单个连接池指标
metrics = await sql_pool.get_metrics()
print(f"SQL连接池指标: {metrics}")

# 获取所有连接池指标
all_metrics = await pool_manager.get_all_metrics()
for name, metrics in all_metrics.items():
    print(f"{name}连接池指标: {metrics}")
```

### 6. 关闭连接池

```python
# 关闭单个连接池
await sql_pool.close()

# 关闭所有连接池
await pool_manager.close_all()
```

## 配置说明

### SQLAlchemy连接池配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| url | str | 必填 | 数据库连接URL |
| pool_size | int | 5 | 连接池大小 |
| max_overflow | int | 10 | 最大溢出连接数 |
| pool_timeout | int | 30 | 连接超时时间（秒） |
| pool_recycle | int | 1800 | 连接回收时间（秒） |
| pool_pre_ping | bool | True | 是否预检连接 |

### Redis连接池配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| host | str | 必填 | Redis主机地址 |
| port | int | 必填 | Redis端口号 |
| db | int | 0 | 数据库编号 |
| max_connections | int | 10 | 最大连接数 |
| timeout | int | 30 | 连接超时时间（秒） |

### MongoDB连接池配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| uri | str | 必填 | MongoDB连接URI |
| max_pool_size | int | 100 | 最大连接数 |
| min_pool_size | int | 0 | 最小连接数 |
| max_idle_time_ms | int | 10000 | 最大空闲时间（毫秒） |
| wait_queue_timeout_ms | int | 1000 | 等待队列超时时间（毫秒） |

## 监控指标

### 基础指标

| 指标名 | 类型 | 说明 |
|--------|------|------|
| created_at | datetime | 连接池创建时间 |
| total_connections | int | 总连接数 |
| active_connections | int | 活跃连接数 |
| idle_connections | int | 空闲连接数 |
| max_connections | int | 最大连接数 |

### SQLAlchemy特有指标

| 指标名 | 类型 | 说明 |
|--------|------|------|
| overflow | int | 溢出连接数 |
| checkedin | int | 已回收连接数 |
| checkedout | int | 已借出连接数 |

## 异常处理

### 常见异常

1. 连接池未初始化
```python
RuntimeError: {name} 连接池未初始化
```

2. 连接池不存在
```python
KeyError: 连接池不存在: {name}
```

3. 连接超时
```python
TimeoutError: 获取连接超时
```

### 异常处理建议

1. 使用try-except捕获异常
```python
try:
    pool = pool_manager.get_pool("sql")
except KeyError:
    logger.error("连接池不存在")
```

2. 实现重试机制
```python
from tenacity import retry, stop_after_attempt

@retry(stop=stop_after_attempt(3))
async def get_connection():
    return await pool.acquire()
```

3. 记录错误日志
```python
try:
    await pool.create_pool()
except Exception as e:
    logger.error(f"创建连接池失败: {str(e)}")
    raise
```

## 性能优化建议

1. 合理设置连接池大小
   - 考虑系统负载
   - 监控连接使用情况
   - 定期调整配置

2. 启用连接预检
   - 设置pool_pre_ping=True
   - 及时发现无效连接
   - 自动重新连接

3. 使用连接回收
   - 设置合适的pool_recycle
   - 避免连接过期
   - 定期清理空闲连接

4. 实现连接复用
   - 使用上下文管理器
   - 及时释放连接
   - 避免连接泄漏

## 最佳实践

1. 初始化连接池
```python
async def init_pools():
    """初始化所有连接池"""
    await pool_manager.create_pool("sql", SQLAlchemyPool, sql_config)
    await pool_manager.create_pool("redis", RedisConnectionPool, redis_config)
    await pool_manager.create_pool("mongo", MongoConnectionPool, mongo_config)
```

2. 使用上下文管理器
```python
async def get_user(user_id: int):
    """获取用户信息"""
    pool = pool_manager.get_pool("sql")
    async with pool.pool.connect() as conn:
        result = await conn.execute(
            select(users).where(users.c.id == user_id)
        )
        return await result.first()
```

3. 实现健康检查
```python
async def check_pools_health():
    """检查连接池健康状态"""
    metrics = await pool_manager.get_all_metrics()
    for name, pool_metrics in metrics.items():
        if pool_metrics["active_connections"] >= pool_metrics["max_connections"]:
            logger.warning(f"{name}连接池已满")
```

4. 优雅关闭
```python
async def shutdown():
    """优雅关闭连接池"""
    try:
        await pool_manager.close_all()
    except Exception as e:
        logger.error(f"关闭连接池失败: {str(e)}")
```

## 常见问题

1. 连接池满载
   - 增加最大连接数
   - 减少连接持有时间
   - 优化查询性能

2. 连接超时
   - 检查网络状态
   - 调整超时时间
   - 实现重试机制

3. 连接泄漏
   - 使用上下文管理器
   - 实现连接追踪
   - 定期检查泄漏

4. 性能问题
   - 监控连接使用
   - 优化连接配置
   - 使用连接池指标 