"""导出功能测试

该模块包含导出功能的测试用例，包括：
1. 基础导出功能测试
2. HTML格式导出测试
3. 批量导出测试
4. 资源处理测试
5. 错误处理测试
"""

import os
import json
import pytest
import asyncio
import aiohttp
from pathlib import Path
from bs4 import BeautifulSoup
from unittest.mock import Mock, patch, AsyncMock
from src.export.base import ExportManager, ExportError
from src.export.html import HTMLExport

# 测试数据
TEST_CONFIG = {
    "version": "1.0",
    "formats": {
        "html": {
            "enabled": True,
            "template_dir": "templates/html",
            "resource_dir": "resources",
            "default_style": "style.css",
            "image_quality": 85,
            "max_image_size": 1920,
            "batch_concurrency": 2,
            "create_index": True
        }
    },
    "storage": {
        "local": {
            "path": "exports",
            "cleanup_threshold": "1GB",
            "cleanup_age": "7d"
        },
        "s3": {
            "enabled": False
        }
    },
    "notification": {
        "enabled": True,
        "events": ["export.start", "export.complete", "export.error"],
        "channels": {
            "webhook": {
                "enabled": True,
                "url": "http://example.com/webhook",
                "headers": {
                    "Authorization": "Bearer test"
                }
            }
        }
    }
}

TEST_ARTICLE = {
    "title": "测试文章",
    "author": "测试作者",
    "date": "2024-03-27",
    "category": "测试分类",
    "tags": ["测试", "示例"],
    "content": """
    <h2>测试标题</h2>
    <p>这是一段测试内容，包含一张图片：</p>
    <img src="https://example.com/test.jpg" alt="测试图片">
    <p>这是另一段内容。</p>
    """
}

@pytest.fixture
def config_file(tmp_path):
    """创建测试配置文件"""
    config_path = tmp_path / "export.json"
    with open(config_path, "w") as f:
        json.dump(TEST_CONFIG, f)
    return str(config_path)

@pytest.fixture
def template_dir(tmp_path):
    """创建测试模板目录"""
    template_dir = tmp_path / "templates" / "html"
    template_dir.mkdir(parents=True)
    
    # 创建文章模板
    article_template = template_dir / "article.html"
    article_template.write_text("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{{ title }}</title>
    </head>
    <body>
        <h1>{{ title }}</h1>
        <div class="meta">
            <span>{{ author }}</span>
            <span>{{ date }}</span>
            <span>{{ category }}</span>
            <span>{{ tags|join(', ') }}</span>
        </div>
        <div class="content">
            {{ content|safe }}
        </div>
    </body>
    </html>
    """)
    
    # 创建索引模板
    index_template = template_dir / "index.html"
    index_template.write_text("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>文章列表</title>
    </head>
    <body>
        <h1>文章列表</h1>
        <div class="article-list">
            {% for item in items %}
            <div class="article-card">
                <h2><a href="{{ item.path }}">{{ item.title }}</a></h2>
            </div>
            {% endfor %}
        </div>
    </body>
    </html>
    """)
    
    return template_dir

@pytest.fixture
def export_manager(config_file, template_dir):
    """创建导出管理器"""
    manager = ExportManager(config_file)
    manager.register_format("html", HTMLExport)
    return manager

@pytest.mark.asyncio
async def test_export_article(export_manager, tmp_path):
    """测试文章导出"""
    output_path = str(tmp_path / "test.html")
    
    # 模拟图片下载
    async def mock_get(*args, **kwargs):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=b"fake image data")
        return mock_response
    
    with patch("aiohttp.ClientSession.get", mock_get):
        await export_manager.export(
            TEST_ARTICLE,
            "html",
            "article",
            output_path
        )
    
    # 验证输出文件
    assert os.path.exists(output_path)
    
    # 验证内容
    with open(output_path) as f:
        content = f.read()
        soup = BeautifulSoup(content, "html.parser")
        
        # 验证标题
        assert soup.title.string == TEST_ARTICLE["title"]
        assert soup.h1.string == TEST_ARTICLE["title"]
        
        # 验证元信息
        meta = soup.find("div", class_="meta")
        assert TEST_ARTICLE["author"] in meta.text
        assert TEST_ARTICLE["date"] in meta.text
        assert TEST_ARTICLE["category"] in meta.text
        assert all(tag in meta.text for tag in TEST_ARTICLE["tags"])
        
        # 验证图片处理
        img = soup.find("img")
        assert img["src"].startswith("images/")
        assert os.path.exists(tmp_path / img["src"])

