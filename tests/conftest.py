"""测试配置"""

import os
import pytest
import asyncio
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import Generator, Any, Dict, AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy.pool import StaticPool
from loguru import logger
from fastapi import FastAPI
from httpx import AsyncClient
from redis.asyncio import Redis

from src.models import (
    Base,
    Platform,
    Tag,
    Content,
    ContentType,
    ContentStatus,
    Comment,
    GeneratedContent,
    Report,
    content_tags,
    report_contents
)
from src.database.session import async_session_factory as Session
from src.database.session import engine, async_session_factory, init_db
from .test_settings import test_settings
from src.config import Config
from src.utils.logger import setup_logger

# 创建内存数据库
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# 配置日志
logger.configure(**test_settings.get_log_config())

# 初始化日志配置
setup_logger("tests")

class TestDataFactory:
    """测试数据工厂"""
    
    @staticmethod
    def create_platform(**kwargs) -> Platform:
        """创建平台"""
        return Platform(
            name=kwargs.get('name', 'test'),
            is_active=kwargs.get('is_active', True),
            rate_limit=kwargs.get('rate_limit', 1.0),
            retry_limit=kwargs.get('retry_limit', 3),
            cookie_config=kwargs.get('cookie_config', {})
        )
    
    @staticmethod
    def create_tag(**kwargs) -> Tag:
        """创建标签"""
        return Tag(
            name=kwargs.get('name', 'test_tag'),
            description=kwargs.get('description', 'Test tag')
        )
    
    @staticmethod
    def create_content(platform: Platform, **kwargs) -> Content:
        """创建内容"""
        return Content(
            title=kwargs.get('title', 'Test content'),
            content=kwargs.get('content', 'This is test content'),
            author_name=kwargs.get('author_name', 'test_author'),
            author_id=kwargs.get('author_id', 'test_author_id'),
            platform_id=platform.id,
            url=kwargs.get('url', 'https://example.com/test'),
            images=kwargs.get('images', []),
            video=kwargs.get('video'),
            publish_time=kwargs.get('publish_time', datetime.utcnow())
        )
        
    @staticmethod
    def create_generated_content(source_content: Content, **kwargs) -> GeneratedContent:
        """创建生成内容"""
        return GeneratedContent(
            title=kwargs.get('title', 'Generated content'),
            content=kwargs.get('content', 'This is generated content'),
            content_type=kwargs.get('content_type', 'article'),
            source_content=source_content,
            format_config=kwargs.get('format_config', {}),
            generation_config=kwargs.get('generation_config', {}),
            prompt_used=kwargs.get('prompt_used', 'test prompt'),
            model_used=kwargs.get('model_used', 'test_model')
        )
        
    @staticmethod
    def create_report(**kwargs) -> Report:
        """创建报告"""
        return Report(
            title=kwargs.get('title', 'Test report'),
            summary=kwargs.get('summary', 'This is a test report'),
            report_type=kwargs.get('report_type', 'daily'),
            report_date=kwargs.get('report_date', datetime.now())
        )

@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def init_database():
    """初始化数据库"""
    await init_db()
    yield
    # 清理数据库
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session(init_database) -> AsyncGenerator[AsyncSession, None]:
    """创建数据库会话"""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()

@pytest.fixture(scope="session")
def test_data_dir(tmp_path_factory) -> Path:
    """创建测试数据目录"""
    return tmp_path_factory.mktemp("data")

@pytest.fixture(scope="session")
def test_db_config() -> Dict[str, Any]:
    """测试数据库配置"""
    return test_settings.get_test_database_config()

@pytest.fixture(scope="session")
def test_crawler_config() -> Dict[str, Any]:
    """测试爬虫配置"""
    return {
        "platform_name": "test",
        "concurrent_limit": 2,
        "retry_limit": 3,
        "timeout": 5,
        "proxy": {
            "enabled": False
        },
        "cookie": {
            "enabled": False
        }
    }

@pytest.fixture
async def sample_platform(db_session) -> Platform:
    """创建示例平台"""
    platform = Platform(
        name="test_platform",
        description="Test Platform",
        base_url="https://test.com",
        enabled=True,
        config={}
    )
    db_session.add(platform)
    await db_session.commit()
    await db_session.refresh(platform)
    return platform

