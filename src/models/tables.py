"""数据库表定义模块。"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, 
    JSON, Boolean, Float, Enum, Table
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from .base import Base
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

content_categories = Table(
    'content_categories',
    Base.metadata,
    Column('content_id', Integer, ForeignKey('contents.id'), primary_key=True),
    Column('category_id', Integer, ForeignKey('categories.id'), primary_key=True),
    extend_existing=True
)

# 模型定义
class Platform(Base):
    """平台模型"""
    __tablename__ = 'platforms'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False, comment='平台名称')
    description = Column(String(200), nullable=True, comment='平台描述')
    base_url = Column(String(200), nullable=False, comment='平台基础URL')
    enabled = Column(Boolean, default=True, nullable=False, comment='是否启用')
    config = Column(JSON, nullable=True, comment='平台配置')
    create_time = Column(DateTime, default=func.now())
    update_time = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关联关系
    contents = relationship('Content', back_populates='platform')

class Tag(Base):
    """标签模型"""
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False, comment='标签名称')
    description = Column(String(200), nullable=True, comment='标签描述')
    parent_id = Column(Integer, ForeignKey('tags.id'), nullable=True, comment='父标签ID')
    level = Column(Integer, default=0, nullable=False, comment='标签层级')
    weight = Column(Float, default=1.0, nullable=False, comment='标签权重')
    create_time = Column(DateTime, default=func.now())
    update_time = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关联关系
    parent = relationship('Tag', remote_side=[id], backref='children')
    contents = relationship('Content', secondary=content_tags, back_populates='tags')

class Category(Base):
    """分类模型"""
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False, comment='分类名称')
    description = Column(String(200), nullable=True, comment='分类描述')
    parent_id = Column(Integer, ForeignKey('categories.id'), nullable=True, comment='父分类ID')
    level = Column(Integer, default=0, nullable=False, comment='分类层级')
    weight = Column(Float, default=1.0, nullable=False, comment='分类权重')
    create_time = Column(DateTime, default=func.now())
    update_time = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关联关系
    parent = relationship('Category', remote_side=[id], backref='children')
    contents = relationship('Content', secondary=content_categories, back_populates='categories')

class Content(Base):
    """内容模型"""
    __tablename__ = 'contents'

    id = Column(Integer, primary_key=True, autoincrement=True)
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
    language = Column(String(10), nullable=True, comment='语言')
    create_time = Column(DateTime, default=func.now())
    update_time = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关系
    platform = relationship('Platform', back_populates='contents')
    tags = relationship('Tag', secondary=content_tags, back_populates='contents')
    categories = relationship('Category', secondary=content_categories, back_populates='contents')
    comments = relationship('Comment', back_populates='content')
    reports = relationship('Report', secondary=report_contents, back_populates='contents')
    generated_contents = relationship('GeneratedContent', back_populates='source_content')

class Comment(Base):
    """评论模型"""
    __tablename__ = 'comments'

    id = Column(Integer, primary_key=True, autoincrement=True)
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
    create_time = Column(DateTime, default=func.now())
    update_time = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关系
    parent = relationship('Comment', remote_side=[id], backref='children')
    content = relationship('Content', back_populates='comments')

class GeneratedContent(Base):
    """生成内容模型"""
    __tablename__ = 'generated_contents'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False, comment='标题')
    content = Column(Text, nullable=False, comment='内容')
    content_type = Column(String(50), nullable=False, comment='内容类型')
    source_content_id = Column(Integer, ForeignKey('contents.id'), nullable=False, comment='原始内容ID')
    format_config = Column(JSON, default={}, nullable=False, comment='格式配置')
    generation_config = Column(JSON, default={}, nullable=False, comment='生成配置')
    prompt_used = Column(Text, nullable=False, comment='使用的提示词')
    model_used = Column(String(100), nullable=False, comment='使用的模型')
    create_time = Column(DateTime, default=func.now())
    update_time = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关联关系
    source_content = relationship('Content', back_populates='generated_contents')

class Report(Base):
    """报告模型"""
    __tablename__ = 'reports'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False, comment='标题')
    summary = Column(Text, nullable=False, comment='摘要')
    report_type = Column(String(50), nullable=False, comment='报告类型')
    report_date = Column(DateTime, nullable=False, comment='报告日期')
    create_time = Column(DateTime, default=func.now())
    update_time = Column(DateTime, default=func.now(), onupdate=func.now())
    status = Column(Integer, default=0)  # 0: 草稿, 1: 已发布

    # 关联关系
    contents = relationship('Content', secondary=report_contents, back_populates='reports')

class Task(Base):
    """任务模型"""
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment='任务名称')
    task_type = Column(String(50), nullable=False, comment='任务类型')
    platform_id = Column(Integer, ForeignKey('platforms.id'), nullable=False, comment='平台ID')
    config = Column(JSON, nullable=True, comment='任务配置')
    schedule = Column(JSON, nullable=True, comment='调度配置')
    enabled = Column(Boolean, default=True, nullable=False, comment='是否启用')
    priority = Column(Integer, default=0, nullable=False, comment='优先级')
    retry_times = Column(Integer, default=3, nullable=False, comment='重试次数')
    retry_interval = Column(Integer, default=60, nullable=False, comment='重试间隔(秒)')
    timeout = Column(Integer, default=300, nullable=False, comment='超时时间(秒)')
    last_run_time = Column(DateTime, nullable=True, comment='上次运行时间')
    next_run_time = Column(DateTime, nullable=True, comment='下次运行时间')
    create_time = Column(DateTime, default=func.now())
    update_time = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关联关系
    platform = relationship('Platform')
    logs = relationship('TaskLog', back_populates='task')

class TaskLog(Base):
    """任务日志模型"""
    __tablename__ = 'task_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False, comment='任务ID')
    status = Column(String(20), nullable=False, comment='状态')
    start_time = Column(DateTime, nullable=False, comment='开始时间')
    end_time = Column(DateTime, nullable=True, comment='结束时间')
    duration = Column(Integer, nullable=True, comment='执行时长(秒)')
    error = Column(Text, nullable=True, comment='错误信息')
    result = Column(JSON, nullable=True, comment='执行结果')
    create_time = Column(DateTime, default=func.now())
    update_time = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关联关系
    task = relationship('Task', back_populates='logs')

class Cookie(Base):
    """Cookie模型"""
    __tablename__ = 'cookies'

    id = Column(Integer, primary_key=True, autoincrement=True)
    platform_id = Column(Integer, ForeignKey('platforms.id'), nullable=False, comment='平台ID')
    value = Column(Text, nullable=False, comment='Cookie值')
    user_agent = Column(String(500), nullable=True, comment='User-Agent')
    ip = Column(String(50), nullable=True, comment='IP地址')
    score = Column(Float, default=100.0, nullable=False, comment='评分')
    last_use_time = Column(DateTime, nullable=True, comment='最后使用时间')
    expire_time = Column(DateTime, nullable=True, comment='过期时间')
    is_valid = Column(Boolean, default=True, nullable=False, comment='是否有效')
    create_time = Column(DateTime, default=func.now())
    update_time = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关联关系
    platform = relationship('Platform')

class Proxy(Base):
    """代理模型"""
    __tablename__ = 'proxies'

    id = Column(Integer, primary_key=True, autoincrement=True)
    host = Column(String(100), nullable=False, comment='主机地址')
    port = Column(Integer, nullable=False, comment='端口')
    protocol = Column(String(10), nullable=False, comment='协议')
    username = Column(String(100), nullable=True, comment='用户名')
    password = Column(String(100), nullable=True, comment='密码')
    location = Column(String(100), nullable=True, comment='地理位置')
    score = Column(Float, default=100.0, nullable=False, comment='评分')
    last_check_time = Column(DateTime, nullable=True, comment='最后检查时间')
    success_count = Column(Integer, default=0, nullable=False, comment='成功次数')
    fail_count = Column(Integer, default=0, nullable=False, comment='失败次数')
    is_valid = Column(Boolean, default=True, nullable=False, comment='是否有效')
    create_time = Column(DateTime, default=func.now())
    update_time = Column(DateTime, default=func.now(), onupdate=func.now())

class Request(Base):
    """请求模型"""
    __tablename__ = 'requests'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False, comment='任务ID')
    url = Column(String(500), nullable=False, comment='请求URL')
    method = Column(String(10), nullable=False, comment='请求方法')
    headers = Column(JSON, nullable=True, comment='请求头')
    params = Column(JSON, nullable=True, comment='URL参数')
    data = Column(JSON, nullable=True, comment='请求数据')
    proxy_id = Column(Integer, ForeignKey('proxies.id'), nullable=True, comment='代理ID')
    cookie_id = Column(Integer, ForeignKey('cookies.id'), nullable=True, comment='CookieID')
    status_code = Column(Integer, nullable=True, comment='状态码')
    response = Column(Text, nullable=True, comment='响应内容')
    error = Column(Text, nullable=True, comment='错误信息')
    start_time = Column(DateTime, nullable=False, comment='开始时间')
    end_time = Column(DateTime, nullable=True, comment='结束时间')
    duration = Column(Integer, nullable=True, comment='执行时长(毫秒)')
    create_time = Column(DateTime, default=func.now())
    update_time = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关联关系
    task = relationship('Task')
    proxy = relationship('Proxy')
    cookie = relationship('Cookie')

class Error(Base):
    """错误模型"""
    __tablename__ = 'errors'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=True, comment='任务ID')
    request_id = Column(Integer, ForeignKey('requests.id'), nullable=True, comment='请求ID')
    error_type = Column(String(50), nullable=False, comment='错误类型')
    error_message = Column(Text, nullable=False, comment='错误信息')
    stack_trace = Column(Text, nullable=True, comment='堆栈跟踪')
    context = Column(JSON, nullable=True, comment='上下文信息')
    is_resolved = Column(Boolean, default=False, nullable=False, comment='是否已解决')
    resolution = Column(Text, nullable=True, comment='解决方案')
    create_time = Column(DateTime, default=func.now())
    update_time = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关联关系
    task = relationship('Task')
    request = relationship('Request')