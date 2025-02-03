# API 文档

## 概述

本文档描述了内容采集和分析系统的所有API接口。

## 平台管理接口

### 获取平台列表

```bash
GET /api/v1/platforms
```

**参数：**
- `enabled` (可选): 是否启用，布尔值
- `offset` (可选): 偏移量，默认0
- `limit` (可选): 限制数量，默认20

**响应：**
```json
{
  "total": 2,
  "items": [
    {
      "id": 1,
      "name": "xiaohongshu",
      "description": "小红书",
      "base_url": "https://www.xiaohongshu.com",
      "enabled": true,
      "config": {},
      "created_at": "2024-03-27T00:00:00Z",
      "updated_at": "2024-03-27T00:00:00Z"
    }
  ]
}
```

### 添加平台

```bash
POST /api/v1/platforms
```

**请求体：**
```json
{
  "name": "xiaohongshu",
  "description": "小红书",
  "base_url": "https://www.xiaohongshu.com",
  "config": {
    "api": {
      "search": "https://www.xiaohongshu.com/api/sns/v10/search/notes"
    }
  }
}
```

**响应：**
```json
{
  "id": 1,
  "name": "xiaohongshu",
  "description": "小红书",
  "base_url": "https://www.xiaohongshu.com",
  "enabled": true,
  "config": {},
  "created_at": "2024-03-27T00:00:00Z",
  "updated_at": "2024-03-27T00:00:00Z"
}
```

### 更新平台

```bash
PUT /api/v1/platforms/{platform_id}
```

**请求体：**
```json
{
  "description": "小红书平台",
  "config": {
    "api": {
      "search": "https://www.xiaohongshu.com/api/sns/v10/search/notes"
    }
  }
}
```

### 启用/禁用平台

```bash
PATCH /api/v1/platforms/{platform_id}/status
```

**请求体：**
```json
{
  "enabled": true
}
```

## 内容管理接口

### 搜索内容

```bash
GET /api/v1/contents
```

**参数：**
- `platform_id` (可选): 平台ID
- `keyword` (可选): 搜索关键词
- `content_type` (可选): 内容类型
- `status` (可选): 内容状态
- `start_time` (可选): 开始时间
- `end_time` (可选): 结束时间
- `offset` (可选): 偏移量，默认0
- `limit` (可选): 限制数量，默认20

**响应：**
```json
{
  "total": 100,
  "items": [
    {
      "id": 1,
      "platform_id": 1,
      "url": "https://www.xiaohongshu.com/note/123",
      "title": "测试内容",
      "summary": "内容摘要",
      "content_type": "article",
      "author": "测试作者",
      "publish_time": "2024-03-27T00:00:00Z",
      "status": "published",
      "quality_score": 0.8,
      "stats": {
        "likes": 100,
        "comments": 50,
        "collects": 30
      },
      "created_at": "2024-03-27T00:00:00Z",
      "updated_at": "2024-03-27T00:00:00Z"
    }
  ]
}
```

### 获取内容详情

```bash
GET /api/v1/contents/{content_id}
```

### 更新内容状态

```bash
PATCH /api/v1/contents/{content_id}/status
```

**请求体：**
```json
{
  "status": "published"
}
```

### 获取内容统计

```bash
GET /api/v1/contents/stats
```

**参数：**
- `platform_id` (可选): 平台ID
- `start_time` (可选): 开始时间
- `end_time` (可选): 结束时间

**响应：**
```json
{
  "total": 1000,
  "platform_stats": {
    "xiaohongshu": 500,
    "bilibili": 500
  },
  "type_stats": {
    "article": 600,
    "video": 400
  },
  "status_stats": {
    "published": 800,
    "draft": 200
  },
  "quality_stats": {
    "high": 300,
    "medium": 500,
    "low": 200
  }
}
```

## 标签管理接口

### 获取标签列表

```bash
GET /api/v1/tags
```

### 添加标签

```bash
POST /api/v1/tags
```

### 更新标签

```bash
PUT /api/v1/tags/{tag_id}
```

### 删除标签

```bash
DELETE /api/v1/tags/{tag_id}
```

## 评论管理接口

### 获取评论列表

```bash
GET /api/v1/comments
```

### 获取评论详情

```bash
GET /api/v1/comments/{comment_id}
```

### 更新评论状态

```bash
PATCH /api/v1/comments/{comment_id}/status
```

## 错误码

| 错误码 | 描述 |
|--------|------|
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 409 | 资源冲突 |
| 429 | 请求过于频繁 |
| 500 | 服务器内部错误 |

## 认证

所有API请求都需要在Header中携带认证Token：

```
Authorization: Bearer <your_token>
```

## 限流

- 普通用户：100次/分钟
- 高级用户：1000次/分钟

## 数据格式

- 请求和响应均使用JSON格式
- 时间格式：ISO 8601
- 分页参数：offset/limit
- 默认编码：UTF-8