@pytest.fixture
async def sample_tag(db_session) -> Tag:
    """创建示例标签"""
    tag = Tag(
        name="test_tag",
        description="Test Tag",
        level=0,
        weight=1.0
    )
    db_session.add(tag)
    await db_session.commit()
    await db_session.refresh(tag)
    return tag

@pytest.fixture
async def sample_content(db_session, sample_platform) -> Content:
    """创建示例内容"""
    content = Content(
        title="Test Content",
        content="Test content body",
        author_name="Test Author",
        author_id="test_author_id",
        platform_id=sample_platform.id,
        url="https://test.com/content/1",
        images=[],
        publish_time=datetime.now(),
        content_type=ContentType.ARTICLE,
        status=ContentStatus.DRAFT
    )
    db_session.add(content)
    await db_session.commit()
    await db_session.refresh(content)
    return content

@pytest.fixture
async def sample_generated_content(db_session, sample_content) -> GeneratedContent:
    """创建示例生成内容"""
    generated_content = TestDataFactory.create_generated_content(sample_content)
    db_session.add(generated_content)
    await db_session.commit()
    await db_session.refresh(generated_content)
    return generated_content

@pytest.fixture
async def sample_report(db_session) -> Report:
    """创建示例报告"""
    report = TestDataFactory.create_report()
    db_session.add(report)
    await db_session.commit()
    await db_session.refresh(report)
    return report

@pytest.fixture
def mock_llm_response() -> dict:
    """模拟LLM响应"""
    return {
        "success": True,
        "data": {
            "text": "这是一个测试响应",
            "score": 0.95,
            "tokens": 10,
            "model": "test_model",
            "metadata": {
                "temperature": 0.7,
                "max_tokens": 100
            }
        }
    }

@pytest.fixture
def mock_proxy_list() -> list:
    """模拟代理列表"""
    return [
        "http://proxy1.test.com:8080",
        "http://proxy2.test.com:8080",
        "http://proxy3.test.com:8080"
    ]

@pytest.fixture
def mock_cookies() -> dict:
    """模拟Cookie"""
    return {
        "session": "test_session",
        "user_id": "test_user",
        "token": "test_token"
    }

@pytest.fixture
def mock_api_response() -> dict:
    """模拟API响应"""
    return {
        "success": True,
        "data": {
            "items": [
                {
                    "id": "1",
                    "title": "测试内容1",
                    "content": "这是测试内容1"
                },
                {
                    "id": "2",
                    "title": "测试内容2",
                    "content": "这是测试内容2"
                }
            ],
            "total": 2,
            "page": 1,
            "page_size": 10
        }
    }

@pytest.fixture(scope='session')
def test_monitor_config() -> dict:
    """测试监控配置"""
    return {
        "metrics": {
            "enabled": True,
            "interval": 60,
            "exporters": ["prometheus"]
        },
        "alert": {
            "enabled": True,
            "webhook": "http://test.com/alert",
            "rules": [
                {
                    "name": "error_rate",
                    "threshold": 0.1,
                    "window": 300
                }
            ]
        }
    }

@pytest.fixture
async def crawler():
    """创建爬虫实例"""
    from src.crawlers.xiaohongshu.crawler import XiaoHongShuCrawler
    async with XiaoHongShuCrawler() as crawler:
        yield crawler

@pytest.fixture
def mock_response():
    """模拟响应数据"""
    return {
        "success": True,
        "data": {
            "time": "2024-03-27T10:00:00",
            "title": "测试笔记",
            "content": "这是一个测试笔记的内容",
            "user": {
                "id": "user1",
                "nickname": "测试用户",
                "avatar": "http://example.com/avatar.jpg"
            },
            "images": ["http://example.com/image1.jpg"],
            "video": None,
            "stats": {
                "likes": 100,
                "comments": 50,
                "collects": 30,
                "shares": 20
            },
            "type": "normal",
            "id": "note1"
        }
    }

