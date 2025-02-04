# 缓存模块

## 简介

缓存模块提供了一个灵活、高性能的缓存系统，支持本地缓存和分布式缓存，并提供了缓存同步机制。

## 主要特性

### 1. 多级缓存
- 本地缓存（LRU算法）
- Redis缓存（分布式）
- 缓存同步（本地与远程）

### 2. 基本功能
- 获取/设置缓存值
- 删除缓存值
- 检查键是否存在
- 清空缓存
- TTL过期机制

### 3. 高级特性
- 批量操作支持
- 事件通知机制
- 分布式锁
- 计数器功能
- 版本控制

### 4. 性能优化
- 连接池管理
- 批量操作优化
- 异步操作支持
- 管道命令支持

### 5. 监控指标
- 缓存命中率
- 缓存大小
- 淘汰次数
- 访问统计

## 使用示例

### 1. 本地缓存

```python
from cache.local_cache import LRUCache

# 创建缓存实例
cache = LRUCache("local", max_size=1000)

# 启动缓存
await cache.start()

# 设置缓存
await cache.set("key", "value", ttl=3600)

# 获取缓存
value = await cache.get("key")

# 停止缓存
await cache.stop()
```

### 2. Redis缓存

```python
from redis.asyncio import Redis
from cache.redis_cache import RedisCache

# 创建Redis客户端
redis = Redis(host="localhost", port=6379)

# 创建缓存实例
cache = RedisCache("redis", redis, prefix="app:")

# 设置缓存
await cache.set("key", "value", ttl=3600)

# 获取缓存
value = await cache.get("key")

# 使用分布式锁
async with cache.acquire_lock("lock_key"):
    # 执行需要加锁的操作
    pass
```

### 3. 缓存同步

```python
from cache.cache_sync import CacheSyncManager

# 创建同步管理器
sync_manager = CacheSyncManager(
    "sync",
    local_cache,
    remote_cache,
    sync_interval=60
)

# 启动同步
await sync_manager.start()

# 停止同步
await sync_manager.stop()
```

## 配置说明

### 1. 本地缓存配置
- `max_size`: 最大缓存条目数
- `cleanup_interval`: 清理间隔（秒）
- `default_ttl`: 默认过期时间（秒）

### 2. Redis缓存配置
- `prefix`: 键前缀
- `default_ttl`: 默认过期时间（秒）
- `serializer`: 序列化函数
- `deserializer`: 反序列化函数

### 3. 同步配置
- `sync_interval`: 同步间隔（秒）
- `retry_times`: 重试次数
- `retry_delay`: 重试延迟（秒）

## 性能优化建议

1. 合理设置缓存大小
   - 根据内存限制设置max_size
   - 避免过度淘汰

2. 使用批量操作
   - 优先使用multi_get/multi_set
   - 减少网络请求次数

3. 合理设置TTL
   - 避免过短的TTL
   - 根据数据更新频率设置

4. 优化序列化
   - 选择高效的序列化方式
   - 减少数据大小

## 监控指标说明

1. 命中率（hit_rate）
   - 计算公式：hits / (hits + misses)
   - 建议值：>80%

2. 淘汰率（eviction_rate）
   - 计算公式：evictions / total_operations
   - 建议值：<1%

3. 内存使用率（memory_usage）
   - 计算公式：used_memory / max_memory
   - 建议值：<80%

4. 响应时间（response_time）
   - 获取操作：<1ms
   - 设置操作：<2ms

## 常见问题

1. 缓存穿透
   - 问题：查询不存在的键
   - 解决：布隆过滤器

2. 缓存击穿
   - 问题：热点键过期
   - 解决：互斥锁

3. 缓存雪崩
   - 问题：大量键同时过期
   - 解决：随机TTL

4. 数据一致性
   - 问题：缓存与数据库不一致
   - 解决：更新策略（Cache-Aside） 