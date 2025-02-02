# API文档

## 基本信息

- 基础URL: `http://localhost:8000/api/v1`
- 认证方式: Bearer Token
- 响应格式: JSON
- 时间格式: ISO 8601 (YYYY-MM-DDTHH:mm:ssZ)

## 认证

### 获取访问令牌

```http
POST /auth/token
Content-Type: application/json

{
    "username": "string",
    "password": "string"
}
```

响应:

```json
{
    "access_token": "string",
    "token_type": "bearer",
    "expires_in": 3600
}
```

## 关键词分析

### 分析关键词

```http
POST /analyze
Content-Type: application/json
Authorization: Bearer <token>

{
    "keyword": "string",
    "time_range": "24h",
    "platforms": ["xhs", "bilibili"],
    "limit": 20
}
```

响应:

```json
{
    "request_id": "string",
    "status": "success",
    "data": {
        "keyword": "string",
        "questions": [
            {
                "id": "string",
                "question": "string",
                "frequency": 100,
                "sources": [
                    {
                        "platform": "string",
                        "url": "string",
                        "timestamp": "2024-03-27T12:00:00Z"
                    }
                ]
            }
        ],
        "metadata": {
            "total_sources": 1000,
            "platforms": ["xhs", "bilibili"],
            "time_range": "24h"
        }
    }
}
```

### 获取分析状态

```http
GET /analyze/{request_id}
Authorization: Bearer <token>
```

响应:

```json
{
    "request_id": "string",
    "status": "processing",
    "progress": 0.75,
    "message": "正在分析数据...",
    "created_at": "2024-03-27T12:00:00Z",
    "updated_at": "2024-03-27T12:01:00Z"
}
```

## 内容生成

### 生成内容

```http
POST /generate
Content-Type: application/json
Authorization: Bearer <token>

{
    "question_id": "string",
    "format": "xhs",
    "options": {
        "style": "专业",
        "tone": "正式",
        "length": "medium"
    }
}
```

响应:

```json
{
    "task_id": "string",
    "status": "accepted",
    "estimated_time": 300
}
```

### 获取生成结果

```http
GET /generate/{task_id}
Authorization: Bearer <token>
```

响应:

```json
{
    "task_id": "string",
    "status": "completed",
    "data": {
        "content": {
            "title": "string",
            "body": "string",
            "tags": ["string"],
            "media": [
                {
                    "type": "image",
                    "url": "string",
                    "description": "string"
                }
            ]
        },
        "metadata": {
            "format": "xhs",
            "generated_at": "2024-03-27T12:00:00Z",
            "word_count": 1000
        }
    }
}
```

## 数据管理

### 获取问题列表

```http
GET /questions
Authorization: Bearer <token>
Query Parameters:
- keyword: string
- time_range: string (24h, 7d, 30d)
- platform: string
- page: integer
- per_page: integer
```

响应:

```json
{
    "total": 100,
    "page": 1,
    "per_page": 20,
    "data": [
        {
            "id": "string",
            "question": "string",
            "frequency": 100,
            "created_at": "2024-03-27T12:00:00Z"
        }
    ]
}
```

### 获取内容列表

```http
GET /contents
Authorization: Bearer <token>
Query Parameters:
- question_id: string
- format: string
- status: string
- page: integer
- per_page: integer
```

响应:

```json
{
    "total": 100,
    "page": 1,
    "per_page": 20,
    "data": [
        {
            "id": "string",
            "question_id": "string",
            "format": "xhs",
            "status": "published",
            "created_at": "2024-03-27T12:00:00Z",
            "content": {
                "title": "string",
                "body": "string"
            }
        }
    ]
}
```

## 系统管理

### 获取系统状态

```http
GET /system/status
Authorization: Bearer <token>
```

响应:

```json
{
    "status": "healthy",
    "components": {
        "database": "up",
        "redis": "up",
        "worker": "up"
    },
    "metrics": {
        "requests_per_minute": 100,
        "average_response_time": 200,
        "error_rate": 0.01
    }
}
```

### 获取任务队列状态

```http
GET /system/queue
Authorization: Bearer <token>
```

响应:

```json
{
    "total_tasks": 100,
    "active_tasks": 10,
    "queued_tasks": 90,
    "workers": [
        {
            "id": "string",
            "status": "active",
            "current_task": "string",
            "processed_tasks": 1000
        }
    ]
}
```

## 错误处理

### 错误响应格式

```json
{
    "error": {
        "code": "string",
        "message": "string",
        "details": {}
    },
    "request_id": "string",
    "timestamp": "2024-03-27T12:00:00Z"
}
```

### 常见错误代码

- 400: 请求参数错误
- 401: 未授权
- 403: 权限不足
- 404: 资源不存在
- 429: 请求过于频繁
- 500: 服务器内部错误
- 503: 服务暂时不可用

## 限流策略

- 基础限制: 60次/分钟
- 分析API: 10次/分钟
- 生成API: 5次/分钟

## WebSocket接口

### 实时任务状态

```javascript
ws://localhost:8000/ws/tasks/{task_id}
```

消息格式:

```json
{
    "type": "status_update",
    "data": {
        "task_id": "string",
        "status": "string",
        "progress": 0.75,
        "message": "string",
        "timestamp": "2024-03-27T12:00:00Z"
    }
}
```

## 批量操作

### 批量分析关键词

```http
POST /analyze/batch
Content-Type: application/json
Authorization: Bearer <token>

{
    "keywords": ["string"],
    "time_range": "24h",
    "platforms": ["xhs", "bilibili"]
}
```

响应:

