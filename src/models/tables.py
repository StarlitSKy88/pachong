"""数据库表定义模块。"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean, Float, Enum, Table
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from .base import Base, BaseModel
from .enums import ContentType, ContentStatus

# 关联表定义
content_tags = Table(
    'content_tags',
    Base.metadata,
    Column('content_id', Integer, ForeignKey('contents.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True),
    extend_existing=True
)

report_contents = Table(
    'report_contents',
    Base.metadata,
    Column('report_id', Integer, ForeignKey('reports.id'), primary_key=True),
    Column('content_id', Integer, ForeignKey('contents.id'), primary_key=True),
    extend_existing=True
)

# 模型定义
class Platform(BaseModel):
    """平台模型"""
    __tablename__ = 'platforms'
    
    name = Column(String(50), unique=True, nullable=False, comment='平台名称')
    description = Column(String(200), nullable=True, comment='平台描述')
    base_url = Column(String(200), nullable=False, comment='平台基础URL')
    enabled = Column(Boolean, default=True, nullable=False, comment='是否启用')
    config = Column(JSON, nullable=True, comment='平台配置')
    
    # 关联关系
    contents = relationship('Content', back_populates='platform')

class Tag(BaseModel):
    """标签模型"""
    __tablename__ = 'tags'

    name = Column(String(50), unique=True, nullable=False, comment='标签名称')
    description = Column(String(200), nullable=True, comment='标签描述')
    parent_id = Column(Integer, ForeignKey('tags.id'), nullable=True, comment='父标签ID')
    level = Column(Integer, default=0, nullable=False, comment='标签层级')
    weight = Column(Float, default=1.0, nullable=False, comment='标签权重')
    
    # 关联关系
    parent = relationship('Tag', remote_side=[id], backref='children')
    contents = relationship('Content', secondary=content_tags, back_populates='tags')

class Content(BaseModel):
    """内容模型"""
    __tablename__ = 'contents'

    title = Column(String(200), nullable=False, comment='标题')
    content = Column(Text, nullable=False, comment='内容')
    author_name = Column(String(100), nullable=False, comment='作者名称')
    author_id = Column(String(100), nullable=False, comment='作者ID')
    platform_id = Column(Integer, ForeignKey('platforms.id'), nullable=False, comment='平台ID')
    url = Column(String(500), nullable=False, comment='原始链接')
    images = Column(JSON, default=[], nullable=False, comment='图片列表')
    video = Column(String(500), nullable=True, comment='视频链接')
    publish_time = Column(DateTime, nullable=False, comment='发布时间')
    content_type = Column(Enum(ContentType), nullable=False, default=ContentType.ARTICLE, comment='内容类型')
    status = Column(Enum(ContentStatus), nullable=False, default=ContentStatus.DRAFT, comment='内容状态')
    cover_image = Column(String(500), nullable=True, comment='封面图片')
    summary = Column(String(500), nullable=True, comment='摘要')
    word_count = Column(Integer, default=0, nullable=False, comment='字数')
    read_time = Column(Integer, default=0, nullable=False, comment='阅读时间(秒)')
    is_original = Column(Boolean, default=True, nullable=False, comment='是否原创')
    is_premium = Column(Boolean, default=False, nullable=False, comment='是否优质内容')
    is_sensitive = Column(Boolean, default=False, nullable=False, comment='是否敏感内容')
    meta_info = Column(JSON, nullable=True, comment='元数据')
    stats = Column(JSON, nullable=True, comment='统计数据')
    score = Column(Float, default=0.0, nullable=False, comment='内容评分')
    quality_check = Column(JSON, nullable=True, comment='质量检查结果')
    keywords = Column(JSON, nullable=True, comment='关键词')
    categories = Column(JSON, nullable=True, comment='分类')
    language = Column(String(10), nullable=True, comment='语言')

    # 关系
    platform = relationship('Platform', back_populates='contents')
    tags = relationship('Tag', secondary=content_tags, back_populates='contents')
    comments = relationship('Comment', back_populates='content')
    reports = relationship('Report', secondary=report_contents, back_populates='contents')
    generated_contents = relationship('GeneratedContent', back_populates='source_content')

class Comment(BaseModel):
    """评论模型"""
    __tablename__ = 'comments'

    content_id = Column(Integer, ForeignKey('contents.id'), nullable=False, comment='内容ID')
    parent_id = Column(Integer, ForeignKey('comments.id'), nullable=True, comment='父评论ID')
    user_id = Column(String(100), nullable=False, comment='用户ID')
    username = Column(String(100), nullable=True, comment='用户名')
    content = Column(String(1000), nullable=False, comment='评论内容')
    likes = Column(Integer, default=0, nullable=False, comment='点赞数')
    replies = Column(Integer, default=0, nullable=False, comment='回复数')
    is_top = Column(Boolean, default=False, nullable=False, comment='是否置顶')
    status = Column(String(20), default='normal', nullable=False, comment='状态')
    meta_info = Column(JSON, nullable=True, comment='元数据')

    # 关系
    parent = relationship('Comment', remote_side=[id], backref='children')
    content = relationship('Content', back_populates='comments')

class GeneratedContent(BaseModel):
    """生成内容模型"""
    __tablename__ = 'generated_contents'

    title = Column(String(200), nullable=False, comment='标题')
    content = Column(Text, nullable=False, comment='内容')
    content_type = Column(String(50), nullable=False, comment='内容类型')
    source_content_id = Column(Integer, ForeignKey('contents.id'), nullable=False, comment='原始内容ID')
    format_config = Column(JSON, default={}, nullable=False, comment='格式配置')
    generation_config = Column(JSON, default={}, nullable=False, comment='生成配置')
    prompt_used = Column(Text, nullable=False, comment='使用的提示词')
    model_used = Column(String(100), nullable=False, comment='使用的模型')
    
    # 关联关系
    source_content = relationship('Content', back_populates='generated_contents')

class Report(BaseModel):
    """报告模型"""
    __tablename__ = 'reports'

    title = Column(String(200), nullable=False, comment='标题')
    summary = Column(Text, nullable=False, comment='摘要')
    report_type = Column(String(50), nullable=False, comment='报告类型')
    report_date = Column(DateTime, nullable=False, comment='报告日期')
    create_time = Column(DateTime, default=func.now())
    update_time = Column(DateTime, default=func.now(), onupdate=func.now())
    status = Column(Integer, default=0)  # 0: 草稿, 1: 已发布

    # 关联关系
    contents = relationship('Content', secondary=report_contents, back_populates='reports')