@pytest.mark.asyncio
async def test_batch_export(export_manager, tmp_path):
    """测试批量导出"""
    output_dir = str(tmp_path / "batch")
    articles = [
        {**TEST_ARTICLE, "title": f"测试文章 {i}"}
        for i in range(5)
    ]
    
    # 模拟图片下载
    async def mock_get(*args, **kwargs):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=b"fake image data")
        return mock_response
    
    with patch("aiohttp.ClientSession.get", mock_get):
        await export_manager.batch_export(
            articles,
            "html",
            "article",
            output_dir
        )
    
    # 验证输出文件
    assert os.path.exists(output_dir)
    assert len(os.listdir(output_dir)) == 6  # 5篇文章 + 1个索引页
    
    # 验证索引页
    index_path = os.path.join(output_dir, "index.html")
    assert os.path.exists(index_path)
    
    with open(index_path) as f:
        content = f.read()
        soup = BeautifulSoup(content, "html.parser")
        
        # 验证文章列表
        articles = soup.find_all("div", class_="article-card")
        assert len(articles) == 5
        
        # 验证链接
        links = [a["href"] for a in soup.find_all("a")]
        assert all(f"{i + 1}.html" in links for i in range(5))

@pytest.mark.asyncio
async def test_export_error_handling(export_manager, tmp_path):
    """测试错误处理"""
    output_path = str(tmp_path / "error.html")
    
    # 测试模板不存在
    with pytest.raises(ExportError) as exc:
        await export_manager.export(
            TEST_ARTICLE,
            "html",
            "not_exists",
            output_path
        )
    assert "Template not found" in str(exc.value)
    
    # 测试图片下载失败
    async def mock_get(*args, **kwargs):
        mock_response = AsyncMock()
        mock_response.status = 404
        return mock_response
    
    with patch("aiohttp.ClientSession.get", mock_get):
        await export_manager.export(
            TEST_ARTICLE,
            "html",
            "article",
            output_path
        )
    
    # 验证输出文件仍然生成
    assert os.path.exists(output_path)
    
    # 验证图片链接被保留
    with open(output_path) as f:
        content = f.read()
        soup = BeautifulSoup(content, "html.parser")
        img = soup.find("img")
        assert img["src"] == "https://example.com/test.jpg"

@pytest.mark.asyncio
async def test_notification(export_manager, tmp_path):
    """测试通知功能"""
    output_path = str(tmp_path / "test.html")
    
    # 记录通知
    notifications = []
    
    async def mock_post(*args, **kwargs):
        notifications.append(kwargs["json"])
        mock_response = AsyncMock()
        mock_response.status = 200
        return mock_response
    
    with patch("aiohttp.ClientSession.post", mock_post):
        await export_manager.export(
            TEST_ARTICLE,
            "html",
            "article",
            output_path
        )
    
    # 验证通知
    assert len(notifications) == 2  # start + complete
    assert notifications[0]["event"] == "export.start"
    assert notifications[1]["event"] == "export.complete"
    
    # 测试错误通知
    with patch("aiohttp.ClientSession.post", mock_post):
        with pytest.raises(ExportError):
            await export_manager.export(
                TEST_ARTICLE,
                "html",
                "not_exists",
                output_path
            )
    
    # 验证错误通知
    assert len(notifications) == 5  # start + error + start + error
    assert notifications[-1]["event"] == "export.error"
    assert "error" in notifications[-1]["data"] 