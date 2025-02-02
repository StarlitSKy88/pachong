import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError
import uuid

from src.models.content import Content
from src.models.tag import Tag
from src.models.platform import Platform
from src.models.generated_content import GeneratedContent
from src.models.report import Report

class TestContent:
    """内容模型测试"""
    
    def test_create_content(self, db_session, sample_platform):
        """测试创建内容"""
        content = Content(
            platform=sample_platform,
            title="Test Title",
            content="Test Content",
            url="https://test.com/content/123"
        )
        db_session.add(content)
        db_session.commit()
        
        assert content.id is not None
        assert content.platform.id == sample_platform.id
        assert content.title == "Test Title"
        assert content.created_at is not None
    
    def test_content_platform_required(self, db_session):
        """测试平台字段必填"""
        content = Content(
            title="Test Title",
            content="Test Content"
        )
        db_session.add(content)
        with pytest.raises(IntegrityError, match=r".*platform_id.*"):
            db_session.commit()
    
    def test_content_relationships(self, db_session, sample_content, sample_tag):
        """测试内容关联关系"""
        # 测试标签关联
        sample_content.tags.append(sample_tag)
        db_session.commit()
        
        assert len(sample_content.tags) == 1
        assert sample_content.tags[0].name == sample_tag.name
        
        # 测试平台关联
        assert sample_content.platform is not None
        assert sample_content.platform.id == sample_content.platform_id
    
    def test_content_to_dict(self, sample_content):
        """测试转换为字典"""
        data = sample_content.to_dict()
        
        assert data['platform_id'] == sample_content.platform_id
        assert data['title'] == sample_content.title
        assert data['content'] == sample_content.content
        assert isinstance(data['created_at'], str)

class TestTag:
    """标签模型测试"""
    
    def test_create_tag(self, db_session):
        """测试创建标签"""
        tag = Tag(
            name="test_tag",
            description="Test Tag",
            category="test"
        )
        db_session.add(tag)
        db_session.commit()
        
        assert tag.id is not None
        assert tag.name == "test_tag"
        assert tag.created_at is not None
    
    def test_tag_unique_name(self, db_session, sample_tag):
        """测试标签名称唯一"""
        tag = Tag(name=sample_tag.name)
        db_session.add(tag)
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_tag_relationships(self, db_session, sample_tag, sample_content):
        """测试标签关联关系"""
        sample_tag.contents.append(sample_content)
        db_session.commit()
        
        assert len(sample_tag.contents) == 1
        assert sample_tag.contents[0].id == sample_content.id
    
    def test_tag_to_dict(self, sample_tag):
        """测试转换为字典"""
        data = sample_tag.to_dict()
        
        assert data['name'] == sample_tag.name
        assert data['description'] == sample_tag.description
        assert data['category'] == sample_tag.category
        assert isinstance(data['created_at'], str)

class TestPlatform:
    """平台模型测试"""
    
    def test_create_platform(self, db_session):
        """测试创建平台"""
        platform = Platform(
            name="test_platform",
            description="Test Platform",
            base_url="https://test.com",
            api_base_url="https://api.test.com"
        )
        db_session.add(platform)
        db_session.commit()
        
        assert platform.id is not None
        assert platform.name == "test_platform"
        assert platform.created_at is not None
    
    def test_platform_unique_name(self, db_session, sample_platform):
        """测试平台名称唯一"""
        platform = Platform(name=sample_platform.name)
        db_session.add(platform)
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_platform_relationships(self, db_session, sample_platform, sample_content):
        """测试平台关联关系"""
        assert len(sample_platform.contents) == 1
        assert sample_platform.contents[0].id == sample_content.id
    
    def test_platform_to_dict(self, sample_platform):
        """测试转换为字典"""
        data = sample_platform.to_dict()
        
        assert data['name'] == sample_platform.name
        assert data['description'] == sample_platform.description
        assert data['base_url'] == sample_platform.base_url
        assert data['api_base_url'] == sample_platform.api_base_url
        assert isinstance(data['created_at'], str)

