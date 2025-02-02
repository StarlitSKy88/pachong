"""测试配置"""

import os
import pytest
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Generator, Any, Dict, AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy.pool import StaticPool

from src.models import Base
from src.models.platform import Platform
from src.models.content import Content
from src.models.tag import Tag
from src.models.generated_content import GeneratedContent
from src.models.report import Report
from src.database.session import async_session_factory as Session

# 创建内存数据库
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

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
async def engine():
    """创建数据库引擎"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=StaticPool,
        echo=False
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture(scope="session")
def session_factory(engine):
    """创建会话工厂"""
    return sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

@pytest.fixture
async def db_session(session_factory) -> AsyncGenerator[AsyncSession, None]:
    """创建数据库会话"""
    async with session_factory() as session:
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
    return {
        "url": TEST_DATABASE_URL,
        "engine_kwargs": {
            "poolclass": StaticPool,
            "echo": False
        }
    }

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
    platform = TestDataFactory.create_platform()
    db_session.add(platform)
    await db_session.commit()
    await db_session.refresh(platform)
    return platform

@pytest.fixture
async def sample_tag(db_session) -> Tag:
    """创建示例标签"""
    tag = TestDataFactory.create_tag()
    db_session.add(tag)
    await db_session.commit()
    await db_session.refresh(tag)
    return tag

@pytest.fixture
async def sample_content(db_session, sample_platform) -> Content:
    """创建示例内容"""
    content = TestDataFactory.create_content(sample_platform)
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