@pytest.fixture
def mock_search_response():
    """模拟搜索响应"""
    return {
        "success": True,
        "data": {
            "notes": [
                {
                    "id": "note1",
                    "title": "测试笔记1",
                    "desc": "测试内容1",
                    "user": {"nickname": "测试用户1"},
                    "time": "2024-03-27T12:00:00",
                    "likes": 100,
                    "comments": 50,
                    "images": ["image1.jpg"],
                    "video": "video1.mp4"
                },
                {
                    "id": "note2",
                    "title": "测试笔记2",
                    "desc": "测试内容2",
                    "user": {"nickname": "测试用户2"},
                    "time": "2024-03-27T13:00:00",
                    "likes": 200,
                    "comments": 100,
                    "images": ["image2.jpg"],
                    "video": None
                }
            ]
        }
    }

@pytest.fixture
def mock_detail_response():
    """模拟详情响应"""
    return {
        "success": True,
        "data": {
            "note": {
                "id": "note1",
                "title": "测试笔记1",
                "content": "测试内容1",
                "user": {
                    "nickname": "测试用户1",
                    "avatar": "avatar1.jpg",
                    "id": "user1"
                },
                "time": "2024-03-27T12:00:00",
                "stats": {
                    "likes": 100,
                    "comments": 50,
                    "shares": 20,
                    "collects": 30
                },
                "images": ["image1.jpg"],
                "video": "video1.mp4"
            }
        }
    }

@pytest.fixture
async def storage():
    """初始化存储"""
    from src.database.sqlite_storage import SQLiteStorage
    
    # 使用测试数据库
    db_path = Path(test_settings.BASE_DIR) / "data" / "test.db"
    storage = SQLiteStorage(str(db_path))
    await storage.init()
    
    yield storage
    
    # 清理测试数据
    if db_path.exists():
        os.remove(db_path)

@pytest.fixture
async def cache():
    """初始化缓存"""
    from src.database.cache_storage import CacheStorage
    
    cache = CacheStorage(test_settings.REDIS_URL)
    await cache.init()
    
    yield cache
    
    # 清理缓存
    await cache.clear()
    await cache.close()

@pytest.fixture
async def cached_storage(storage, cache):
    """初始化带缓存的存储"""
    from src.database.cache_storage import CachedStorage
    
    cached_storage = CachedStorage(storage, cache)
    yield cached_storage

@pytest.fixture
async def perf_monitor():
    """初始化性能监控"""
    from src.monitor.performance_monitor import PerformanceMonitor
    
    monitor = PerformanceMonitor()
    await monitor.start()
    
    yield monitor
    
    await monitor.stop()

@pytest.fixture
async def business_monitor(cached_storage):
    """初始化业务监控"""
    from src.monitor.business_monitor import BusinessMonitor
    
    monitor = BusinessMonitor(cached_storage)
    await monitor.start()
    
    yield monitor
    
    await monitor.stop()

# 设置测试环境
def pytest_configure(config):
    """配置pytest环境"""
    # 加载测试环境变量
    from dotenv import load_dotenv
    load_dotenv("tests/.env.test")
    
    # 设置日志
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "DEBUG"),
        format=os.getenv("LOG_FORMAT", "%(asctime)s [%(levelname)8s] %(message)s"),
        filename=os.getenv("LOG_FILE", "./logs/test.log")
    )
    
    # 创建必要的目录
    os.makedirs("./logs", exist_ok=True)
    os.makedirs("./test_exports", exist_ok=True)

def pytest_unconfigure(config):
    """清理pytest环境"""
    # 清理测试目录
    shutil.rmtree("./test_exports", ignore_errors=True)

@pytest.fixture(scope="session")
def test_data() -> Dict[str, Any]:
    """创建测试数据"""
    return {
        "article": {
            "id": "test-article",
            "title": "测试文章",
            "author": "测试作者",
            "date": "2024-03-27",
            "category": "测试",
            "tags": ["测试", "示例"],
            "content": "这是一篇测试文章的内容。",
            "images": [
                "https://example.com/image1.jpg",
                "https://example.com/image2.jpg"
            ]
        },
        "post": {
            "id": "test-post",
            "title": "测试帖子",
            "content": "这是一个测试帖子。",
            "images": ["https://example.com/post.jpg"]
        },
        "video": {
            "id": "test-video",
            "title": "测试视频",
            "description": "这是一个测试视频。",
            "thumbnail": "https://example.com/thumbnail.jpg",
            "url": "https://example.com/video.mp4"
        }
    }