class TestGeneratedContent:
    """生成内容模型测试"""
    
    def test_create_generated_content(self, db_session, sample_content):
        """测试创建生成内容"""
        generated = GeneratedContent(
            title="Generated Title",
            content="Generated Content",
            content_type="xiaohongshu",
            source_content_id=sample_content.id
        )
        db_session.add(generated)
        db_session.commit()
        
        assert generated.id is not None
        assert generated.title == "Generated Title"
        assert generated.created_at is not None
    
    def test_generated_content_relationships(self, db_session, sample_generated_content):
        """测试生成内容关联关系"""
        assert sample_generated_content.source_content is not None
        assert sample_generated_content.source_content.id == sample_generated_content.source_content_id
    
    def test_generated_content_to_dict(self, sample_generated_content):
        """测试转换为字典"""
        data = sample_generated_content.to_dict()
        
        assert data['title'] == sample_generated_content.title
        assert data['content'] == sample_generated_content.content
        assert data['content_type'] == sample_generated_content.content_type
        assert data['source_content_id'] == sample_generated_content.source_content_id
        assert isinstance(data['created_at'], str)

@pytest.mark.asyncio
async def test_tag_model(db_session):
    """测试标签模型"""
    tag_name = f"test_tag_{uuid.uuid4().hex[:8]}"
    tag = Tag(
        name=tag_name,
        description="测试标签",
        category="test",
        weight=1.0
    )
    db_session.add(tag)
    db_session.commit()

    assert tag.name == tag_name
    assert tag.description == "测试标签"
    assert tag.category == "test"
    assert tag.weight == 1.0
    assert tag.usage_count == 0
    assert tag.created_at is not None
    assert tag.updated_at is not None
    
    # 创建平台
    platform = Platform(
        name="test_platform",
        description="测试平台",
        base_url="https://test.com",
        api_base_url="https://api.test.com",
        crawler_config={},
        api_config={},
        cookie_config={},
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()
    
    # 创建内容并关联标签
    content1 = Content(
        title="测试标题1",
        content="测试内容1",
        url="https://test.com/1",
        platform=platform
    )
    content1.tags.append(tag)
    
    content2 = Content(
        title="测试标题2",
        content="测试内容2",
        url="https://test.com/2",
        platform=platform
    )
    content2.tags.append(tag)
    
    db_session.add(content1)
    db_session.add(content2)
    db_session.commit()
    
    # 验证关联关系
    assert len(tag.contents) == 2
    assert content1 in tag.contents
    assert content2 in tag.contents
    assert tag.contents[0].title == "测试标题1"
    assert tag.contents[1].title == "测试标题2"
    
    # 测试标签权重更新
    tag.weight = 2.0
    db_session.commit()
    assert tag.weight == 2.0

@pytest.mark.asyncio
async def test_platform_model(db_session):
    """测试平台模型"""
    # 创建平台
    platform = Platform(
        name=f"test_platform_{uuid.uuid4().hex[:8]}",
        description="测试平台",
        base_url="https://test.com",
        api_base_url="https://api.test.com",
        crawler_config={
            "rate_limit": 1,
            "retry_limit": 3
        },
        api_config={
            "version": "v1",
            "timeout": 30
        },
        cookie_config={
            "domain": "test.com",
            "path": "/"
        },
        is_active=True,
        error_count=0,
        last_error=None,
        crawl_interval=3600,
        rate_limit=1.0,
        retry_limit=3
    )
    db_session.add(platform)
    db_session.commit()
    
    # 验证平台
    assert platform.name.startswith("test_platform_")
    assert platform.description == "测试平台"
    assert platform.base_url == "https://test.com"
    assert platform.api_base_url == "https://api.test.com"
    assert platform.crawler_config["rate_limit"] == 1
    assert platform.crawler_config["retry_limit"] == 3
    assert platform.api_config["version"] == "v1"
    assert platform.api_config["timeout"] == 30
    assert platform.cookie_config["domain"] == "test.com"
    assert platform.cookie_config["path"] == "/"
    assert platform.is_active is True
    assert platform.error_count == 0
    assert platform.last_error is None
    assert platform.crawl_interval == 3600
    assert platform.rate_limit == 1.0
    assert platform.retry_limit == 3
    
    # 创建内容
    content = Content(
        title="测试标题",
        content="测试内容",
        url="https://test.com/1",
        platform=platform
    )
    db_session.add(content)
    db_session.commit()
    
    # 验证关联关系
    assert content in platform.contents
    assert len(platform.contents) == 1
    assert platform.contents[0].title == "测试标题"
    
    # 测试错误计数
    platform.error_count += 1
    platform.last_error = "测试错误"
    db_session.commit()
    
    assert platform.error_count == 1
    assert platform.last_error == "测试错误"

@pytest.mark.asyncio
async def test_content_model(db_session):
    """测试内容模型"""
    # 创建平台
    platform = Platform(
        name=f"test_platform_{uuid.uuid4().hex[:8]}",
        description="测试平台",
        base_url="https://test.com",
        api_base_url="https://api.test.com",
        crawler_config={},
        api_config={},
        cookie_config={},
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()
    
    # 创建标签
    tag = Tag(
        name=f"test_tag_{uuid.uuid4().hex[:8]}",
        description="测试标签",
        category="test",
        weight=1.0
    )
    db_session.add(tag)
    db_session.commit()
    
    # 创建内容
    content = Content(
        title="测试标题",
        content="测试内容",
        url="https://test.com/1",
        platform=platform,
        author={"name": "测试作者", "id": "123"},
        images=["image1.jpg", "image2.jpg"],
        video_url="https://test.com/video.mp4",
        cover="cover.jpg",
        views=100,
        likes=50,
        comments=20,
        shares=10,
        collects=5,
        status=1
    )
    content.tags.append(tag)
    db_session.add(content)
    db_session.commit()
    
    # 验证内容
    assert content.title == "测试标题"
    assert content.content == "测试内容"
    assert content.url == "https://test.com/1"
    assert content.platform.name == platform.name
    assert content.author["name"] == "测试作者"
    assert content.author["id"] == "123"
    assert len(content.images) == 2
    assert content.video_url == "https://test.com/video.mp4"
    assert content.cover == "cover.jpg"
    assert content.views == 100
    assert content.likes == 50
    assert content.comments == 20
    assert content.shares == 10
    assert content.collects == 5
    assert content.status == 1
    assert len(content.tags) == 1
    assert content.tags[0].name == tag.name
    
    # 测试关联关系
    assert content in platform.contents
    assert content in tag.contents
    
    # 创建报告
    report = Report(
        title="测试报告",
        summary="测试报告摘要",
        report_type="daily",
        report_date=datetime.now()
    )
    report.contents.append(content)
    db_session.add(report)
    db_session.commit()
    
    # 验证报告关联
    assert content in report.contents
    assert report in content.reports

@pytest.mark.asyncio
async def test_report_model(db_session):
    """测试报告模型"""
    # 创建平台
    platform = Platform(
        name=f"test_platform_{uuid.uuid4().hex[:8]}",
        description="测试平台",
        base_url="https://test.com",
        api_base_url="https://api.test.com",
        crawler_config={},
        api_config={},
        cookie_config={},
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()
    
    # 创建内容
    content1 = Content(
        title="测试标题1",
        content="测试内容1",
        url="https://test.com/1",
        platform=platform
    )
    content2 = Content(
        title="测试标题2",
        content="测试内容2",
        url="https://test.com/2",
        platform=platform
    )
    db_session.add(content1)
    db_session.add(content2)
    db_session.commit()
    
    # 创建报告
    report = Report(
        title="测试报告",
        summary="测试报告摘要",
        report_type="daily",
        report_date=datetime.now(),
        status=0  # 草稿状态
    )
    report.contents.extend([content1, content2])
    db_session.add(report)
    db_session.commit()
    
    # 验证报告
    assert report.title == "测试报告"
    assert report.summary == "测试报告摘要"
    assert report.report_type == "daily"
    assert isinstance(report.report_date, datetime)
    assert report.status == 0
    assert len(report.contents) == 2
    assert content1 in report.contents
    assert content2 in report.contents
    
    # 测试报告状态更新
    report.status = 1  # 发布状态
    db_session.commit()
    assert report.status == 1
    
    # 测试报告字典转换
    report_dict = report.to_dict()
    assert report_dict['title'] == "测试报告"
    assert report_dict['summary'] == "测试报告摘要"
    assert report_dict['report_type'] == "daily"
    assert isinstance(report_dict['report_date'], str)
    assert report_dict['status'] == 1
    assert len(report_dict['contents']) == 2
    assert report_dict['contents'][0]['title'] == "测试标题1"
    assert report_dict['contents'][1]['title'] == "测试标题2" 