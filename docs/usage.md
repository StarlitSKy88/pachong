# 使用说明

## 安装

1. 克隆项目
```bash
git clone https://github.com/your-username/your-project.git
cd your-project
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

## 配置

1. 创建配置文件
```bash
cp config/export.json.example config/export.json
```

2. 编辑配置文件
```json
{
    "version": "1.0",
    "formats": {
        "html": {
            "enabled": true,
            "template_dir": "templates/html",
            "resource_dir": "resources",
            "default_style": "style.css",
            "image_quality": 85,
            "max_image_size": 1920,
            "batch_concurrency": 5,
            "create_index": true
        }
    },
    "storage": {
        "local": {
            "path": "exports",
            "cleanup_threshold": "1GB",
            "cleanup_age": "7d"
        },
        "s3": {
            "enabled": false,
            "endpoint": "https://s3.amazonaws.com",
            "region": "us-east-1",
            "bucket": "your-bucket",
            "prefix": "exports",
            "access_key": "",
            "secret_key": ""
        }
    },
    "notification": {
        "enabled": true,
        "events": [
            "export.start",
            "export.complete",
            "export.error",
            "batch.start",
            "batch.complete",
            "batch.error"
        ],
        "channels": {
            "email": {
                "enabled": false,
                "template": "email/notification.html",
                "from": "noreply@example.com",
                "to": ["admin@example.com"],
                "smtp": {
                    "host": "smtp.example.com",
                    "port": 587,
                    "username": "",
                    "password": ""
                }
            },
            "webhook": {
                "enabled": false,
                "url": "https://example.com/webhook",
                "headers": {
                    "Authorization": "Bearer your-token"
                }
            }
        }
    }
}
```

## 基本用法

### 1. 导出单篇文章

```python
import asyncio
from src.export.base import ExportManager
from src.export.html import HTMLExport

# 准备数据
article = {
    "title": "示例文章",
    "author": "作者",
    "date": "2024-03-27",
    "category": "分类",
    "tags": ["标签1", "标签2"],
    "content": "<h1>标题</h1><p>内容</p>"
}

async def export_article():
    # 创建导出管理器
    manager = ExportManager()
    manager.register_format("html", HTMLExport)
    
    # 导出文章
    await manager.export(
        article,
        "html",
        "article",
        "output/article.html"
    )

# 运行导出
asyncio.run(export_article())
```

### 2. 批量导出

```python
import asyncio
from src.export.base import ExportManager
from src.export.html import HTMLExport

# 准备数据
articles = [
    {
        "title": f"文章 {i}",
        "content": f"<p>内容 {i}</p>"
    }
    for i in range(10)
]

async def batch_export():
    # 创建导出管理器
    manager = ExportManager()
    manager.register_format("html", HTMLExport)
    
    # 批量导出
    await manager.batch_export(
        articles,
        "html",
        "article",
        "output/articles"
    )

# 运行导出
asyncio.run(batch_export())
```

## 自定义模板

### 1. 创建模板

在 `templates/html` 目录下创建模板文件：

```html
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
</head>
<body>
    <article>
        <h1>{{ title }}</h1>
        <div class="meta">
            {% if author %}
            <span>{{ author }}</span>
            {% endif %}
            
            {% if date %}
            <span>{{ date }}</span>
            {% endif %}
        </div>
        <div class="content">
            {{ content|safe }}
        </div>
    </article>
</body>
</html>
```

### 2. 配置模板

在配置文件中指定模板：

```json
{
    "formats": {
        "html": {
            "templates": {
                "article": {
                    "file": "article.html"
                },
                "index": {
                    "file": "index.html"
                }
            }
        }
    }
}
```

## 存储配置

### 1. 本地存储

```json
{
    "storage": {
        "local": {
            "path": "exports",
            "cleanup_threshold": "1GB",
            "cleanup_age": "7d"
        }
    }
}
```

### 2. S3存储

```json
{
    "storage": {
        "s3": {
            "enabled": true,
            "endpoint": "https://s3.amazonaws.com",
            "region": "us-east-1",
            "bucket": "your-bucket",
            "prefix": "exports",
            "access_key": "your-access-key",
            "secret_key": "your-secret-key"
        }
    }
}
```

## 通知配置

### 1. 邮件通知

```json
{
    "notification": {
        "channels": {
            "email": {
                "enabled": true,
                "template": "email/notification.html",
                "from": "noreply@example.com",
                "to": ["admin@example.com"],
                "smtp": {
                    "host": "smtp.example.com",
                    "port": 587,
                    "username": "your-username",
                    "password": "your-password"
                }
            }
        }
    }
}
```

### 2. Webhook通知

```json
{
    "notification": {
        "channels": {
            "webhook": {
                "enabled": true,
                "url": "https://example.com/webhook",
                "headers": {
                    "Authorization": "Bearer your-token"
                }
            }
        }
    }
}
```

## 错误处理

```python
from src.export.base import ExportError

try:
    await manager.export(...)
except ExportError as e:
    print(f"导出失败：{e}")
except Exception as e:
    print(f"发生错误：{e}")
```

## 性能优化

1. 图片优化
   - 配置最大尺寸：`max_image_size`
   - 配置质量：`image_quality`

2. 并发控制
   - 配置并发数：`batch_concurrency`

3. 存储清理
   - 配置清理阈值：`cleanup_threshold`
   - 配置清理时间：`cleanup_age`

## 最佳实践

1. 模板管理
   - 使用版本控制管理模板
   - 提供默认样式
   - 支持响应式设计
   - 添加打印样式

2. 资源处理
   - 优化图片大小和质量
   - 使用CDN加速资源
   - 实现资源缓存
   - 处理下载失败

3. 错误处理
   - 记录详细日志
   - 实现错误恢复
   - 提供友好提示
   - 发送错误通知

4. 性能优化
   - 使用异步操作
   - 控制并发数量
   - 优化资源使用
   - 实现定期清理 