@pytest.fixture(scope="session")
def test_templates(tmp_path_factory) -> Generator[Path, None, None]:
    """创建测试模板"""
    templates_dir = tmp_path_factory.mktemp("templates")
    
    # HTML模板
    html_dir = templates_dir / "html"
    html_dir.mkdir()
    
    article_template = """
    <!DOCTYPE html>
    <html>
    <head><title>{{ title }}</title></head>
    <body><article>{{ content }}</article></body>
    </html>
    """
    (html_dir / "article.html").write_text(article_template)
    
    post_template = """
    <!DOCTYPE html>
    <html>
    <head><title>{{ title }}</title></head>
    <body><div>{{ content }}</div></body>
    </html>
    """
    (html_dir / "post.html").write_text(post_template)
    
    # PDF模板
    pdf_dir = templates_dir / "pdf"
    pdf_dir.mkdir()
    
    article_pdf_template = """
    Title: {{ title }}
    Author: {{ author }}
    ---
    {{ content }}
    """
    (pdf_dir / "article.tex").write_text(article_pdf_template)
    
    yield templates_dir
    
    # 清理
    shutil.rmtree(templates_dir)

@pytest.fixture(scope="session")
def test_resources(tmp_path_factory) -> Generator[Path, None, None]:
    """创建测试资源"""
    resources_dir = tmp_path_factory.mktemp("resources")
    
    # 创建测试图片
    image_dir = resources_dir / "images"
    image_dir.mkdir()
    
    # 创建一个1x1的黑色PNG图片
    png_data = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
        0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4,
        0x89, 0x00, 0x00, 0x00, 0x0D, 0x49, 0x44, 0x41,
        0x54, 0x78, 0x9C, 0x63, 0x00, 0x01, 0x00, 0x00,
        0x05, 0x00, 0x01, 0x0D, 0x0A, 0x2D, 0xB4, 0x00,
        0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE,
        0x42, 0x60, 0x82
    ])
    
    (image_dir / "test.png").write_bytes(png_data)
    (image_dir / "large.png").write_bytes(png_data * 1000)
    
    yield resources_dir
    
    # 清理
    shutil.rmtree(resources_dir)

@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """设置测试环境变量"""
    # 设置测试配置
    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setenv("TEST_TIMEOUT", "30")
    monkeypatch.setenv("TEST_CONCURRENT", "4")
    
    # 禁用真实的外部服务
    monkeypatch.setenv("DISABLE_EXTERNAL_SERVICES", "true")
    
    # 使用测试存储
    monkeypatch.setenv("EXPORT_STORAGE_LOCAL_PATH", "./test_exports")
    monkeypatch.setenv("EXPORT_STORAGE_S3_BUCKET", "test-exports")

@pytest.fixture
def mock_external_services(mocker):
    """模拟外部服务"""
    # 模拟图片下载
    async def mock_download(*args, **kwargs):
        return b"fake image data"
    
    mocker.patch("src.utils.http.download_file", side_effect=mock_download)
    
    # 模拟S3操作
    mocker.patch("boto3.client")
    
    # 模拟监控指标
    mocker.patch("prometheus_client.Counter")
    mocker.patch("prometheus_client.Gauge")
    mocker.patch("prometheus_client.Histogram")

@pytest.fixture(scope="session")
async def app() -> FastAPI:
    """创建测试应用。

    Returns:
        FastAPI应用实例
    """
    from src.main import app
    return app

@pytest.fixture(scope="session")
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """创建测试客户端。

    Args:
        app: FastAPI应用实例

    Returns:
        异步HTTP客户端生成器
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture(scope="session")
async def redis_client() -> AsyncGenerator[Redis, None]:
    """Redis客户端"""
    client = Redis(
        host="localhost",
        port=6379,
        db=0,
        decode_responses=True
    )
    try:
        yield client
    finally:
        await client.close()

@pytest.fixture(autouse=True)
async def initialize_tests():
    """初始化测试环境"""
    # 设置测试环境变量
    os.environ["TESTING"] = "True"
    
    # 初始化测试数据库
    await init_db(is_test=True)
    
    yield

@pytest.fixture
def config() -> Config:
    """获取配置对象"""
    return Config() 