```json
{
    "batch_id": "string",
    "total_tasks": 10,
    "accepted_tasks": 10,
    "failed_tasks": 0
}
```

### 获取批量操作状态

```http
GET /batch/{batch_id}
Authorization: Bearer <token>
```

响应:

```json
{
    "batch_id": "string",
    "status": "processing",
    "total_tasks": 10,
    "completed_tasks": 5,
    "failed_tasks": 0,
    "created_at": "2024-03-27T12:00:00Z",
    "updated_at": "2024-03-27T12:01:00Z"
}
```

## 爬虫API

### BaseCrawler

基础爬虫类，提供通用的爬虫功能。

#### 初始化参数

- `platform`: 平台名称
- `proxy_manager`: 代理管理器实例（可选）
- `cookie_manager`: Cookie管理器实例（可选）

#### 主要方法

##### async crawl(keywords: List[str], time_range: str = "24h", limit: int = 100) -> List[Dict[str, Any]]

爬取内容。

参数：
- `keywords`: 关键词列表
- `time_range`: 时间范围（24h/1w/1m）
- `limit`: 返回数量限制

返回：
- 内容列表

##### async parse(data: Dict[str, Any]) -> Dict[str, Any]

解析数据。

参数：
- `data`: 原始数据

返回：
- 解析后的数据

### XHSCrawler

小红书爬虫类，继承自BaseCrawler。

#### 特有方法

##### async _search_notes(keyword: str, time_range: str) -> List[Dict[str, Any]]

搜索笔记。

参数：
- `keyword`: 关键词
- `time_range`: 时间范围

返回：
- 笔记列表

##### async _get_note_detail(note_id: str) -> Dict[str, Any]

获取笔记详情。

参数：
- `note_id`: 笔记ID

返回：
- 笔记详情

### BiliBiliCrawler

B站爬虫类，继承自BaseCrawler。

#### 特有方法

##### async _search_videos(keyword: str, time_range: str) -> List[Dict[str, Any]]

搜索视频。

参数：
- `keyword`: 关键词
- `time_range`: 时间范围

返回：
- 视频列表

##### async _get_video_detail(video_id: str) -> Dict[str, Any]

获取视频详情。

参数：
- `video_id`: 视频ID

返回：
- 视频详情

## 代理管理API

### ProxyManager

代理管理器类。

#### 初始化参数

- `api_url`: 代理API地址
- `min_score`: 最低代理分数
- `max_score`: 最高代理分数
- `check_interval`: 检查间隔（秒）

#### 主要方法

##### async get_proxy() -> Optional[str]

获取代理。

返回：
- 代理地址

##### async check_proxy(proxy: str) -> bool

检查代理。

参数：
- `proxy`: 代理地址

返回：
- 是否可用

## Cookie管理API

### CookieManager

Cookie管理器类。

#### 初始化参数

- `cookie_file`: Cookie文件路径
- `min_score`: 最低Cookie分数
- `max_score`: 最高Cookie分数
- `check_interval`: 检查间隔（秒）

#### 主要方法

##### async get_cookie(platform: str) -> Optional[Dict[str, str]]

获取Cookie。

参数：
- `platform`: 平台名称

返回：
- Cookie字典

##### async check_cookie(platform: str, cookie: Dict[str, str]) -> bool

检查Cookie。

参数：
- `platform`: 平台名称
- `cookie`: Cookie字典

返回：
- 是否有效

## 监控API

### BaseMonitor

基础监控类。

#### 初始化参数

- `name`: 监控器名称
- `check_interval`: 检查间隔（秒）

#### 主要方法

##### async collect_metrics() -> Dict[str, Any]

收集指标。

返回：
- 监控指标

##### async check_alerts() -> List[Dict[str, Any]]

检查告警。

返回：
- 告警列表

### CrawlerMonitor

爬虫监控类，继承自BaseMonitor。

#### 特有方法

##### async _collect_proxy_metrics() -> Dict[str, Any]

收集代理指标。

返回：
- 代理指标

##### async _collect_cookie_metrics() -> Dict[str, Any]

收集Cookie指标。

返回：
- Cookie指标

## 任务队列API

### TaskQueue

任务队列管理器类。

#### 初始化参数

- `max_workers`: 最大工作线程数
- `max_queue_size`: 最大队列大小

#### 主要方法

##### async add_task(task: Task) -> None

添加任务。

参数：
- `task`: 任务对象

##### def get_task(task_id: str) -> Optional[Task]

获取任务。

参数：
- `task_id`: 任务ID

返回：
- 任务对象

##### def get_stats() -> Dict[str, Any]

获取统计信息。

返回：
- 统计信息

## 数据导出API

### Exporter

数据导出工具类。

#### 初始化参数

- `output_dir`: 输出目录

#### 主要方法

##### def export_json(data: List[Dict[str, Any]], filename: str) -> str

导出JSON格式。

参数：
- `data`: 数据列表
- `filename`: 文件名

返回：
- 输出文件路径

##### def export_csv(data: List[Dict[str, Any]], filename: str) -> str

导出CSV格式。

参数：
- `data`: 数据列表
- `filename`: 文件名

返回：
- 输出文件路径

##### def export_excel(data: List[Dict[str, Any]], filename: str) -> str

导出Excel格式。

参数：
- `data`: 数据列表
- `filename`: 文件名

返回：
- 输出文件路径

##### def export_all(data: List[Dict[str, Any]], filename_prefix: str) -> Dict[str, str]

导出所有支持的格式。

参数：
- `data`: 数据列表
- `filename_prefix`: 文件名前缀

返回：
- 各格式输出文件路径
